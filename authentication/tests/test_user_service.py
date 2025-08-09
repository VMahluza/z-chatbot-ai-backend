from django.test import TestCase
from django.contrib.auth import get_user_model
from authentication.services.user_service import register_user, RegistrationError

User = get_user_model()


class RegisterUserServiceTests(TestCase):
    def test_successful_registration(self):
        result = register_user(email="test@example.com", password="strongpassword123", first_name="Test", last_name="User")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)
        self.assertEqual(result.user.email, "test@example.com")

    def test_duplicate_email(self):
        User.objects.create_user(email="dup@example.com", password="pass1234")
        with self.assertRaises(RegistrationError):
            register_user(email="dup@example.com", password="anotherpass123")

    def test_password_too_short(self):
        with self.assertRaises(RegistrationError):
            register_user(email="short@example.com", password="123")
