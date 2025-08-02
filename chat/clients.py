from zai import ZaiClient
from core.settings import Z_AI_MODEL, Z_AI_API_KEY, AI_SYSTEM_CONTENT

# Initialize client
client = ZaiClient(api_key=Z_AI_API_KEY)

async def get_ai_response(user_message):
    """Get AI response for a user message."""
    try:
        response = client.chat.completions.create(
            model=Z_AI_MODEL,
            messages=[
                {"role": "system", "content": AI_SYSTEM_CONTENT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            top_p=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Sorry, I couldn't process your request."