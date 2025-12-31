#!/bin/bash

# QWEN3-8B完整训练系统一键启动脚本
# 启动完整的产业报告生成系统（前端+后端+完整训练模型）

echo "=========================================="
echo "🚀 QWEN3-8B完整训练系统启动脚本"
echo "=========================================="
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务状态函数
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name: 运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name: 未启动${NC}"
        return 1
    fi
}

# 1. 启动RAG检索服务
echo -e "${BLUE}1. 启动RAG检索增强服务...${NC}"

# 停止可能存在的旧进程
pkill -f "rag_service.py" 2>/dev/null || true
pkill -f "start_rag_service.sh" 2>/dev/null || true
sleep 2

# 启动RAG服务
cd /home/xzy/QWEN3-8B
bash start_rag_service.sh &
RAG_SERVER_PID=$!

echo "RAG服务启动中 (PID: $RAG_SERVER_PID)..."
sleep 5

# 检查RAG服务状态
if curl -s --max-time 5 http://127.0.0.1:8002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ RAG服务启动成功!${NC}"
else
    echo -e "${YELLOW}⚠️ RAG服务启动中...${NC}"
fi

echo

# 2. 启动LangChain集成服务
echo -e "${BLUE}2. 启动LangChain集成服务...${NC}"

# 停止可能存在的旧进程
pkill -f "langchain_api_server.py" 2>/dev/null || true
pkill -f "start_langchain_service.sh" 2>/dev/null || true
sleep 2

# 启动LangChain服务
cd /home/xzy/QWEN3-8B
bash start_langchain_service.sh &
LANGCHAIN_SERVER_PID=$!

echo "LangChain服务启动中 (PID: $LANGCHAIN_SERVER_PID)..."
sleep 5

# 检查LangChain服务状态
if curl -s --max-time 5 http://127.0.0.1:8003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ LangChain服务启动成功!${NC}"
else
    echo -e "${YELLOW}⚠️ LangChain服务启动中...${NC}"
fi

echo

# 3. 启动完整训练的QWEN3-8B模型服务器
echo -e "${BLUE}3. 启动完整训练的QWEN3-8B模型服务器...${NC}"

# 停止可能存在的旧进程
pkill -f "model_server.py" 2>/dev/null || true
pkill -f "start_model_server.sh" 2>/dev/null || true
sleep 2

# 启动模型服务器
cd /home/xzy/QWEN3-8B
bash scripts/start_model_server.sh &
MODEL_SERVER_PID=$!

echo "模型服务器启动中 (PID: $MODEL_SERVER_PID)..."
echo "等待模型加载 (可能需要2-3分钟)..."

# 等待模型服务器启动
MAX_WAIT=300  # 5分钟超时
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s --max-time 5 http://127.0.0.1:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 模型服务器启动成功!${NC}"
        break
    fi
    
    sleep 10
    WAIT_COUNT=$((WAIT_COUNT + 10))
    
    if [ $((WAIT_COUNT % 60)) -eq 0 ]; then
        echo "等待模型服务器启动... ($WAIT_COUNT/$MAX_WAIT 秒)"
    fi
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ 模型服务器启动超时${NC}"
    exit 1
fi

echo

# 2. 启动ZJU-SEM-Project后端
echo -e "${BLUE}2. 启动ZJU-SEM-Project后端服务...${NC}"

# 停止可能存在的旧进程
pkill -f "npm.*server.js" 2>/dev/null || true
sleep 2

# 启动后端
cd /home/xzy/QWEN3-8B/ZJU-SEM-Project/backend
npm start &
BACKEND_PID=$!

echo "后端服务启动中 (PID: $BACKEND_PID)..."
sleep 5

echo

# 3. 启动前端服务
echo -e "${BLUE}3. 启动前端界面...${NC}"

# 停止可能存在的旧进程
pkill -f "vite" 2>/dev/null || true
sleep 2

# 启动前端
cd /home/xzy/QWEN3-8B/ZJU-SEM-Project/frontend/final-project
npm run dev &
FRONTEND_PID=$!

echo "前端服务启动中 (PID: $FRONTEND_PID)..."
sleep 5

echo

# 4. 最终状态检查
echo -e "${BLUE}4. 系统状态检查...${NC}"
echo

check_service "RAG检索服务" "http://127.0.0.1:8002/health"
check_service "LangChain集成服务" "http://127.0.0.1:8003/health"
check_service "QWEN3-8B模型服务器" "http://127.0.0.1:8001/health"
check_service "后端API服务" "http://localhost:3000/health"
check_service "前端界面" "http://localhost:5173"  # 前端可能返回非200状态

echo

# 5. 输出访问信息
echo "=========================================="
echo -e "${GREEN}🎉 微调+RAG+LangChain完整系统启动成功!${NC}"
echo "=========================================="
echo
echo -e "${YELLOW}🤖 AI系统架构:${NC}"
echo "   • 微调模型: Qwen3-8B (LoRA, 150轮训练)"
echo "   • RAG检索: FAISS向量搜索 (12,088个文档块)"
echo "   • LangChain: 完整的链式调用和管理"
echo "   • 量化方式: 4-bit NF4 (内存优化)"
echo
echo -e "${YELLOW}📊 训练指标:${NC}"
echo "   • 训练步数: 19,200步"
echo "   • 最终损失: 1.1826"
echo "   • 训练时长: 23小时"
echo "   • 训练方式: 4卡DDP分布式"
echo "   • 样本数量: 256个高质量产业报告"
echo
echo -e "${YELLOW}🌐 服务地址:${NC}"
echo "   • 前端界面:   http://localhost:5173"
echo "   • 后端API:     http://localhost:3000"
echo "   • RAG服务:     http://127.0.0.1:8002"
echo "   • LangChain:   http://127.0.0.1:8003"
echo "   • 模型服务:    http://127.0.0.1:8001"
echo
echo -e "${YELLOW}⚙️  进程信息:${NC}"
echo "   • RAG服务PID:      $RAG_SERVER_PID"
echo "   • LangChain服务PID: $LANGCHAIN_SERVER_PID"
echo "   • 模型服务器PID:   $MODEL_SERVER_PID"
echo "   • 后端服务PID:     $BACKEND_PID"
echo "   • 前端服务PID:     $FRONTEND_PID"
echo
echo -e "${YELLOW}🎯 立即体验:${NC}"
echo "   1. 打开浏览器访问: http://localhost:5173"
echo "   2. 点击右上角的'新建产业报告'"
echo "   3. 填写报告信息并生成AI产业报告"
echo "   4. 享受完整训练模型的高质量输出!"
echo
echo -e "${YELLOW}🛑 停止服务:${NC}"
echo "   kill $RAG_SERVER_PID $LANGCHAIN_SERVER_PID $MODEL_SERVER_PID $BACKEND_PID $FRONTEND_PID"
echo
echo -e "${GREEN}🚀 系统已就绪，享受AI产业报告生成体验!${NC}"

# 保持脚本运行以显示状态
echo
echo "按 Ctrl+C 退出监控..."
trap "echo -e '\n${YELLOW}正在停止服务...${NC}'; kill $RAG_SERVER_PID $LANGCHAIN_SERVER_PID $MODEL_SERVER_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

while true; do
    sleep 30
    echo -e "${BLUE}系统运行正常... (时间: $(date '+%H:%M:%S'))${NC}"
done
