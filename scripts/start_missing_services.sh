#!/bin/bash

# Start Only Missing Services for Local QWEN3-8B Integration
# This script checks which services are missing and starts only those

echo "🔍 检查服务状态并启动缺失的服务..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if service is running
check_and_start_service() {
    local port=$1
    local service_name=$2
    local start_command=$3
    local health_url=$4

    echo -n "检查 $service_name... "

    if curl -s "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 已在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⏳ 未运行，正在启动...${NC}"

        # Execute start command
        eval "$start_command"

        # Wait for service to start
        local attempts=0
        local max_attempts=30

        while [ $attempts -lt $max_attempts ]; do
            if curl -s "$health_url" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $service_name 启动成功${NC}"
                return 0
            fi
            sleep 2
            ((attempts++))
        done

        echo -e "${RED}❌ $service_name 启动失败${NC}"
        return 1
    fi
}

# Check and start Model Server
MODEL_START_CMD="
if [ ! -d 'venv' ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python model_server.py &
echo \$! > /tmp/model_server.pid
"

check_and_start_service 8001 "模型服务器" "$MODEL_START_CMD" "http://127.0.0.1:8001/health"

# Check and start Frontend (only check basic connectivity)
echo -n "检查 前端... "
if curl -s "http://localhost:5173" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 已在运行${NC}"
else
    echo -e "${YELLOW}⏳ 未运行，正在启动...${NC}"

    cd ZJU-SEM-Project-master/frontend/final-project
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev &
    echo $! > /tmp/frontend.pid
    cd ../../..

    # Wait a bit for frontend
    sleep 5
    if curl -s "http://localhost:5173" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端启动成功${NC}"
    else
        echo -e "${RED}❌ 前端启动失败${NC}"
    fi
fi

echo ""
echo "📊 当前服务状态:"

# Final status check
echo -n "  🤖 模型服务器: "
if curl -s "http://127.0.0.1:8001/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 运行中${NC} (http://127.0.0.1:8001/health)"
else
    echo -e "${RED}❌ 未运行${NC}"
fi

echo -n "  🔧 后端API:    "
if curl -s "http://localhost:3000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 运行中${NC} (http://localhost:3000/health)"
else
    echo -e "${RED}❌ 未运行${NC}"
fi

echo -n "  🎨 前端:       "
if curl -s "http://localhost:5173" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 运行中${NC} (http://localhost:5173)"
else
    echo -e "${RED}❌ 未运行${NC}"
fi

echo ""
echo "🧪 运行测试: python test_integration.py"
echo ""
echo "💡 提示: 后端服务已在运行，无需重复启动"
