#!/bin/bash
# SmartDigest 服务状态检查脚本

echo "📊 SmartDigest 服务状态检查"
echo "================================"

# 检查后端服务
echo "🔧 后端服务 (localhost:3000):"
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "  ✅ 运行正常"
    # 显示数据库状态
    if netstat -tlnp 2>/dev/null | grep -q ":3306 "; then
        echo "  💾 数据库: MySQL (3306)"
    else
        echo "  💾 数据库: SQLite (文件)"
    fi
else
    echo "  ❌ 未运行或连接失败"
fi

echo ""

# 检查前端服务
echo "🎨 前端服务 (localhost:5173):"
if curl -s -I http://localhost:5173 | grep -q "200 OK"; then
    echo "  ✅ 运行正常"
else
    echo "  ❌ 未运行或连接失败"
fi

echo ""

# 检查其他AI服务
echo "🤖 AI服务状态:"

# 检查本地模型服务器
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "  ✅ 本地QWEN模型 (8001)"
else
    echo "  ❌ 本地QWEN模型 (8001)"
fi

# 检查RAG服务
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "  ✅ RAG增强服务 (8002)"
else
    echo "  ❌ RAG增强服务 (8002)"
fi

# 检查LangChain服务
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "  ✅ LangChain服务 (8003)"
else
    echo "  ❌ LangChain服务 (8003)"
fi

echo ""
echo "💡 快速启动命令:"
echo "   ./start_services.sh    # 启动前后端服务"
echo "   ./check_services.sh    # 检查服务状态"
echo ""
echo "🎯 访问地址:"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:3000"
echo "================================"
