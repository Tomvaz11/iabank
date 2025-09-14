"""
Multi-tenancy middleware for IABANK.
Provides automatic tenant context and query filtering.
"""

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import Tenant

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that provides tenant context for multi-tenant applications.

    Tenant identification priority:
    1. X-Tenant-ID header
    2. JWT token tenant claim
    3. Subdomain extraction
    4. DEFAULT_TENANT_ID from settings (development only)
    """

    def process_request(self, request):
        """Process incoming request to identify and set tenant context."""
        tenant_id = self._extract_tenant_id(request)

        if not tenant_id:
            return self._tenant_required_response()

        try:
            tenant = self._get_tenant(tenant_id)
            if not tenant.is_active:
                return self._tenant_inactive_response()

            # Set tenant context
            request.tenant = tenant
            request.tenant_id = tenant.id

            # Set thread-local tenant for model queries
            self._set_tenant_context(tenant)

        except Tenant.DoesNotExist:
            logger.warning(f"Tenant not found: {tenant_id}")
            return self._tenant_not_found_response()
        except Exception as e:
            logger.error(f"Error processing tenant {tenant_id}: {e}")
            return self._server_error_response()

    def process_response(self, request, response):
        """Clean up tenant context after request processing."""
        self._clear_tenant_context()
        return response

    def _extract_tenant_id(self, request) -> str | None:
        """Extract tenant ID from various sources."""
        # 1. Check X-Tenant-ID header
        tenant_id = request.META.get("HTTP_X_TENANT_ID")
        if tenant_id:
            logger.debug(f"Tenant ID from header: {tenant_id}")
            return tenant_id

        # 2. Extract from JWT token if available
        tenant_id = self._extract_from_jwt(request)
        if tenant_id:
            logger.debug(f"Tenant ID from JWT: {tenant_id}")
            return tenant_id

        # 3. Extract from subdomain
        tenant_id = self._extract_from_subdomain(request)
        if tenant_id:
            logger.debug(f"Tenant ID from subdomain: {tenant_id}")
            return tenant_id

        # 4. Development fallback
        if settings.DEBUG and hasattr(settings, "DEFAULT_TENANT_ID"):
            logger.debug(f"Using default tenant ID: {settings.DEFAULT_TENANT_ID}")
            return settings.DEFAULT_TENANT_ID

        return None

    def _extract_from_jwt(self, request) -> str | None:
        """Extract tenant ID from JWT token claims."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        try:
            from jwt import decode
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from rest_framework_simplejwt.tokens import UntypedToken

            token = auth_header.split(" ")[1]
            UntypedToken(token)  # Validate token

            decoded = decode(token, options={"verify_signature": False})
            return decoded.get("tenant_id")
        except (InvalidToken, TokenError, Exception):
            return None

    def _extract_from_subdomain(self, request) -> str | None:
        """Extract tenant from subdomain (e.g., company.iabank.com)."""
        host = request.get_host().lower()
        if not host or "." not in host:
            return None

        subdomain = host.split(".")[0]
        if subdomain in ["www", "api", "admin"]:
            return None

        try:
            # Look up tenant by slug
            tenant = Tenant.objects.get(slug=subdomain)
            return str(tenant.id)
        except Tenant.DoesNotExist:
            return None

    def _get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID with caching."""
        # Add caching later if needed
        return Tenant.objects.get(id=tenant_id)

    def _set_tenant_context(self, tenant: Tenant):
        """Set thread-local tenant context and PostgreSQL RLS context."""
        import threading

        from django.db import connections

        # Set thread-local context using proper thread-local storage
        current_thread = threading.current_thread()
        current_thread.tenant = tenant

        # Set PostgreSQL RLS context on default connection
        try:
            conn = connections["default"]
            with conn.cursor() as cursor:
                cursor.execute("SELECT set_tenant_context(%s)", [str(tenant.id)])
                logger.debug(f"PostgreSQL RLS context set for tenant: {tenant.id}")
        except Exception as e:
            logger.warning(f"Failed to set PostgreSQL RLS context: {e}")
            # RLS is additional security layer, app-level filtering still works

    def _clear_tenant_context(self):
        """Clear thread-local tenant context."""
        import threading

        current_thread = threading.current_thread()
        if hasattr(current_thread, "tenant"):
            delattr(current_thread, "tenant")

    @classmethod
    def get_current_tenant(cls) -> Tenant | None:
        """Get current tenant from thread-local context."""
        import threading

        current_thread = threading.current_thread()
        return getattr(current_thread, "tenant", None)

    def _tenant_required_response(self):
        """Return error response when tenant is required but not provided."""
        return JsonResponse(
            {
                "errors": [
                    {
                        "status": "400",
                        "code": "TENANT_REQUIRED",
                        "detail": "Tenant identification is required. Please provide X-Tenant-ID header or valid JWT token.",
                    }
                ]
            },
            status=400,
        )

    def _tenant_not_found_response(self):
        """Return error response when tenant is not found."""
        return JsonResponse(
            {
                "errors": [
                    {
                        "status": "404",
                        "code": "TENANT_NOT_FOUND",
                        "detail": "The specified tenant was not found.",
                    }
                ]
            },
            status=404,
        )

    def _tenant_inactive_response(self):
        """Return error response when tenant is inactive."""
        return JsonResponse(
            {
                "errors": [
                    {
                        "status": "403",
                        "code": "TENANT_INACTIVE",
                        "detail": "This tenant account is currently inactive. Please contact support.",
                    }
                ]
            },
            status=403,
        )

    def _server_error_response(self):
        """Return generic server error response."""
        return JsonResponse(
            {
                "errors": [
                    {
                        "status": "500",
                        "code": "INTERNAL_ERROR",
                        "detail": "An internal error occurred while processing your request.",
                    }
                ]
            },
            status=500,
        )


class TenantQuerySetMixin:
    """
    Mixin for QuerySets to automatically filter by current tenant.
    """

    def get_queryset(self):
        """Filter queryset by current tenant."""
        queryset = super().get_queryset()
        current_tenant = TenantMiddleware.get_current_tenant()

        if current_tenant and hasattr(queryset.model, "tenant"):
            return queryset.filter(tenant=current_tenant)

        return queryset


class TenantModelMixin(models.Model):
    """
    Mixin for models to automatically set tenant on save.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Automatically set tenant if not already set."""
        if hasattr(self, "tenant") and not self.tenant_id:
            current_tenant = TenantMiddleware.get_current_tenant()
            if current_tenant:
                self.tenant = current_tenant
            else:
                raise ValidationError("No tenant context available")

        super().save(*args, **kwargs)
