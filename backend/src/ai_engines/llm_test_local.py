from langchain_ollama import ChatOllama
import asyncio
from prompts import SYSTEM_PROMPT, system_message, user_message_format


model = ChatOllama(
    model="qwen3:0.6b"
)


async def stream_conversation():
    messages = [system_message]
    userText = ''
    while True:
        userText = input('\nYou:')
        if userText == 'q':
            break
        messages.append(user_message_format(context=[], user_query=userText))
        async for chunk in model.astream(messages):
            print(chunk.content, end="", flush=True)

asyncio.run(stream_conversation())