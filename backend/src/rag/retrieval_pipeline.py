from src.db.qdrant_store import QdrantStore
from qdrant_client.models import QueryResponse
from src.ai_engines.llm_ollama import LLM
from src.ai_engines.prompts import user_message_format, SYSTEM_PROMPT
from src.db.redis_history_store import RedisHistoryStore
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage


class RAGPipeline:
    def __init__(self, vector_store: QdrantStore, redis_store: RedisHistoryStore):
        self.vector_store = vector_store
        self.conversation_store = redis_store
        self.llm = LLM()

    async def run_pipeline(self, query: str, chat_id: str):
        # 1. retrieve
        response: QueryResponse = self.vector_store.search(query=query, k=20)

        # todo add reranking later

        # 2. augment
        docs = [
            p.payload.get("text", "")
            for p in response.points
            if p.payload
        ]

        conversation = self.build_conversation(
            chat_id=chat_id, docs=docs, query=query)
        async for chunk in self.llm.stream_conversation(conversation=conversation):
            yield chunk

        self.conversation_store.add_to_history(
            chat_id=chat_id, message=conversation[-1])

    def build_conversation(self, chat_id: str, docs: list, query=str) -> list[BaseMessage]:
        new_user_message = user_message_format(docs, query)
        history = self.conversation_store.get_full_history(chat_id=chat_id)
        if not history:
            # If there is no history it is the first message
            history = [
                SystemMessage(SYSTEM_PROMPT)
            ]

        history.append(new_user_message)
        self.conversation_store.add_to_history(
            chat_id=chat_id, message=new_user_message)

        return history
