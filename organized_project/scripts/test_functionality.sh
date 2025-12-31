#!/bin/bash

# QWEN3-8B 产业报告生成系统功能测试脚本

echo "🧪 QWEN3-8B 产业报告生成系统功能测试"
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试函数
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "测试 $service_name... "

    if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        return 1
    fi
}

# 测试 API 端点
test_api_endpoint() {
    local endpoint_name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "测试 $endpoint_name ($method $url)... "

    if curl -s -X "$method" --max-time 10 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        return 1
    fi
}

# 1. 测试服务可用性
echo "1. 服务可用性测试"
echo "-------------------"

test_service "后端API服务" "http://localhost:3000/health"
BACKEND_OK=$?

test_service "RAG检索服务" "http://127.0.0.1:8002/health"
RAG_OK=$?

test_service "本地模型服务" "http://127.0.0.1:8001/health"
MODEL_OK=$?

test_service "前端界面" "http://localhost:5173"
FRONTEND_OK=$?

echo

# 2. 测试 API 功能
echo "2. API 功能测试"
echo "----------------"

if [ $BACKEND_OK -eq 0 ]; then
    # 测试获取报告列表
    test_api_endpoint "获取报告列表" "http://localhost:3000/api/reports" "GET"
    REPORTS_OK=$?

    # 测试创建报告
    echo -n "测试创建报告... "
    CREATE_RESPONSE=$(curl -s -X POST http://localhost:3000/api/reports \
        -H "Content-Type: application/json" \
        -d '{"title":"功能测试报告","industry":"测试行业","scenario":"功能验证","objective":"验证系统功能","data_sources":[]}' \
        --max-time 30 2>/dev/null)

    if echo "$CREATE_RESPONSE" | grep -q "reportId"; then
        echo -e "${GREEN}✅ 通过${NC}"
        CREATE_OK=0

        # 提取报告ID
        REPORT_ID=$(echo "$CREATE_RESPONSE" | sed -n 's/.*"reportId"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p')

        if [ -n "$REPORT_ID" ]; then
            echo "创建的报告ID: $REPORT_ID"

            # 测试生成报告
            echo -n "测试生成报告... "
            GENERATE_RESPONSE=$(curl -s -X POST "http://localhost:3000/api/reports/$REPORT_ID/generate" \
                -H "Content-Type: application/json" \
                -d '{}' \
                --max-time 120 2>/dev/null)

            if echo "$GENERATE_RESPONSE" | grep -q "成功\|success"; then
                echo -e "${GREEN}✅ 通过${NC}"
                GENERATE_OK=0

                # 检查报告状态
                echo -n "检查报告完成状态... "
                STATUS_RESPONSE=$(curl -s "http://localhost:3000/api/reports/$REPORT_ID" --max-time 10 2>/dev/null)
                if echo "$STATUS_RESPONSE" | grep -q '"status":"completed"'; then
                    echo -e "${GREEN}✅ 通过${NC}"
                    STATUS_OK=0
                else
                    echo -e "${RED}❌ 失败 (状态: $(echo "$STATUS_RESPONSE" | sed -n 's/.*"status":"*\([^"]*\)".*/\1/p'))${NC}"
                    STATUS_OK=1
                fi
            else
                echo -e "${RED}❌ 失败${NC}"
                GENERATE_OK=1
                STATUS_OK=1
            fi
        else
            echo -e "${RED}❌ 无法提取报告ID${NC}"
            GENERATE_OK=1
            STATUS_OK=1
        fi
    else
        echo -e "${RED}❌ 失败${NC}"
        CREATE_OK=1
        GENERATE_OK=1
        STATUS_OK=1
    fi

    # 测试报告列表是否更新
    if [ $REPORTS_OK -eq 0 ] && [ $CREATE_OK -eq 0 ]; then
        echo -n "测试报告列表更新... "
        LIST_RESPONSE=$(curl -s "http://localhost:3000/api/reports" --max-time 10 2>/dev/null)
        if echo "$LIST_RESPONSE" | grep -q "$REPORT_ID"; then
            echo -e "${GREEN}✅ 通过${NC}"
            LIST_OK=0
        else
            echo -e "${RED}❌ 失败${NC}"
            LIST_OK=1
        fi
    fi
else
    echo "跳过 API 功能测试 (后端不可用)"
    REPORTS_OK=1
    CREATE_OK=1
    GENERATE_OK=1
    STATUS_OK=1
    LIST_OK=1
fi

echo

# 3. 测试前端代理
echo "3. 前端代理测试"
echo "----------------"

if [ $FRONTEND_OK -eq 0 ]; then
    test_api_endpoint "前端代理健康检查" "http://localhost:5173/api/health" "GET"
    PROXY_OK=$?

    if [ $CREATE_OK -eq 0 ] && [ -n "$REPORT_ID" ]; then
        test_api_endpoint "前端代理获取报告" "http://localhost:5173/api/reports/$REPORT_ID" "GET"
        PROXY_REPORT_OK=$?
    else
        PROXY_REPORT_OK=1
    fi
else
    echo "跳过前端代理测试 (前端不可用)"
    PROXY_OK=1
    PROXY_REPORT_OK=1
fi

echo

# 4. 测试总结
echo "4. 测试总结"
echo "------------"

TOTAL_TESTS=9
PASSED_TESTS=0

# 计算通过的测试数
[ $BACKEND_OK -eq 0 ] && ((PASSED_TESTS++))
[ $RAG_OK -eq 0 ] && ((PASSED_TESTS++))
[ $MODEL_OK -eq 0 ] && ((PASSED_TESTS++))
[ $FRONTEND_OK -eq 0 ] && ((PASSED_TESTS++))
[ $REPORTS_OK -eq 0 ] && ((PASSED_TESTS++))
[ $CREATE_OK -eq 0 ] && ((PASSED_TESTS++))
[ $GENERATE_OK -eq 0 ] && ((PASSED_TESTS++))
[ $STATUS_OK -eq 0 ] && ((PASSED_TESTS++))
[ $PROXY_OK -eq 0 ] && ((PASSED_TESTS++))

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}🎉 测试通过率: $PASSED_TESTS/$TOTAL_TESTS ($SUCCESS_RATE%)${NC}"
    echo -e "${GREEN}✅ 系统功能正常${NC}"
    exit 0
elif [ $SUCCESS_RATE -ge 50 ]; then
    echo -e "${YELLOW}⚠️ 测试通过率: $PASSED_TESTS/$TOTAL_TESTS ($SUCCESS_RATE%)${NC}"
    echo -e "${YELLOW}⚠️ 系统功能部分正常${NC}"
    exit 1
else
    echo -e "${RED}❌ 测试通过率: $PASSED_TESTS/$TOTAL_TESTS ($SUCCESS_RATE%)${NC}"
    echo -e "${RED}❌ 系统功能异常${NC}"
    exit 1
fi
