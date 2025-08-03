# Queries
import graphene
import graphql_jwt

from authentication.models import User
from authentication.schema import RegisterUser, UserType


# QUERIES 
class Query(graphene.ObjectType):
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    me = graphene.Field(UserType)

    def resolve_user(self, info, id):
        return User.objects.get(pk=id)
    
    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
class Mutation(graphene.ObjectType):
    token_auth: graphene.Field = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token: graphene.Field = graphql_jwt.Verify.Field()
    register_user: graphene.Field = RegisterUser.Field()

schema: graphene.Schema = graphene.Schema(query=Query, mutation=Mutation)