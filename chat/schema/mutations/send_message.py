import graphene
from chat.schema.types import ConversationType, MessageType
from chat.services.conversation_service import ConversationService


class SendMessage(graphene.Mutation):
    class Arguments:
        conversation_id = graphene.Int(required=False)
        content = graphene.String(required=True)
        model = graphene.String(required=False)

    ok = graphene.Boolean()
    conversation = graphene.Field(ConversationType)
    user_message = graphene.Field(MessageType)
    ai_message = graphene.Field(MessageType)

    @classmethod
    async def mutate(cls, root, info, content: str, conversation_id: int | None = None, model: str | None = None):  # type: ignore[override]
        user = info.context.user
        if not user.is_authenticated:
            return cls(ok=False, conversation=None, user_message=None, ai_message=None)
        service = ConversationService()
        result = await service.send_message(user=user, conversation_id=conversation_id, content=content, model=model or "gpt-4o-mini")
        return cls(
            ok=True,
            conversation=result.conversation,
            user_message=result.user_message,
            ai_message=result.ai_message,
        )
