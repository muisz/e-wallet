from django.test import TestCase
from factory import faker
from faker import Faker
from rest_framework.exceptions import NotFound
from apps.users.models import User
from apps.utils import messages
from apps.utils.decorators import assert_raise_error

fake = Faker()


class UserTestCase(TestCase):
    def test_set_email_method(self):
        email = fake.email()
        user = User()
        user.set_email(email)

        self.assertEqual(user.email, email)
    
    def test_set_name_method(self):
        first_name = fake.first_name()
        last_name = fake.last_name()
        user = User()
        user.set_name(first_name + ' ' + last_name)

        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
    
    def test_name_property(self):
        first_name = fake.first_name()
        last_name = fake.last_name()
        name = first_name + ' ' + last_name
        user = User()
        user.set_name(name)

        self.assertEqual(user.name, name)
    
    def test_create_method(self):
        name = fake.name()
        email = fake.email()
        password = fake.password()
        user = User.create(name, email, password)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, name)
        self.assertEqual(user.email, email)

    @assert_raise_error(NotFound(messages.USER_NOT_FOUND))
    def test_get_by_email_method_raise_error(self):
        User.get_by_email(fake.email(), raise_exception=True)

    def test_get_by_email_method_return_none(self):
        user = User.get_by_email(fake.email())

        self.assertIsNone(user)
    
    def test_get_by_email_method(self):
        name = fake.name()
        email = fake.email()
        password = fake.password()
        user = User.create(name, email, password)
        user_from_method = User.get_by_email(email)

        self.assertEqual(user_from_method, user)
        
    @assert_raise_error(NotFound(messages.USER_NOT_FOUND))
    def test_get_by_id_method_raise_error(self):
        User.get_by_id(0, raise_exception=True)

    def test_get_by_id_method_return_none(self):
        user = User.get_by_id(0)

        self.assertIsNone(user)
    
    def test_get_by_id_method(self):
        name = fake.name()
        email = fake.email()
        password = fake.password()
        user = User.create(name, email, password)
        user_from_method = User.get_by_id(user.id)

        self.assertEqual(user_from_method, user)

    def test_update_last_login_method(self):
        name = fake.name()
        email = fake.email()
        password = fake.password()
        user = User.create(name, email, password)
        user.update_last_login()

        self.assertIsNotNone(user.last_login)
    
    def test_authenticate_method(self):
        name = fake.name()
        email = fake.email()
        password = fake.password()
        user = User.create(name, email, password)
        user_from_method = User.authenticate(email, password)



        self.assertEqual(user_from_method, user)