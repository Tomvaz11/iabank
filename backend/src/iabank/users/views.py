"""
Views do app Users.

Implementa endpoints para autenticação, gestão de perfil
e operações relacionadas aos usuários do sistema.
"""

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from iabank.core.models import User
from .serializers import (
    UserProfileSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    UserCreateSerializer
)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet para operações de autenticação.
    
    Fornece endpoints para login, logout e gestão
    de sessão de usuários.
    """
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Endpoint para autenticação de usuários."""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Retorna dados do usuário autenticado
            user_serializer = UserProfileSerializer(user)
            return Response({
                'user': user_serializer.data,
                'message': 'Login realizado com sucesso.'
            })
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Endpoint para logout de usuários."""
        logout(request)
        return Response({
            'message': 'Logout realizado com sucesso.'
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint para obter dados do usuário autenticado."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserProfileView(APIView):
    """
    View para gestão do perfil do usuário.
    
    Permite visualização e edição dos dados
    pessoais do usuário autenticado.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna dados do perfil do usuário."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """Atualiza dados do perfil do usuário."""
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    """
    View para alteração de senha do usuário.
    
    Permite que usuários autenticados alterem
    suas próprias senhas.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Altera a senha do usuário autenticado."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Senha alterada com sucesso.'
            })
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestão de usuários (apenas administradores).
    
    Permite que administradores do tenant gerenciem
    usuários associados ao mesmo tenant.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra usuários pelo tenant atual."""
        if not self.request.user.is_tenant_admin:
            # Usuários comuns só veem a si mesmos
            return User.objects.filter(id=self.request.user.id)
        
        # Administradores veem todos os usuários do tenant
        return User.objects.filter(tenant=self.request.tenant)
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action."""
        if self.action == 'create':
            return UserCreateSerializer
        else:
            return UserProfileSerializer
    
    def create(self, request, *args, **kwargs):
        """Cria novos usuários (apenas administradores)."""
        if not request.user.is_tenant_admin:
            return Response(
                {'detail': 'Apenas administradores podem criar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Desativa usuários ao invés de excluir."""
        if not request.user.is_tenant_admin:
            return Response(
                {'detail': 'Apenas administradores podem desativar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        if user == request.user:
            return Response(
                {'detail': 'Não é possível desativar sua própria conta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.save()
        
        return Response({
            'message': 'Usuário desativado com sucesso.'
        })