
from graphene_django import DjangoObjectType
from authentication.models import User
import graphene

# Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"

# Mutations
class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, password, email, first_name=None, last_name=None):
        from .models import User
        errors = []
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        if errors:
            return RegisterUser(success=False, errors=errors)
        user = User(
            username=username,
            email=email,
            first_name=first_name or "",
            last_name=last_name or ""
        )

        

        user.set_password(password)
        user.save()
        return RegisterUser(user=user, success=True, errors=None)
