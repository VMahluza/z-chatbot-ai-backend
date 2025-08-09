import graphene
from chat.schema.types import ConversationType
from chat.models import Conversation


class ConversationListQuery(graphene.ObjectType):
    conversations = graphene.List(ConversationType)

    def resolve_conversations(self, info):  # type: ignore[override]
        user = info.context.user
        if not user.is_authenticated:
            return Conversation.objects.none()
        return Conversation.objects.filter(user=user).order_by('-created_at')
