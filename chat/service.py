from zai import ZaiClient
from asgiref.sync import sync_to_async
from core.settings import Z_AI_MODEL, Z_AI_API_KEY, AI_SYSTEM_CONTENT, AI_BOT_NAME
from authentication.models import User
from chat.models import Message, Conversation




# Initialize client
client = ZaiClient(api_key=Z_AI_API_KEY)




async def make_title(message:str) -> str:
    """Create a title for the conversation."""
    return "New Conversation"

async def get_ai_response(user: User, user_message: str) -> str:
    """Get AI response for a user message."""
    if not user or not user.is_authenticated:
        return "User not authenticated."
    bot = await sync_to_async(get_bot_user)()
    if not bot:
        return "Bot user not found."
    try:
        message_content = await ai_response(user_message)
 
        await save_chat_message(user, bot, user_message, message_content)
        return message_content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Sorry, I couldn't process your request."
    

async def ai_response(user_message: str) -> str:
    """Get AI response for a user message."""
    try:
        # Wrap the sync client call
        response = await sync_to_async(client.chat.completions.create)(
            model=Z_AI_MODEL,
            messages=[
                {"role": "system", "content": AI_SYSTEM_CONTENT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            top_p=0.8,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Sorry, I couldn't process your request."
    

def get_bot_user() -> User | None:
    """Get the bot user context."""
    try:
        return User.objects.get(username=AI_BOT_NAME)
    except User.DoesNotExist:
        return None

    
async def save_chat_message(user: User, bot: User, user_message: str, ai_text: str):
    """Save the chat message to the database and return (conversation, user_msg, bot_msg)."""


    # Conversation
    try:
        conversation = await sync_to_async(Conversation.objects.get)(user=user, is_active=True)
    except Conversation.DoesNotExist:
        conversation = await sync_to_async(Conversation.objects.create)(user=user)
    # User message
    user_msg : Message = await sync_to_async(Message.objects.create)(
        conversation=conversation,
        sender=user,
        content=user_message,

    )
    # Bot message
    bot_msg : Message = await sync_to_async(Message.objects.create)(
        conversation=conversation,
        sender=bot,
        content=ai_text,

    )

    print(f"Saved messages: User - {user_msg.content}, Bot - {bot_msg.content}")
    return conversation, user_msg, bot_msg