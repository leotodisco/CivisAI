from langchain_ollama import ChatOllama
from src.ai_engines.prompts import user_message_format, SYSTEM_PROMPT
from typing import Sequence
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from src.core.settings import get_settings


class LLM:
    def __init__(self):
        settings = get_settings()
        self.model = ChatOllama(
            base_url=settings.ollama_url,
            model="qwen3:0.6b"
        )

    async def stream_conversation(self, conversation: Sequence[BaseMessage]):
        ai_message = ''
        async for chunk in self.model.astream(conversation):
            if chunk.content:
                ai_message += chunk.content
                yield f"data: {chunk.content}\n\n"

        conversation.append(AIMessage(ai_message))
        yield "data: [DONE]\n\n"



