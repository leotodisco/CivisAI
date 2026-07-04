#!/bin/bash

ollama serve &

docker run -p 6379:6379 redis:latest &

docker run -p 6333:6333 qdrant/qdrant &

python -m uvicorn backend.src.api.routes:app --reload &