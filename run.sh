#!/bin/bash
# QWEN3-8B 产业报告生成系统启动器
# SmartDigest - 智能产业报告生成平台

echo "🤖 QWEN3-8B 产业报告生成系统"
echo "SmartDigest - 智能产业报告生成平台"
echo "=========================================="
echo ""
echo "作者信息:"
echo "  前端开发: 陆昊辰 (Github: denis-lu)"
echo "  后端及大模型: 谢泽宇 (Github: LoveSong)"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请安装 Python 3.8+ 并重试"
    exit 1
fi

# 设置执行权限
chmod +x run.py 2>/dev/null || true

# 运行主程序
python3 run.py "$@"
