import graphene
from authentication.schema.types import UserType
from authentication.services.user_service import register_user, RegistrationError


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

    @classmethod
    def mutate(cls, root, info, username, password, email, first_name=None, last_name=None):  # type: ignore[override]
        try:
            result = register_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            return RegisterUser(user=result.user, success=True, errors=[])
        except RegistrationError as e:
            return RegisterUser(user=None, success=False, errors=e.messages)

__all__ = ["RegisterUser"]
