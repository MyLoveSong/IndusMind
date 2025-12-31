#!/bin/bash

# QWEN3-8B 产业报告生成系统开发环境设置脚本

set -e

echo "🚀 设置 QWEN3-8B 产业报告生成系统开发环境"
echo "================================================"

# 检查系统要求
echo "📋 检查系统要求..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 需要安装 Node.js 18+"
    exit 1
fi

# 检查 CUDA (可选)
if command -v nvidia-smi &> /dev/null; then
    echo "✅ 检测到 CUDA GPU"
else
    echo "⚠️ 未检测到 CUDA GPU，将使用 CPU 模式"
fi

echo "✅ 系统要求检查通过"

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装前端依赖
echo "🎨 安装前端依赖..."
cd frontend/main
npm install
cd ../..

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p data logs models/pretrained models/finetuned

# 复制配置文件模板
echo "⚙️ 配置环境变量..."
if [ ! -f ".env" ]; then
    cp configs/.env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

echo ""
echo "🎉 开发环境设置完成！"
echo "================================================"
echo ""
echo "📝 下一步操作："
echo "1. 编辑 .env 文件配置 API 密钥和数据库"
echo "2. 下载或准备模型文件到 models/ 目录"
echo "3. 运行以下命令启动系统："
echo "   bash scripts/start_local_industry_report_stack.sh --with-frontend"
echo ""
echo "📖 更多信息请查看 docs/ 目录下的文档"
