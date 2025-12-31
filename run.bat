@echo off
REM QWEN3-8B 产业报告生成系统 Windows 启动器
REM SmartDigest - 智能产业报告生成平台

echo ======================================================================
echo 🤖 QWEN3-8B 产业报告生成系统
echo SmartDigest - 智能产业报告生成平台
echo ======================================================================
echo.
echo 作者信息:
echo   前端开发: 陆昊辰 (Github: denis-lu)
echo   后端及大模型: 谢泽宇 (Github: LoveSong)
echo ======================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python
    echo 请安装 Python 3.8+ 并添加到 PATH
    pause
    exit /b 1
)

REM 运行主程序
python run.py %*

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错，请检查错误信息
    pause
)

echo.
echo 感谢使用 QWEN3-8B 产业报告生成系统！
pause
