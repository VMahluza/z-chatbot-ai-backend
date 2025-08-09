import graphene
import graphql_jwt

from authentication.schema.mutations.register_user import RegisterUser
from authentication.schema.queries.me import MeQuery
from authentication.schema.queries.user_by_id import UserByIdQuery
from chat.schema import ConversationListQuery, MessagesByConversationQuery, SendMessage


class Query(MeQuery, UserByIdQuery, ConversationListQuery, MessagesByConversationQuery, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    register_user = RegisterUser.Field()
    send_message = SendMessage.Field()


schema: graphene.Schema = graphene.Schema(query=Query, mutation=Mutation)