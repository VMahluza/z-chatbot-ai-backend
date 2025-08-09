"""Data migration converting Message.sender from CharField -> ForeignKey(User).

We can't safely AlterField directly because existing rows contain string values like:
  - 'USER', 'BOT', 'SYSTEM'
  - Stringified user objects such as 'First Last (username)'

Strategy:
 1. Add a temporary nullable FK field 'sender_user'.
 2. Populate it by mapping old 'sender' values:
      - If pattern '(username)' extract username.
      - If equals 'USER' use conversation.user.
      - If equals 'BOT' or 'AI' use/create a bot user (username='bot').
      - If equals 'SYSTEM' fallback to first superuser or bot.
      - Else try to match username exactly; fallback to first superuser or bot.
 3. Remove old 'sender' CharField.
 4. Rename 'sender_user' -> 'sender'.

This preserves message ownership without breaking FK constraints.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import re


def forwards(apps, schema_editor):
    User = apps.get_model('authentication', 'User')
    Message = apps.get_model('chat', 'Message')
    Conversation = apps.get_model('chat', 'Conversation')

    # Ensure a bot user exists
    bot_user, _ = User.objects.get_or_create(
        username='bot',
        defaults={
            'password': '',
            'role': 'BOT',
            'is_active': True,
        }
    )
    system_user = User.objects.filter(is_superuser=True).first() or bot_user

    username_pattern = re.compile(r'\(([^)]+)\)$')

    for msg in Message.objects.all():
        raw = getattr(msg, 'sender', '') or ''
        raw = raw.strip()
        assign = None
        # Try pattern (username)
        m = username_pattern.search(raw)
        if m:
            uname = m.group(1).strip()
            assign = User.objects.filter(username=uname).first()
        if not assign and raw:
            # Direct username match
            assign = User.objects.filter(username=raw).first()
        if not assign:
            if raw == 'USER':
                # Use conversation owner
                try:
                    assign = msg.conversation.user
                except Exception:
                    assign = system_user
            elif raw in ('BOT', 'AI'):
                assign = bot_user
            elif raw == 'SYSTEM':
                assign = system_user
        if not assign:
            assign = system_user
        setattr(msg, 'sender_user', assign)
        msg.save(update_fields=['sender_user'])


def backwards(apps, schema_editor):
    # Reverse: degrade FK to CharField representing role/username.
    Message = apps.get_model('chat', 'Message')
    for msg in Message.objects.all():
        user = getattr(msg, 'sender', None)
        if not user:
            val = 'SYSTEM'
        elif getattr(user, 'username', '') == 'bot':
            val = 'BOT'
        else:
            val = user.username
        setattr(msg, 'sender_old', val)
        msg.save(update_fields=['sender_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_remove_message_ai_model_remove_message_response_time_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add temporary field
        migrations.AddField(
            model_name='message',
            name='sender_user',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        # 2. Populate
        migrations.RunPython(forwards, backwards),
        # 3. Remove old CharField
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
        # 4. Rename sender_user -> sender (final FK)
        migrations.RenameField(
            model_name='message',
            old_name='sender_user',
            new_name='sender',
        ),
        # 5. Adjust final FK attributes (related_name)
        migrations.AlterField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to=settings.AUTH_USER_MODEL),
        ),
    ]
