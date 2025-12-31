#!/bin/bash
# SmartDigest 前后端服务启动脚本

echo "🚀 启动 SmartDigest 智能产业报告生成系统"
echo "=============================================="

# 检查是否已有服务在运行
echo "📋 检查现有服务..."
if netstat -tlnp 2>/dev/null | grep -q ":3000 "; then
    echo "⚠️  检测到3000端口已有服务运行"
else
    echo "✅ 3000端口可用"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5173 "; then
    echo "⚠️  检测到5173端口已有服务运行"
else
    echo "✅ 5173端口可用"
fi

# 启动后端服务
echo ""
echo "🔧 启动后端服务 (端口: 3000)..."
cd "/home/xzy/QWEN3-8B/QWEN3-8B/ZJU-SEM-Project-master/backend"
USE_SQLITE=true SQLITE_DB_PATH=../data.sqlite3 node server.js &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if curl -s http://localhost:3000/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端服务
echo ""
echo "🎨 启动前端服务 (端口: 5173)..."
cd "/home/xzy/QWEN3-8B/QWEN3-8B/ZJU-SEM-Project-master/frontend/final-project"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

# 检查前端是否启动成功
if curl -s -I http://localhost:5173 | grep -q "200 OK"; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
fi

echo ""
echo "🎉 服务启动完成！"
echo "=============================================="
echo "📱 前端界面: http://localhost:5173"
echo "🔗 后端API:   http://localhost:3000"
echo ""
echo "💡 测试账号: testuser / testpass123"
echo ""
echo "🛑 停止服务请运行: kill $BACKEND_PID $FRONTEND_PID"
echo "=============================================="

# 保持脚本运行，显示服务状态
echo ""
echo "📊 服务状态监控 (按 Ctrl+C 退出)..."
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ 后端服务已停止"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端服务已停止"
        break
    fi
    sleep 10
done
