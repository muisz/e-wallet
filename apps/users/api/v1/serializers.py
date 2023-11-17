from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User as UserModel
from apps.utils import messages

User: UserModel = get_user_model()


class CreateUserSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_email(self, value):
        user = User.get_by_email(value)
        if user is not None:
            raise ValidationError(messages.USER_ALREADY_EXIST)
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name

    class Meta:
        model = User
        fields = ("id", "name", "email", "last_login")


class AuthUserSerializer(UserSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return {"access": str(token.access_token), "refresh": str(token)}

    class Meta:
        model = User
        fields = ("id", "name", "email", "last_login", "token")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
