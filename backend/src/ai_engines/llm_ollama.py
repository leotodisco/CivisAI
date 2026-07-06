from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from typing import Sequence
from langchain_core.messages import BaseMessage, AIMessage
from src.core.settings import get_settings, LLM_MODE


class LLM:
    def __init__(self):
        settings = get_settings()
        if settings.llm_mode == LLM_MODE.OLLAMA:
            self.model = ChatOllama(
                base_url=settings.ollama_url,
                model="qwen3:0.6b"
            )
        else:
            self.model = ChatOpenAI(
                model=settings.llm_name,
                api_key=settings.openai_api_key
            )

    async def stream_conversation(self, conversation: Sequence[BaseMessage]):
        ai_message = ''
        async for chunk in self.model.astream(conversation):
            if chunk.content:
                ai_message += chunk.content
                yield f"data: {chunk.content}\n\n"

        conversation.append(AIMessage(ai_message))
        yield "data: [DONE]\n\n"
