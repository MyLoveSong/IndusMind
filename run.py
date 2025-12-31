#!/usr/bin/env python3
"""
QWEN3-8B 产业报告生成系统 - 一键运行脚本
SmartDigest - 智能产业报告生成平台

作者: 谢泽宇 (LoveSong) - 后端及大模型构建训练
      陆昊辰 (denis-lu) - 前端开发

项目特色:
- 本地 LoRA 微调 Qwen3-8B 模型
- RAG 检索增强生成
- 现代化 Vue 3 前端界面
- 完整的产业报告生成流程
"""

import os
import sys
import subprocess
import time
import signal
import argparse
from pathlib import Path

class SmartDigestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.organized_project = self.project_root / "organized_project"
        self.processes = []

    def check_dependencies(self):
        """检查必要的依赖"""
        print("🔍 检查系统依赖...")

        # 检查 Python
        try:
            import torch
            print("✅ PyTorch 已安装")
        except ImportError:
            print("❌ PyTorch 未安装，请运行: pip install torch")
            return False

        # 检查 Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js 已安装: {result.stdout.strip()}")
            else:
                print("❌ Node.js 未安装")
                return False
        except FileNotFoundError:
            print("❌ Node.js 未安装")
            return False

        # 检查 CUDA (可选)
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True)
            if result.returncode == 0:
                print("✅ CUDA GPU 可用")
            else:
                print("⚠️ CUDA GPU 不可用，将使用 CPU 模式")
        except FileNotFoundError:
            print("⚠️ CUDA GPU 不可用，将使用 CPU 模式")

        return True

    def start_services(self, with_frontend=True):
        """启动所有服务"""
        print("\n🚀 启动 QWEN3-8B 产业报告生成系统...")
        print("=" * 50)

        # 检查并启动 RAG 服务
        print("1. 启动 RAG 检索服务...")
        rag_script = self.project_root / "start_rag_service.sh"
        if rag_script.exists():
            process = subprocess.Popen(
                ["bash", str(rag_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            self.processes.append(("RAG服务", process))
            print("✅ RAG 服务启动中...")
        else:
            print("⚠️ RAG 启动脚本不存在")

        # 等待 RAG 服务启动
        time.sleep(3)

        # 检查并启动模型服务
        print("2. 启动本地模型服务...")
        model_script = self.project_root / "scripts" / "start_model_server.sh"
        if model_script.exists():
            process = subprocess.Popen(
                ["bash", str(model_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            self.processes.append(("模型服务", process))
            print("✅ 模型服务启动中...")
        else:
            print("⚠️ 模型服务启动脚本不存在")

        # 等待模型服务启动 (需要较长时间)
        print("⏳ 等待模型加载 (可能需要 2-3 分钟)...")
        time.sleep(30)  # 给模型一些启动时间

        # 检查并启动后端服务
        print("3. 启动后端 API 服务...")
        backend_dir = self.project_root / "ZJU-SEM-Project" / "backend"
        if backend_dir.exists():
            process = subprocess.Popen(
                ["npm", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=backend_dir
            )
            self.processes.append(("后端API", process))
            print("✅ 后端服务启动中...")
        else:
            print("⚠️ 后端目录不存在")

        # 等待后端启动
        time.sleep(3)

        # 启动前端服务
        if with_frontend:
            print("4. 启动前端界面...")
            frontend_dir = self.project_root / "ZJU-SEM-Project" / "frontend" / "final-project"
            if frontend_dir.exists():
                process = subprocess.Popen(
                    ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=frontend_dir
                )
                self.processes.append(("前端界面", process))
                print("✅ 前端服务启动中...")
            else:
                print("⚠️ 前端目录不存在")

        print("\n" + "=" * 50)
        print("🎉 系统启动完成!")
        print("=" * 50)
        print("\n🌐 服务地址:")
        print("   • 后端 API:    http://localhost:3000")
        print("   • RAG 服务:    http://127.0.0.1:8002")
        print("   • 模型服务:    http://127.0.0.1:8001")
        if with_frontend:
            print("   • 前端界面:    http://localhost:5173")
        print("\n📝 使用说明:")
        print("   1. 打开浏览器访问前端地址")
        print("   2. 点击'新建产业报告'")
        print("   3. 填写信息并生成AI产业报告")
        print("\n🛑 按 Ctrl+C 停止所有服务")

    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止服务...")
        for name, process in self.processes:
            if process.poll() is None:  # 仍在运行
                print(f"停止 {name}...")
                process.terminate()

        # 等待进程结束
        time.sleep(2)

        # 强制结束仍在运行的进程
        for name, process in self.processes:
            if process.poll() is None:
                process.kill()

        print("✅ 所有服务已停止")

    def run_tests(self):
        """运行功能测试"""
        print("\n🧪 运行功能测试...")
        test_script = self.organized_project / "scripts" / "test_functionality.sh"
        if test_script.exists():
            result = subprocess.run(["bash", str(test_script)])
            return result.returncode == 0
        else:
            print("⚠️ 测试脚本不存在")
            return False

    def check_services_health(self):
        """检查服务健康状态"""
        print("\n🏥 检查服务健康状态...")

        services = [
            ("后端API", "http://localhost:3000/health"),
            ("RAG服务", "http://127.0.0.1:8002/health"),
            ("模型服务", "http://127.0.0.1:8001/health"),
            ("前端界面", "http://localhost:5173")
        ]

        import requests
        healthy_count = 0

        for name, url in services:
            try:
                if "前端" in name:
                    # 前端检查首页
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {name}: 正常")
                        healthy_count += 1
                    else:
                        print(f"❌ {name}: HTTP {response.status_code}")
                else:
                    # API服务检查健康端点
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {name}: 正常")
                        healthy_count += 1
                    else:
                        print(f"❌ {name}: HTTP {response.status_code}")
            except:
                print(f"❌ {name}: 连接失败")

        return healthy_count == len(services)

def main():
    parser = argparse.ArgumentParser(description="QWEN3-8B 产业报告生成系统")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端服务")
    parser.add_argument("--test", action="store_true", help="启动后运行功能测试")
    parser.add_argument("--check", action="store_true", help="仅检查服务状态")

    args = parser.parse_args()

    runner = SmartDigestRunner()

    if args.check:
        # 仅检查服务状态
        runner.check_services_health()
        return

    # 检查依赖
    if not runner.check_dependencies():
        print("❌ 依赖检查失败，请安装必要的依赖后重试")
        sys.exit(1)

    # 设置信号处理
    def signal_handler(sig, frame):
        runner.stop_services()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 启动服务
        with_frontend = not args.no_frontend
        runner.start_services(with_frontend)

        if args.test:
            # 运行测试
            success = runner.run_tests()
            if success:
                print("\n🎉 功能测试通过!")
            else:
                print("\n❌ 功能测试失败!")

        # 保持运行
        print("\n🔄 系统运行中... 按 Ctrl+C 退出")
        while True:
            time.sleep(10)
            # 定期检查服务状态
            if not runner.check_services_health():
                print("⚠️ 检测到服务异常，请检查日志")

    except KeyboardInterrupt:
        pass
    finally:
        runner.stop_services()

if __name__ == "__main__":
    print("🤖 QWEN3-8B 产业报告生成系统")
    print("SmartDigest - 智能产业报告生成平台")
    print("=" * 50)
    main()
