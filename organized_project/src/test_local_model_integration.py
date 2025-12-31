#!/usr/bin/env python3
"""
测试本地模型集成 - 验证Node.js后端直接调用Python模型
"""

import subprocess
import json
import time
import requests

def test_local_model_caller():
    """测试本地模型调用器"""
    print("🧠 测试本地模型调用器...")

    # 测试健康检查
    print("\n1. 测试模型健康检查...")
    test_data = {"action": "health"}

    try:
        # 使用虚拟环境的Python
        result = subprocess.run(
            ['bash', '-c', 'cd /home/xzy/QWEN3-8B/QWEN3-8B && source venv/bin/activate && python3 local_model_caller.py'],
            input=json.dumps(test_data),
            text=True,
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            response = json.loads(result.stdout.strip())
            print("✅ 健康检查成功:")
            print(f"   状态: {response['status']}")
            print(f"   模型已加载: {response['model_loaded']}")
            print(f"   设备: {response['device']}")
            print(f"   CUDA可用: {response['cuda_available']}")
        else:
            print("❌ 健康检查失败:")
            print(f"   错误: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

    # 测试文本生成
    print("\n2. 测试文本生成功能...")
    test_messages = [
        {"role": "system", "content": "你是一个专业的AI助手，请用中文回复。"},
        {"role": "user", "content": "请简单介绍一下人工智能的发展历程。"}
    ]

    test_data = {
        "action": "generate",
        "messages": test_messages,
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        start_time = time.time()
        # 使用虚拟环境的Python
        result = subprocess.run(
            ['bash', '-c', 'cd /home/xzy/QWEN3-8B/QWEN3-8B && source venv/bin/activate && python3 local_model_caller.py'],
            input=json.dumps(test_data),
            text=True,
            capture_output=True,
            timeout=60
        )

        processing_time = time.time() - start_time

        if result.returncode == 0:
            response = json.loads(result.stdout.strip())
            if 'error' not in response:
                content = response['content']
                print(".1f")
                print(f"   内容长度: {len(content)} 字符")
                print(f"   内容预览: {content[:100]}...")

                if len(content) > 10:
                    print("✅ 文本生成成功")
                    return True
                else:
                    print("❌ 生成内容过短")
                    return False
            else:
                print(f"❌ 生成失败: {response['error']}")
                return False
        else:
            print("❌ 文本生成失败:")
            print(f"   错误: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 文本生成异常: {e}")
        return False

def test_backend_integration():
    """测试后端集成"""
    print("\n🔗 测试后端集成...")

    # 检查后端是否运行
    try:
        response = requests.get("http://localhost:3000/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未运行，请先启动后端服务")
            return False
    except:
        print("❌ 后端服务连接失败")
        return False

    # 测试对话API
    print("\n1. 测试对话API...")
    try:
        # 创建对话
        create_response = requests.post(
            "http://localhost:3000/api/ai/conversation/create",
            json={"title": "本地模型集成测试"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if create_response.status_code == 200:
            data = create_response.json()
            session_id = data.get('sessionId')
            print(f"✅ 对话创建成功: {session_id}")

            # 发送消息
            message_response = requests.post(
                f"http://localhost:3000/api/ai/conversation/{session_id}/message",
                json={"content": "请介绍一下你自己"},
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            if message_response.status_code == 200:
                msg_data = message_response.json()
                ai_content = msg_data.get('aiResponse', {}).get('content', '')
                processing_time = msg_data.get('aiResponse', {}).get('metadata', {}).get('processing_time', 0)

                print(".1f")
                print(f"   AI回复预览: {ai_content[:100]}...")
                print("✅ 后端对话API成功")

                return True
            else:
                print(f"❌ 消息发送失败: {message_response.status_code}")
                print(f"   响应: {message_response.text}")
                return False
        else:
            print(f"❌ 对话创建失败: {create_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 后端集成测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始本地模型集成测试")
    print("=" * 50)

    # 测试1: 本地模型调用器
    if not test_local_model_caller():
        print("\n❌ 本地模型调用器测试失败")
        return

    # 测试2: 后端集成
    if not test_backend_integration():
        print("\n❌ 后端集成测试失败")
        return

    print("\n" + "=" * 50)
    print("🎉 所有测试通过！")
    print("\n✅ 本地模型集成成功!")
    print("✅ 后端直接调用大模型正常工作!")
    print("✅ 无需HTTP API，直接进程间通信!")
    print("\n📊 优势:")
    print("- 降低网络延迟")
    print("- 减少序列化开销")
    print("- 提高系统稳定性")
    print("- 更好的错误处理")

if __name__ == "__main__":
    main()
