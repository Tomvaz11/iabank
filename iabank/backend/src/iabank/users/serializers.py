"""
Serializers do app Users.

Define os serializers para autenticação, perfis de usuário
e operações relacionadas à gestão de usuários.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from iabank.core.models import User, Tenant


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil do usuário.
    
    Exibe informações do usuário logado, incluindo
    dados do tenant associado.
    """
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'is_tenant_admin',
            'tenant_name',
            'date_joined'
        ]
        read_only_fields = ['id', 'username', 'tenant_name', 'date_joined']


class LoginSerializer(serializers.Serializer):
    """
    Serializer para autenticação de usuários.
    
    Valida credenciais e retorna informações
    do usuário autenticado.
    """
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Valida as credenciais do usuário."""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Credenciais inválidas.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'Conta de usuário desabilitada.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Username e password são obrigatórios.'
            )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para alteração de senha.
    
    Valida senha atual e define nova senha
    para o usuário autenticado.
    """
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        """Valida se a senha atual está correta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value
    
    def validate(self, attrs):
        """Valida se as novas senhas coincidem."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('As senhas não coincidem.')
        return attrs
    
    def save(self):
        """Salva a nova senha do usuário."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novos usuários.
    
    Permite que administradores do tenant criem
    novos usuários associados ao mesmo tenant.
    """
    
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'password',
            'confirm_password'
        ]
    
    def validate(self, attrs):
        """Valida se as senhas coincidem."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('As senhas não coincidem.')
        return attrs
    
    def create(self, validated_data):
        """Cria o usuário associado ao tenant atual."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Obtém o tenant do usuário que está criando
        request = self.context.get('request')
        tenant = request.tenant if hasattr(request, 'tenant') else None
        
        user = User.objects.create_user(
            tenant=tenant,
            password=password,
            **validated_data
        )
        return user