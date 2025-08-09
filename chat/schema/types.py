import graphene
from graphene_django import DjangoObjectType
from chat.models import Conversation, Message


class ConversationType(DjangoObjectType):
    class Meta:
        model = Conversation
        fields = ("id", "title", "created_at")


class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        fields = ("id", "conversation", "role", "content", "model", "created_at")
