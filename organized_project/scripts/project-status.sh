#!/bin/bash

# QWEN3-8B 产业报告生成系统状态检查脚本

echo "📊 QWEN3-8B 产业报告生成系统状态检查"
echo "================================================"

# 检查目录结构
echo "📁 检查项目结构..."
directories=("docs" "scripts" "logs" "configs" "models" "data" "src" "frontend" "tests" "docker")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ (缺失)"
    fi
done

echo ""

# 检查关键文件
echo "📄 检查关键文件..."
key_files=("README.md" "requirements.txt" "scripts/start_local_industry_report_stack.sh")
for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失)"
    fi
done

echo ""

# 检查 Python 环境
echo "🐍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "  ✅ Python: $python_version"
else
    echo "  ❌ Python 未安装"
fi

# 检查 Node.js 环境
echo "📦 检查 Node.js 环境..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "  ✅ Node.js: $node_version"
else
    echo "  ❌ Node.js 未安装"
fi

echo ""

# 检查模型文件
echo "🤖 检查模型文件..."
if [ -d "models/pretrained" ] && [ "$(ls -A models/pretrained 2>/dev/null)" ]; then
    echo "  ✅ 预训练模型文件存在"
else
    echo "  ⚠️ 预训练模型文件缺失"
fi

if [ -d "models/finetuned" ] && [ "$(ls -A models/finetuned 2>/dev/null)" ]; then
    echo "  ✅ 微调模型文件存在"
else
    echo "  ⚠️ 微调模型文件缺失"
fi

echo ""

# 检查配置文件
echo "⚙️ 检查配置文件..."
if [ -f ".env" ]; then
    echo "  ✅ 环境配置文件存在"
else
    echo "  ⚠️ 环境配置文件缺失 (可从 configs/.env.example 复制)"
fi

echo ""

# 检查日志文件
echo "📋 检查日志文件..."
log_count=$(find logs/ -name "*.log" 2>/dev/null | wc -l)
if [ "$log_count" -gt 0 ]; then
    echo "  ✅ 发现 $log_count 个日志文件"
else
    echo "  ℹ️ 暂无日志文件"
fi

echo ""

# 检查数据文件
echo "💾 检查数据文件..."
if [ -d "data" ] && [ "$(ls -A data 2>/dev/null)" ]; then
    data_files=$(find data/ -type f | wc -l)
    echo "  ✅ 数据目录包含 $data_files 个文件"
else
    echo "  ℹ️ 数据目录为空"
fi

echo ""
echo "🎯 快速操作:"
echo "  启动系统: bash scripts/start_local_industry_report_stack.sh --with-frontend"
echo "  检查服务: bash scripts/check_services.sh"
echo "  停止服务: bash scripts/stop_local_industry_report_stack.sh"
echo ""
echo "================================================"
