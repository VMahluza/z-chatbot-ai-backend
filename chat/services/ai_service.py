from asgiref.sync import sync_to_async
from dataclasses import dataclass
from typing import List

# Placeholder for actual AI client (e.g., OpenAI, custom, etc.)
class AIClient:
    async def complete(self, messages: List[dict]) -> str:
        # In a real implementation, call external async API or wrap sync client.
        return "AI response placeholder"


@dataclass
class AIMessage:
    role: str
    content: str


class AIService:
    def __init__(self, client: AIClient | None = None):
        self.client = client or AIClient()

    async def create_completion(self, messages: List[AIMessage]) -> str:
        payload = [ {"role": m.role, "content": m.content} for m in messages ]
        # Assuming underlying client is async; if sync wrap with sync_to_async
        return await self.client.complete(payload)
