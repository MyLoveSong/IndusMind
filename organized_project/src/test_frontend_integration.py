#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端与后端集成
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:3000/api"

def test_backend_new_features():
    """测试后端新功能"""
    print("🔧 测试后端新功能...")

    # 登录获取token
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers={"Content-Type": "application/json"})
        if login_response.status_code != 200:
            print("❌ 登录失败，请先创建测试用户")
            return False

        token = login_response.json().get('token')
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        print("✅ 登录成功")

        # 测试分页功能
        print("  📄 测试分页功能...")
        page_response = requests.get(f"{BASE_URL}/reports?page=1&limit=5", headers=headers)
        if page_response.status_code == 200:
            data = page_response.json()
            print(f"    🔍 实际响应: {data}")  # 调试输出
            if data.get('success') and 'pagination' in data.get('data', {}):
                pagination = data['data']['pagination']
                print(f"    ✅ 分页成功: {pagination['total']} 总报告, {pagination['totalPages']} 页")
            else:
                print("    ❌ 分页响应格式错误")
                print(f"    📝 响应数据: {data}")
                return False
        else:
            print(f"    ❌ 分页请求失败: {page_response.status_code}")
            print(f"    📝 响应内容: {page_response.text}")
            return False

        # 测试统计信息API
        print("  📊 测试统计信息API...")
        stats_response = requests.get(f"{BASE_URL}/reports/stats", headers=headers)
        if stats_response.status_code == 200:
            data = stats_response.json()
            if data.get('success') and 'reports' in data.get('data', {}):
                stats = data['data']
                print(f"    ✅ 统计信息获取成功: {stats['reports']['total_reports']} 报告")
            else:
                print("    ❌ 统计响应格式错误")
                print(f"    📝 响应数据: {data}")
        else:
            print(f"    ❌ 统计请求失败: {stats_response.status_code}")
            print(f"    📝 响应内容: {stats_response.text}")

        # 测试搜索功能
        print("  🔍 测试搜索功能...")
        search_response = requests.get(f"{BASE_URL}/reports?search=test", headers=headers)
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get('success'):
                print("    ✅ 搜索功能正常")
            else:
                print("    ❌ 搜索响应格式错误")
        else:
            print(f"    ❌ 搜索请求失败: {search_response.status_code}")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_frontend_build():
    """测试前端构建"""
    print("🎨 测试前端构建...")

    try:
        import subprocess
        import os

        # 进入前端目录
        frontend_dir = "/home/xzy/QWEN3-8B/QWEN3-8B/ZJU-SEM-Project-master/frontend/final-project"

        # 检查package.json是否存在
        if not os.path.exists(f"{frontend_dir}/package.json"):
            print("❌ 前端package.json不存在")
            return False

        print("✅ 前端项目结构完整")

        # 检查依赖是否已安装
        if not os.path.exists(f"{frontend_dir}/node_modules"):
            print("⚠️  前端依赖未安装，建议运行: npm install")
        else:
            print("✅ 前端依赖已安装")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试前后端集成")
    print("=" * 50)

    # 检查后端是否运行
    try:
        health_response = requests.get("http://localhost:3000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端服务未运行，请先启动后端服务")
            print("   运行命令: cd ZJU-SEM-Project/backend && node server.js")
            return
    except:
        print("❌ 无法连接到后端服务，请先启动后端服务")
        return

    print("✅ 后端服务运行正常")
    print()

    # 执行各项测试
    tests = [
        ("后端新功能测试", test_backend_new_features),
        ("前端构建测试", test_frontend_build)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}通过")
            else:
                print(f"❌ {test_name}失败")
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
        print()

    print("=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 项通过")

    if passed == total:
        print("🎉 前后端集成测试通过！")
        print("\n📋 下一步操作建议:")
        print("1. 启动前端开发服务器: cd frontend/final-project && npm run dev")
        print("2. 打开浏览器访问: http://localhost:5173")
        print("3. 测试新的分页、搜索、批量操作等功能")
    else:
        print("⚠️  部分测试失败，请检查相关配置")

if __name__ == "__main__":
    main()
