from django.db import models
from authentication.models import User
import uuid

class Conversation(models.Model):
    """Model to represent a conversation between user and AI"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
    
    def __str__(self):
        return f"{self.user.username} - {self.title or f'Conversation {self.id}'}"
    
    @property
    def message_count(self):
        return self.messages.count()
    
    def get_title(self):
        """Generate title from first user message if not set"""
        if not self.title:
            first_message = self.messages.filter(sender='USER').first()
            if first_message:
                return first_message.content[:50] + "..." if len(first_message.content) > 50 else first_message.content
        return self.title or f"Conversation {self.created_at.strftime('%Y-%m-%d')}"


class Message(models.Model):
    """Model to represent individual messages in a conversation"""
    
    SENDER_CHOICES = [
        ('USER', 'User'),
        ('AI', 'AI Assistant'),
        ('SYSTEM', 'System'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('FILE', 'File'),
        ('CODE', 'Code'),
        ('ERROR', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='TEXT')
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional data
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # For AI responses
    ai_model = models.CharField(max_length=100, blank=True, null=True)  # e.g., "gpt-4", "claude-3"
    response_time = models.FloatField(null=True, blank=True)  # Response time in seconds
    token_count = models.IntegerField(null=True, blank=True)  # Token usage
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        # Update conversation's updated_at when message is saved
        super().save(*args, **kwargs)
        self.conversation.save(update_fields=['updated_at'])


class MessageReaction(models.Model):
    """Model for user reactions to messages (like, dislike, etc.)"""
    
    REACTION_CHOICES = [
        ('LIKE', '👍'),
        ('DISLIKE', '👎'),
        ('LOVE', '❤️'),
        ('HELPFUL', '✅'),
        ('NOT_HELPFUL', '❌'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']  # One reaction per user per message
        verbose_name = 'Message Reaction'
        verbose_name_plural = 'Message Reactions'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_display()} on {self.message.id}"


class ConversationShare(models.Model):
    """Model for sharing conversations publicly"""
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='share')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Conversation Share'
        verbose_name_plural = 'Conversation Shares'
    
    def __str__(self):
        return f"Share: {self.conversation.get_title()}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class ChatSettings(models.Model):
    """Model for user's chat preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_settings')

    
    # Chat behavior
    auto_save_conversations = models.BooleanField(default=True)
    show_typing_indicator = models.BooleanField(default=True)
    enable_message_reactions = models.BooleanField(default=True)
    
    # Privacy settings
    allow_data_training = models.BooleanField(default=False)
    auto_delete_after_days = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chat Settings'
        verbose_name_plural = 'Chat Settings'
    
    def __str__(self):
        return f"{self.user.username}'s Chat Settings"