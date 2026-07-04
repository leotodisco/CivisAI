import redis
from src.core.settings import get_settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
import json
from typing import List
import logging

logger = logging.getLogger(__name__)


class RedisHistoryStore:

    def __init__(self):
        settings = get_settings()
        try:
            self.redis_store = redis.Redis(
                host=settings.redis_db_url,
                port=int(settings.redis_db_port or 6379),
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Error connecting to redis instance. {str(e)}")

    def add_to_history(self, chat_id: str, message: AIMessage | HumanMessage | SystemMessage) -> None:
        if isinstance(message, AIMessage):
            role = 'assistant'
        elif isinstance(message, HumanMessage):
            role = 'user'
        elif isinstance(message, SystemMessage):
            role = 'system'
        else:
            logger.error(f"The message type is not supported: {type(message)}")
            return None

        try:
            message_str = json.dumps({'role': role, 'content': message.content})
            self.redis_store.rpush(chat_id, message_str)
            self.redis_store.expire(chat_id, 60 * 60 * 24)  # 24 Hours
        except Exception as e:
            logger.error(f"Error pushing element to redis: {str(e)}")

    def get_full_history(self, chat_id: str) -> List[BaseMessage]:
        try:
            history_raw = self.redis_store.lrange(chat_id, 0, -1)
            history: List[BaseMessage] = []

            for msg in history_raw:
                data = json.loads(msg)

                if data["role"] == "user":
                    history.append(HumanMessage(content=data["content"]))
                elif data["role"] == "assistant":
                    history.append(AIMessage(content=data["content"]))
                elif data["role"] == "system":
                    history.append(SystemMessage(content=data["content"]))

            return history
        except Exception as e:
            logger.error(f"Error reading from redis instance: {str(e)}")
            return []