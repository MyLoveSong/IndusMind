#!/bin/bash
set -e

echo "🔗 启动LangChain RAG集成服务..."
echo "========================================"

# 激活conda环境
source /home/xzy/anaconda3/etc/profile.d/conda.sh
conda activate XZY

# 设置环境变量
export PYTHONPATH="/home/xzy/QWEN3-8B:$PYTHONPATH"

# 启动LangChain API服务
echo "🌐 启动LangChain API服务 (端口: 8003)..."
python langchain_api_server.py
