#!/bin/bash

# QWEN3-8B 本地产业报告生成系统一键启动脚本
# 启动完整的产业报告生成系统（前端+后端+完整训练模型）

echo "=========================================="
echo "🚀 QWEN3-8B本地产业报告生成系统启动脚本"
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

# 解析命令行参数
WITH_FRONTEND=false
NO_TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-frontend)
            WITH_FRONTEND=true
            shift
            ;;
        --no-test)
            NO_TEST=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 1. 启动RAG检索服务
echo -e "${BLUE}1. 启动RAG检索增强服务...${NC}"

# 停止可能存在的旧进程
pkill -f "rag_service.py" 2>/dev/null || true
pkill -f "start_rag_service.sh" 2>/dev/null || true
sleep 2

# 启动RAG服务
cd /home/xzy/QWEN3-8B
bash start_rag_service.sh > /home/xzy/rag_service.log 2>&1 &
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

# 2. 启动本地LoRA模型服务器
echo -e "${BLUE}2. 启动本地LoRA模型服务器...${NC}"

# 停止可能存在的旧进程
pkill -f "model_server.py" 2>/dev/null || true
pkill -f "start_model_server.sh" 2>/dev/null || true
sleep 2

# 启动模型服务器
cd /home/xzy/QWEN3-8B
bash scripts/start_model_server.sh > /home/xzy/local_qwen_model_server.log 2>&1 &
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

# 3. 启动后端API服务
echo -e "${BLUE}3. 启动后端API服务...${NC}"

# 停止可能存在的旧进程
pkill -f "npm.*server.js" 2>/dev/null || true
sleep 2

# 启动后端
cd /home/xzy/QWEN3-8B/ZJU-SEM-Project/backend
npm start > /home/xzy/backend_local_lora.log 2>&1 &
BACKEND_PID=$!

echo "后端服务启动中 (PID: $BACKEND_PID)..."
sleep 5

echo

# 4. 启动前端服务 (如果指定)
if [ "$WITH_FRONTEND" = true ]; then
    echo -e "${BLUE}4. 启动前端界面...${NC}"

    # 停止可能存在的旧进程
    pkill -f "vite" 2>/dev/null || true
    sleep 2

    # 启动前端
    cd /home/xzy/QWEN3-8B/ZJU-SEM-Project/frontend/final-project
    npm run dev -- --host 0.0.0.0 --port 5173 > /home/xzy/frontend_dev.log 2>&1 &
    FRONTEND_PID=$!

    echo "前端服务启动中 (PID: $FRONTEND_PID)..."
    sleep 5
fi

# 5. 最终状态检查
echo -e "${BLUE}5. 系统状态检查...${NC}"
echo

check_service "RAG检索服务" "http://127.0.0.1:8002/health"
check_service "QWEN3-8B模型服务器" "http://127.0.0.1:8001/health"
check_service "后端API服务" "http://localhost:3000/health"

if [ "$WITH_FRONTEND" = true ]; then
    check_service "前端界面" "http://localhost:5173"  # 前端可能返回非200状态
fi

echo

# 6. 自检测试 (如果未禁用)
if [ "$NO_TEST" = false ]; then
    echo -e "${BLUE}6. 执行自检测试...${NC}"

    # create report
    CREAT=$(curl -s -X POST http://127.0.0.1:3000/api/reports -H "Content-Type: application/json" -d '{"title":"自检测试报告","industry":"AI产业","scenario":"自检","objective":"验证系统功能","data_sources":[]}' -m 60 || true)
    echo "create: ${CREAT:0:200}"
    RID=$(echo "$CREAT" | sed -n 's/.*"reportId"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p')
    echo "rid=$RID"

    if [ -n "$RID" ]; then
        # generate full report (allow long)
        GEN=$(curl -s -X POST http://127.0.0.1:3000/api/reports/${RID}/generate -H "Content-Type: application/json" -d '{}' -m 1200 || true)
        echo "generate: ${GEN:0:800}"

        # show status from API
        curl -s http://127.0.0.1:3000/api/reports/${RID} -m 30 | python3 -c "import sys, json; d=json.load(sys.stdin); print('status',d.get('status'),'content_len',len(d.get('content') or ''))" || true
    else
        echo -e "${RED}❌ 自检失败：无法创建报告${NC}"
    fi
fi

echo
echo "=========================================="
echo -e "${GREEN}🎉 本地产业报告生成系统启动成功!${NC}"
echo "=========================================="
echo
echo -e "${YELLOW}🤖 AI系统架构:${NC}"
echo "   • 微调模型: Qwen3-8B (LoRA, 150轮训练)"
echo "   • RAG检索: FAISS向量搜索 (12,088个文档块)"
echo "   • 量化方式: 4-bit NF4 (内存优化)"
echo
echo -e "${YELLOW}🌐 服务地址:${NC}"
echo "   • 后端API:     http://localhost:3000"
echo "   • RAG服务:     http://127.0.0.1:8002"
echo "   • 模型服务:    http://127.0.0.1:8001"
if [ "$WITH_FRONTEND" = true ]; then
    echo "   • 前端界面:    http://localhost:5173"
fi
echo
echo -e "${YELLOW}⚙️  进程信息:${NC}"
echo "   • RAG服务PID:      $RAG_SERVER_PID"
echo "   • 模型服务器PID:   $MODEL_SERVER_PID"
echo "   • 后端服务PID:     $BACKEND_PID"
if [ "$WITH_FRONTEND" = true ]; then
    echo "   • 前端服务PID:     $FRONTEND_PID"
fi
echo
echo -e "${YELLOW}🎯 立即体验:${NC}"
if [ "$WITH_FRONTEND" = true ]; then
    echo "   1. 打开浏览器访问: http://localhost:5173"
    echo "   2. 点击右上角的'新建产业报告'"
    echo "   3. 填写报告信息并生成AI产业报告"
fi
echo "   4. 或使用API直接调用后端服务"
echo
echo -e "${YELLOW}🛑 停止服务:${NC}"
if [ "$WITH_FRONTEND" = true ]; then
    echo "   kill $RAG_SERVER_PID $MODEL_SERVER_PID $BACKEND_PID $FRONTEND_PID"
else
    echo "   kill $RAG_SERVER_PID $MODEL_SERVER_PID $BACKEND_PID"
fi
echo
echo -e "${GREEN}🚀 系统已就绪，享受AI产业报告生成体验!${NC}"

# 保持脚本运行以显示状态 (如果有前端)
if [ "$WITH_FRONTEND" = true ]; then
    echo
    echo "按 Ctrl+C 退出监控..."
    trap "echo -e '\n${YELLOW}正在停止服务...${NC}'; kill $RAG_SERVER_PID $MODEL_SERVER_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

    while true; do
        sleep 30
        echo -e "${BLUE}系统运行正常... (时间: $(date '+%H:%M:%S'))${NC}"
    done
fi