from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.users.api.v1.serializers import (
    AuthUserSerializer,
    CreateUserSerializer,
    LoginSerializer,
)
from apps.users.models import User as UserModel

User: UserModel = get_user_model()


class AuthView(GenericViewSet):
    permission_classes = ()
    serializer_class = AuthUserSerializer

    @action(methods=['post'], detail=False)
    def register(self, request):
        serializer = CreateUserSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = User.create(
            name=validated_data['name'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        user.update_last_login()

        response_serializer = self.serializer_class(user, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = User.authenticate(validated_data['email'], validated_data['password'])
        user.update_last_login()

        response_serializer = self.serializer_class(user, context=self.get_serializer_context())
        return Response(response_serializer.data)


auth_view = AuthView
