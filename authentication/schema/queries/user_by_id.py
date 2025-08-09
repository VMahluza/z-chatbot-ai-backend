import graphene
from authentication.schema.types import UserType
from authentication.models import User


class UserByIdQuery(graphene.ObjectType):
    user = graphene.Field(UserType, id=graphene.Int(required=True))

    def resolve_user(self, info, id):  # type: ignore[override]
        return User.objects.get(pk=id)
