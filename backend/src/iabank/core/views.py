"""Utilidades comuns para views DRF do IABANK."""
from __future__ import annotations

from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response


class ApiResponseMixin:
    """Fornece helpers para padronizar payloads de respostas."""

    def _success(
        self,
        data: Any,
        *,
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Response:
        payload: Dict[str, Any] = {"data": data}
        if meta:
            payload["meta"] = meta
        return Response(payload, status=status_code)

    def _pagination_meta(self, queryset=None) -> Dict[str, Any]:
        paginator = getattr(self, "paginator", None)
        if paginator and getattr(paginator, "page", None) is not None:
            return {
                "count": paginator.page.paginator.count,
                "page": paginator.page.number,
                "page_size": paginator.get_page_size(self.request),
                "pages": paginator.page.paginator.num_pages,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
            }

        total = queryset.count() if queryset is not None else 0
        page_size = paginator.get_page_size(self.request) if paginator else total or 0
        pages = (total + page_size - 1) // page_size if page_size else 0
        return {
            "count": total,
            "page": 1 if total else 0,
            "page_size": page_size,
            "pages": pages,
            "next": None,
            "previous": None,
        }
