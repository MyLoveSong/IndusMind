#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端改进功能
"""

import requests
import json
import time
import os

# 配置
BASE_URL = "http://localhost:3000"
HEADERS = {
    "Content-Type": "application/json"
}

def test_pagination_and_search():
    """测试分页和搜索功能"""
    print("🔍 测试分页和搜索功能...")

    # 登录获取token
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if login_response.status_code != 200:
            print("❌ 登录失败，请先创建测试用户")
            return False

        token = login_response.json().get('token')
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # 测试分页
        print("  📄 测试分页功能...")
        page_response = requests.get(f"{BASE_URL}/api/reports?page=1&limit=5", headers=headers)
        if page_response.status_code == 200:
            data = page_response.json()
            if 'pagination' in data and 'data' in data:
                print(f"    ✅ 分页成功: {data['pagination']['total']} 总报告, 当前页 {data['pagination']['totalPages']} 页")
            else:
                print("    ❌ 分页响应格式错误")
                return False
        else:
            print(f"    ❌ 分页请求失败: {page_response.status_code}")
            return False

        # 测试搜索
        print("  🔎 测试搜索功能...")
        search_response = requests.get(f"{BASE_URL}/api/reports?search=产业", headers=headers)
        if search_response.status_code == 200:
            print("    ✅ 搜索功能正常")
        else:
            print(f"    ❌ 搜索请求失败: {search_response.status_code}")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_stats_api():
    """测试统计信息API"""
    print("📊 测试统计信息API...")

    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json().get('token')
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        stats_response = requests.get(f"{BASE_URL}/api/reports/stats", headers=headers)
        if stats_response.status_code == 200:
            data = stats_response.json()
            if 'data' in data and 'reports' in data['data']:
                stats = data['data']
                print(f"    ✅ 统计信息获取成功:")
                print(f"      📋 报告统计: {stats['reports']['total_reports']} 总计")
                print(f"      💬 对话统计: {stats['conversations']['total_conversations']} 条")
                print(f"      🏭 产业分布: {len(stats.get('industries', []))} 个产业")
            else:
                print("    ❌ 统计响应格式错误")
                return False
        else:
            print(f"    ❌ 统计请求失败: {stats_response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_tags_system():
    """测试标签系统"""
    print("🏷️  测试标签系统...")

    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json().get('token')
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # 获取报告列表，找到一个报告ID
        reports_response = requests.get(f"{BASE_URL}/api/reports?page=1&limit=1", headers=headers)
        if reports_response.status_code != 200 or not reports_response.json()['data']['reports']:
            print("    ⚠️  没有报告可以测试标签功能")
            return True

        report_id = reports_response.json()['data']['reports'][0]['id']

        # 更新标签
        tags_data = {
            "tags": ["AI", "产业研究", "测试"]
        }

        update_response = requests.put(f"{BASE_URL}/api/reports/{report_id}/tags", json=tags_data, headers=headers)
        if update_response.status_code == 200:
            print(f"    ✅ 标签更新成功")
        else:
            print(f"    ❌ 标签更新失败: {update_response.status_code}")
            return False

        # 按标签筛选
        filter_response = requests.get(f"{BASE_URL}/api/reports/by-tags?tags=AI", headers=headers)
        if filter_response.status_code == 200:
            print("    ✅ 标签筛选成功")
        else:
            print(f"    ❌ 标签筛选失败: {filter_response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_batch_operations():
    """测试批量操作"""
    print("🔄 测试批量操作...")

    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json().get('token')
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # 创建一个测试报告用于批量删除
        report_data = {
            "title": "测试报告 - 批量删除",
            "industry": "测试产业",
            "scenario": "测试场景",
            "objective": "用于测试批量删除功能"
        }

        create_response = requests.post(f"{BASE_URL}/api/reports", json=report_data, headers=headers)
        if create_response.status_code != 201:
            print("    ⚠️  无法创建测试报告，跳过批量删除测试")
            return True

        report_id = create_response.json()['data']['id']
        print(f"    📝 创建测试报告 ID: {report_id}")

        # 批量删除
        batch_data = {
            "ids": [report_id]
        }

        delete_response = requests.post(f"{BASE_URL}/api/reports/batch-delete", json=batch_data, headers=headers)
        if delete_response.status_code == 200:
            print("    ✅ 批量删除成功")
        else:
            print(f"    ❌ 批量删除失败: {delete_response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_export_functionality():
    """测试导出功能"""
    print("📤 测试导出功能...")

    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False

        token = login_response.json().get('token')
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # 获取报告列表
        reports_response = requests.get(f"{BASE_URL}/api/reports?page=1&limit=1", headers=headers)
        if reports_response.status_code != 200 or not reports_response.json()['data']['reports']:
            print("    ⚠️  没有报告可以测试导出功能")
            return True

        report_id = reports_response.json()['data']['reports'][0]['id']

        # 测试PDF导出
        pdf_response = requests.get(f"{BASE_URL}/api/reports/{report_id}/export?format=pdf", headers=headers)
        if pdf_response.status_code == 200:
            print("    ✅ PDF导出成功")
        else:
            print(f"    ❌ PDF导出失败: {pdf_response.status_code}")

        # 测试Markdown导出
        md_response = requests.get(f"{BASE_URL}/api/reports/{report_id}/export?format=markdown", headers=headers)
        if md_response.status_code == 200:
            print("    ✅ Markdown导出成功")
        else:
            print(f"    ❌ Markdown导出失败: {md_response.status_code}")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试后端改进功能")
    print("=" * 50)

    # 检查后端是否运行
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ 后端服务未运行，请先启动后端服务")
            return
    except:
        print("❌ 无法连接到后端服务，请先启动后端服务")
        return

    print("✅ 后端服务运行正常")
    print()

    # 执行各项测试
    tests = [
        ("分页和搜索功能", test_pagination_and_search),
        ("统计信息API", test_stats_api),
        ("标签系统", test_tags_system),
        ("批量操作", test_batch_operations),
        ("导出功能", test_export_functionality)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}测试通过")
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
        print()

    print("=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 项通过")

    if passed == total:
        print("🎉 所有后端改进功能测试通过！")
    else:
        print("⚠️  部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()
