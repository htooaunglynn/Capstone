"""DRF serializers for SkillSprint API authentication."""

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, logout
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


def user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }


def token_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = authenticate(
            request=request,
            username=attrs.get('username'),
            password=attrs.get('password'),
        )

        if user is None:
            raise serializers.ValidationError('Unable to log in with those credentials.')

        attrs['user'] = user
        return attrs


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            data = {'access': str(refresh.access_token)}

            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
                if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION'):
                    refresh.blacklist()

                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()
                data['refresh'] = str(refresh)

            attrs['tokens'] = data
        except Exception as exc:
            raise serializers.ValidationError('Refresh token is invalid or expired.') from exc

        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        refresh_token = self.validated_data.get('refresh')
        request = self.context.get('request')

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception as exc:
                raise serializers.ValidationError({
                    'refresh': ['Refresh token is invalid or already revoked.'],
                }) from exc

        if request is not None:
            logout(request)


class MeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return user_payload(instance)
