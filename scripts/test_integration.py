#!/usr/bin/env python3
"""
Integration Test Script for Local QWEN3-8B Model
Tests the complete integration from model server to frontend API
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
MODEL_SERVER_URL = "http://127.0.0.1:8001"
BACKEND_URL = "http://localhost:3000"
TEST_MESSAGE = "请简单介绍一下你自己和你的能力。"

def test_model_server_health() -> Dict[str, Any]:
    """Test model server health endpoint"""
    print("🔍 Testing model server health...")

    try:
        response = requests.get(f"{MODEL_SERVER_URL}/health", timeout=10)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Model server health check passed: {data.get('status', 'unknown')}")

        if data.get('model_loaded') is False:
            print("⚠️  Warning: Model not loaded yet, may take a few minutes")
        elif data.get('model_loaded') is True:
            print("✅ Model is loaded and ready")

        return {"success": True, "data": data}

    except requests.exceptions.RequestException as e:
        print(f"❌ Model server health check failed: {e}")
        return {"success": False, "error": str(e)}

def test_model_server_chat() -> Dict[str, Any]:
    """Test direct model server chat endpoint"""
    print("🔍 Testing direct model server chat...")

    payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "你是智能助手，请简洁准确地回答问题。"},
            {"role": "user", "content": TEST_MESSAGE}
        ],
        "max_tokens": 500,
        "temperature": 0.35
    }

    try:
        response = requests.post(
            f"{MODEL_SERVER_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        print("✅ Direct model server chat successful")
        print(f"📝 Response preview: {content[:100]}...")

        return {"success": True, "response": content}

    except requests.exceptions.RequestException as e:
        print(f"❌ Direct model server chat failed: {e}")
        return {"success": False, "error": str(e)}

def test_backend_ai_status() -> Dict[str, Any]:
    """Test backend AI status endpoint"""
    print("🔍 Testing backend AI status...")

    try:
        response = requests.get(f"{BACKEND_URL}/api/ai/status", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend AI status check passed: {data.get('status', 'unknown')}")
            return {"success": True, "data": data}
        else:
            print(f"❌ Backend AI status check failed: HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}

    except requests.exceptions.RequestException as e:
        print(f"❌ Backend AI status check failed: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Run all integration tests"""
    print("🚀 Starting Local QWEN3-8B Integration Tests")
    print("=" * 50)

    results = []

    # Test 1: Model Server Health
    result1 = test_model_server_health()
    results.append(("Model Server Health", result1))
    print()

    # Test 2: Direct Model Chat (only if health check passed)
    if result1.get("success"):
        result2 = test_model_server_chat()
        results.append(("Direct Model Chat", result2))
        print()
    else:
        results.append(("Direct Model Chat", {"success": False, "error": "Skipped - Model server not healthy"}))
        print("⏭️  Skipping direct model chat test (model server not healthy)\n")

    # Test 3: Backend AI Status
    result3 = test_backend_ai_status()
    results.append(("Backend AI Status", result3))
    print()

    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"  {name}: {status}")
        if result.get("success"):
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("💡 Make sure all services are running:")
        print("   1. Model server: python model_server.py")
        print("   2. Backend: npm start (in backend directory)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
