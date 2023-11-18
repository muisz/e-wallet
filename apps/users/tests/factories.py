from django.contrib.auth import get_user_model
from faker import Faker

from apps.users.models import User as UserModel

fake = Faker()
User: UserModel = get_user_model()


def create_user():
    return User.create(fake.name(), fake.email(), fake.password())
