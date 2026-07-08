#!/bin/bash
MODEL_PATH="/home/aarav/.lmstudio/models/lmstudio-community/Ministral-3-3B-Instruct-2512-GGUF/Ministral-3-3B-Instruct-2512-Q4_K_M.gguf"

# Added optimizations specific for llama-cpp-turboquant
echo "Starting llama-server with turbo optimizations..."
/home/aarav/llama-cpp-turboquant/build/bin/llama-server \
  -m "$MODEL_PATH" \
  --ctx-size 8192 \
  --n-gpu-layers 40 \
  --cache-type-k turbo4 \
  --cache-type-v turbo3 \
  --no-mmap \
  --host 0.0.0.0 \
  --port 8080 \
  -t 14 \
  -tb 4
