from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'password')

    def set_email(self, value: str):
        self.email = value.lower()
    
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
        user = cls()
        user.set_name(name)
        user.set_email(email)
        user.set_password(password)
        user.save()
        return user
