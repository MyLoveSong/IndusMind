#!/bin/bash
set -e

echo "🚀 启动RAG增强检索服务..."
echo "========================================"

# 激活conda环境
source /home/xzy/anaconda3/etc/profile.d/conda.sh
conda activate XZY

# 设置环境变量
export PYTHONPATH="/home/xzy/QWEN3-8B:$PYTHONPATH"

# 进入RAG目录
cd /home/xzy/QWEN3-8B/RAG_extracted

# 启动RAG API服务
echo "📡 启动RAG API服务 (端口: 8002)..."
cd /home/xzy/QWEN3-8B/RAG_extracted
python api_server.py \
  --model_path "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B" \
  --index_path "/home/xzy/QWEN3-8B/data/rag" \
  --metadata_path "/home/xzy/QWEN3-8B/data/rag" \
  --port 8002 \
  --host 0.0.0.0
