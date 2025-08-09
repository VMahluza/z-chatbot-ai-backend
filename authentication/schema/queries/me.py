import graphene
from authentication.schema.types import UserType


class MeQuery(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info):  # type: ignore[override]
        user = info.context.user
        return user if user.is_authenticated else None
