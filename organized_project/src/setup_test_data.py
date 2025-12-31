#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化测试数据
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:3000/api"

def create_test_user():
    """创建测试用户"""
    print("👤 创建测试用户...")

    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            print("✅ 测试用户创建成功")
            return True
        elif response.status_code == 409:
            print("ℹ️  测试用户已存在")
            return True
        else:
            print(f"❌ 创建用户失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 创建用户异常: {e}")
        return False

def login_and_create_reports():
    """登录并创建一些测试报告"""
    print("🔑 登录测试用户...")

    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers={"Content-Type": "application/json"})
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json().get('token')
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        print("✅ 登录成功")

        # 创建一些测试报告
        test_reports = [
            {
                "title": "2025年中国AI产业发展报告",
                "industry": "人工智能",
                "scenario": "投资决策",
                "objective": "分析2025年中国AI产业的发展趋势、市场规模、技术创新和投资机会"
            },
            {
                "title": "新能源汽车产业深度分析",
                "industry": "新能源汽车",
                "scenario": "战略规划",
                "objective": "研究新能源汽车产业的发展现状、竞争格局和技术趋势"
            },
            {
                "title": "区块链技术应用前景研究",
                "industry": "区块链",
                "scenario": "技术评估",
                "objective": "评估区块链技术在各行业的应用前景和商业价值"
            }
        ]

        created_reports = []
        for report_data in test_reports:
            try:
                create_response = requests.post(f"{BASE_URL}/reports", json=report_data, headers=headers)
                if create_response.status_code == 201:
                    report = create_response.json().get('data', {})
                    created_reports.append(report)
                    print(f"✅ 创建报告: {report.get('title')}")
                else:
                    print(f"❌ 创建报告失败: {create_response.status_code} - {create_response.text}")
            except Exception as e:
                print(f"❌ 创建报告异常: {e}")

        print(f"📊 成功创建 {len(created_reports)} 个测试报告")

        # 为第一个报告添加标签
        if created_reports:
            first_report = created_reports[0]
            tags_data = {"tags": ["AI", "产业研究", "2025年"]}
            try:
                tag_response = requests.put(f"{BASE_URL}/reports/{first_report['id']}/tags", json=tags_data, headers=headers)
                if tag_response.status_code == 200:
                    print("✅ 为报告添加标签成功")
                else:
                    print(f"❌ 添加标签失败: {tag_response.status_code}")
            except Exception as e:
                print(f"❌ 添加标签异常: {e}")

        return True

    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 初始化测试数据")
    print("=" * 40)

    # 检查后端是否运行
    try:
        health_response = requests.get("http://localhost:3000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端服务未运行，请先启动后端服务")
            return
    except:
        print("❌ 无法连接到后端服务")
        return

    print("✅ 后端服务运行正常")

    # 执行初始化
    success_count = 0
    total_steps = 2

    if create_test_user():
        success_count += 1

    if login_and_create_reports():
        success_count += 1

    print("=" * 40)
    print(f"🎯 初始化结果: {success_count}/{total_steps} 项成功")

    if success_count == total_steps:
        print("🎉 测试数据初始化完成！")
        print("\n📋 现在可以运行测试:")
        print("python3 test_frontend_integration.py")
    else:
        print("⚠️  初始化部分失败，请检查后端服务")

if __name__ == "__main__":
    main()
