import graphene
from chat.schema.types import MessageType
from chat.models import Message, Conversation


class MessagesByConversationQuery(graphene.ObjectType):
    messages = graphene.List(MessageType, conversation_id=graphene.Int(required=True))

    def resolve_messages(self, info, conversation_id):  # type: ignore[override]
        user = info.context.user
        if not user.is_authenticated:
            return []
        # Ensure conversation belongs to user
        try:
            Conversation.objects.get(pk=conversation_id, user=user)
        except Conversation.DoesNotExist:
            return []
        return Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
