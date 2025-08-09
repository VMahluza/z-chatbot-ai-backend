from graphene_django import DjangoObjectType
from authentication.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "date_joined")
