"""User domain service functions.

Business logic lives here, separated from GraphQL mutation classes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from django.db import transaction
from authentication.models import User


class RegistrationError(Exception):
    """Raised when user registration fails validation."""
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__("; ".join(messages))


@dataclass(slots=True)
class RegistrationResult:
    user: User


@transaction.atomic
def register_user(*, username: str, password: str, email: str, first_name: str | None = None, last_name: str | None = None) -> RegistrationResult:
    errors: List[str] = []
    if User.objects.filter(username=username).exists():
        errors.append("Username already exists.")
    if User.objects.filter(email=email).exists():
        errors.append("Email already exists.")
    if errors:
        raise RegistrationError(errors)

    user = User(
        username=username,
        email=email,
        first_name=first_name or "",
        last_name=last_name or "",
    )
    user.set_password(password)
    user.save()
    return RegistrationResult(user=user)
