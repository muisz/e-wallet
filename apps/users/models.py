from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.utils import messages

class User(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'password')

    def set_email(self, value: str):
        self.email = value.lower()
        self.username = self.email
    
    def set_name(self, value: str):
        names = value.split(' ')
        first_name = names[0]
        last_name = ''
        if len(names) > 1:
            last_name = ' '.join(name for name in names[1:])
        self.first_name = first_name
        self.last_name = last_name
    
    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @classmethod
    def create(cls, name: str, email: str, password: str):
        user = cls(is_active=True)
        user.set_name(name)
        user.set_email(email)
        user.set_password(password)
        user.save()
        return user

    @classmethod
    def get_by_email(cls, value: str, raise_exception: bool = False):
        user = cls.objects.filter(email=value).first()
        if not user and raise_exception:
            raise NotFound(messages.USER_NOT_FOUND)
        return user
    
    @classmethod
    def get_by_id(cls, value: id, raise_exception: bool = False):
        user = cls.objects.filter(id=value).first()
        if not user and raise_exception:
            raise NotFound(messages.USER_NOT_FOUND)
        return user

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    @classmethod
    def authenticate(cls, email: str, password: str):
        user = cls.get_by_email(email)
        if user is None or not user.check_password(password):
            raise NotFound(messages.USER_AUTHENTICATION_FAILED)
        return user
