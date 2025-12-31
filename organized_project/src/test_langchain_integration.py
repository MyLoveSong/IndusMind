#!/usr/bin/env python
"""
LangChain集成完整性测试脚本
测试微调模型 + RAG + LangChain的完整流程
"""

import requests
import json
import time
from typing import Dict, Any

def test_service_health(service_name: str, url: str) -> bool:
    """测试服务健康状态"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name}: 正常运行")
            return True
        else:
            print(f"⚠️ {service_name}: 返回状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name}: 连接失败 - {str(e)}")
        return False

def test_langchain_chat():
    """测试LangChain对话功能"""
    print("\n🗣️ 测试LangChain对话功能...")

    try:
        response = requests.post(
            "http://127.0.0.1:8003/chat",
            json={
                "message": "请简单介绍一下中国数字经济的发展现状。",
                "conversation_history": []
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ LangChain对话测试成功")
            print(f"回答预览: {result['answer'][:150]}...")
            return True
        else:
            print(f"❌ LangChain对话测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ LangChain对话测试异常: {str(e)}")
        return False

def test_langchain_report_generation():
    """测试LangChain报告生成功能"""
    print("\n📄 测试LangChain报告生成功能...")

    try:
        response = requests.post(
            "http://127.0.0.1:8003/generate_report",
            json={
                "industry": "人工智能",
                "scenario": "企业数字化转型",
                "objective": "分析AI技术在企业中的应用价值和实施策略"
            },
            timeout=120  # 报告生成可能需要更长时间
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ LangChain报告生成测试成功")
                print(f"报告预览: {result['content'][:200]}...")
                return True
            else:
                print(f"❌ 报告生成失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 报告生成HTTP错误: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 报告生成测试异常: {str(e)}")
        return False

def test_backend_langchain_integration():
    """测试后端LangChain集成"""
    print("\n🔗 测试后端LangChain集成...")

    try:
        response = requests.post(
            "http://localhost:3000/api/reports/langchain/chat",
            json={
                "message": "人工智能技术将如何影响传统制造业？",
                "conversation_history": []
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 后端LangChain集成测试成功")
                print(f"回答预览: {result['answer'][:150]}...")
                return True
            else:
                print(f"❌ 后端集成失败: {result}")
                return False
        else:
            print(f"❌ 后端集成HTTP错误: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 后端集成测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 LangChain集成完整性测试")
    print("=" * 50)

    # 1. 检查所有服务状态
    print("\n🔍 检查服务状态...")
    services_status = {
        "RAG服务": test_service_health("RAG服务", "http://127.0.0.1:8002/health"),
        "LangChain服务": test_service_health("LangChain服务", "http://127.0.0.1:8003/health"),
        "模型服务": test_service_health("模型服务", "http://127.0.0.1:8001/health"),
        "后端服务": test_service_health("后端服务", "http://localhost:3000/health"),
    }

    # 2. 如果所有服务都运行正常，进行功能测试
    if all(services_status.values()):
        print("\n🎯 所有服务正常，开始功能测试...")

        # 测试LangChain直接调用
        langchain_chat_ok = test_langchain_chat()

        # 测试报告生成
        langchain_report_ok = test_langchain_report_generation()

        # 测试后端集成
        backend_integration_ok = test_backend_langchain_integration()

        print("\n" + "=" * 50)
        print("📊 测试结果汇总:"        print(f"   • LangChain对话: {'✅' if langchain_chat_ok else '❌'}")
        print(f"   • 报告生成: {'✅' if langchain_report_ok else '❌'}")
        print(f"   • 后端集成: {'✅' if backend_integration_ok else '❌'}")

        if all([langchain_chat_ok, langchain_report_ok, backend_integration_ok]):
            print("\n🎉 恭喜！微调+RAG+LangChain完整系统测试通过！")
            print("   您的AI产业报告生成系统已经完全就绪！")
        else:
            print("\n⚠️ 部分测试未通过，请检查相关服务配置。")

    else:
        print("\n❌ 部分服务未启动，无法进行完整测试。")
        print("请确保以下服务正在运行：")
        for service, status in services_status.items():
            if not status:
                print(f"   • {service}: 需要启动")

    print("\n💡 提示：")
    print("   如需单独启动服务，可以使用以下命令：")
    print("   • RAG服务: bash start_rag_service.sh")
    print("   • LangChain服务: bash start_langchain_service.sh")
    print("   • 完整系统: bash start_complete_system.sh")

if __name__ == "__main__":
    main()
