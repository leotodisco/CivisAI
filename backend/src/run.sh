#!/bin/bash

ollama serve &

docker run -p 6379:6379 redis:latest &

docker run -p 6333:6333 qdrant/qdrant &

pwd
cwd

python -m uvicorn src.api.routes:app --reload &