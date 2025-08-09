from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction

from chat.models import Conversation, Message
from .ai_service import AIService, AIMessage
from authentication.models import User



@dataclass
class SendMessageResult:
    conversation: Conversation
    user_message: Message
    ai_message: Message | None


class ConversationService:
    def __init__(self, ai_service: AIService | None = None):
        self.ai_service = ai_service or AIService()

    async def list_conversations(self, user: User) -> list["Conversation"]:
        return await sync_to_async(list)(Conversation.objects.filter(user=user).order_by('-created_at'))

    async def list_messages(self, conversation_id: int, user: User) -> list["Message"]:
        qs = Message.objects.filter(conversation_id=conversation_id, conversation__user=user).order_by('created_at')
        return await sync_to_async(list)(qs)

    async def send_message(self, user: User, conversation_id: int | None, content: str, model: str = "gpt-4o-mini") -> "SendMessageResult":
        if conversation_id:
            conversation = await sync_to_async(Conversation.objects.get)(pk=conversation_id, user=user)
        else:
            conversation = await sync_to_async(Conversation.objects.create)(user=user, title=content[:60] or "New Conversation")

        @transaction.atomic
        def _persist_user_message() -> Message:
            return Message.objects.create(conversation=conversation, role="user", content=content, model=model)

        user_msg = await sync_to_async(_persist_user_message)()

        # Build context for AI
        prior_messages = await self.list_messages(conversation.id, user)
        ai_input = [AIMessage(role=m.role, content=m.content) for m in prior_messages[-10:]] + [AIMessage(role="user", content=content)]
        ai_text = await self.ai_service.create_completion(ai_input)

        @transaction.atomic
        def _persist_ai_message() -> Message:
            return Message.objects.create(conversation=conversation, role="assistant", content=ai_text, model=model)

        ai_msg = await sync_to_async(_persist_ai_message)()

        return SendMessageResult(conversation=conversation, user_message=user_msg, ai_message=ai_msg)
