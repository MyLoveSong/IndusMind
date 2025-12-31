#!/usr/bin/env python3
"""
运行后端性能测试脚本
自动测试Qwen3-8B后端API的表现
"""

import json
import requests
import time
from datetime import datetime
import os

def load_test_case(test_file):
    """加载测试用例"""
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_to_backend(test_case):
    """发送测试请求到后端"""
    try:
        # 构造请求体
        request_data = {
            "model": "Qwen/Qwen3-8B",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的产业研究员。请严格按照要求输出结构化的报告内容。"
                },
                {
                    "role": "user",
                    "content": f"{test_case['input']['instruction']}\n\n{test_case['input']['context']}\n\n{test_case['input'].get('template', '')}"
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        print(f"📤 发送请求到后端API...")
        start_time = time.time()

        # 先创建对话会话
        session_response = requests.post(
            "http://localhost:3000/api/ai/conversation/create",
            json={"title": f"性能测试 - {test_case['test_name']}"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if session_response.status_code != 200:
            return {
                "success": False,
                "error": f"创建会话失败: {session_response.status_code}",
                "response_time": 0
            }

        session_data = session_response.json()
        session_id = session_data.get("sessionId")

        if not session_id:
            return {
                "success": False,
                "error": "无法获取会话ID",
                "response_time": 0
            }

        # 发送消息到后端API（这样才能测试改进的提示词）
        response = requests.post(
            f"http://localhost:3000/api/ai/conversation/{session_id}/message",
            json={"content": test_case["input"]["instruction"] + "\n\n" + test_case["input"]["context"]},
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分钟超时，处理复杂任务
        )

        end_time = time.time()
        response_time = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("aiResponse", {})
            content = ai_response.get("content", "")

            if content:
                return {
                    "success": True,
                    "content": content,
                    "response_time": response_time,
                    "tokens": ai_response.get("metadata", {}).get("tokens", 0)
                }
            else:
                return {
                    "success": False,
                    "error": "AI响应内容为空",
                    "response_time": response_time
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response_time
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def evaluate_response(test_case, response):
    """评估AI响应质量"""
    if not response["success"]:
        return {
            "overall_score": 0,
            "criteria_scores": {},
            "issues": [f"请求失败: {response['error']}"]
        }

    content = response["content"]
    criteria = test_case["evaluation_criteria"]

    scores = {}
    issues = []

    # 改进的章节识别逻辑
    def check_section_presence(section_name, content):
        """更精确地检查章节是否存在"""
        # 标准格式检查（优先级最高）
        standard_patterns = [
            f"## {section_name}",
            f"### {section_name}",
            f"#### {section_name}",
            f"**{section_name}**",
            f"【{section_name}】",
            f"({section_name})",
            f"{section_name}：",
            f"{section_name}:"
        ]

        # 检查是否包含章节标题
        for pattern in standard_patterns:
            if pattern in content:
                return True

        # 内容相关性检查（智能识别）
        content_lower = content.lower()
        section_lower = section_name.lower()

        if section_name == "摘要":
            # 摘要通常在开头，包含总结性关键词
            first_part = content[:800]  # 检查前800字符
            summary_indicators = [
                "总结", "概述", "主要内容", "核心观点", "总体情况",
                "本文主要", "报告主要", "内容概要", "abstract", "summary"
            ]
            # 检查是否有明显的总结性表述
            has_summary_content = any(indicator in first_part for indicator in summary_indicators)
            # 检查是否有概括性语言特征
            has_summary_style = any(phrase in first_part for phrase in [
                "综上所述", "总的来说", "总体而言", "主要包括", "核心是"
            ])
            return has_summary_content or has_summary_style

        elif section_name == "正文":
            # 正文通常在中间，包含分析性内容
            middle_part = content[200:len(content)-200]  # 排除开头和结尾
            analysis_indicators = [
                "分析", "研究", "发展", "趋势", "数据", "技术",
                "特点", "现状", "情况", "影响", "作用", "重要性"
            ]
            return any(indicator in middle_part for indicator in analysis_indicators)

        elif section_name == "结论":
            # 结论通常在结尾，包含建议性内容
            last_part = content[-1000:]  # 检查最后1000字符
            conclusion_indicators = [
                "结论", "建议", "展望", "总结", "发现", "因此",
                "综上", "建议", "未来", "发展方向", "战略建议"
            ]
            # 检查是否有结论性表述
            has_conclusion_content = any(indicator in last_part for indicator in conclusion_indicators)
            # 检查是否有建议性语言
            has_recommendation_style = any(phrase in last_part for phrase in [
                "应加强", "需要重视", "建议", "应当", "可以考虑", "有望"
            ])
            return has_conclusion_content or has_recommendation_style

        return False

    # 基础结构检查
    if "expected_output_format" in test_case:
        structure = test_case["expected_output_format"].get("structure", [])
        for section in structure:
            if check_section_presence(section, content):
                scores[f"structure_{section.lower()}"] = 1
            else:
                issues.append(f"缺少必要章节: {section}")
                scores[f"structure_{section.lower()}"] = 0

    # 内容质量评估
    content_length = len(content)
    if content_length < 200:
        issues.append("内容过短，缺乏足够分析")
        scores["content_length"] = 0.3
    elif content_length < 500:
        scores["content_length"] = 0.7
    elif content_length < 1000:
        scores["content_length"] = 1.0
    else:
        scores["content_length"] = 0.9  # 过长可能影响质量

    # 检查专业术语使用（扩展关键词列表）
    professional_terms = [
        "技术", "发展", "趋势", "分析", "结论", "摘要",
        "产业", "市场", "数据", "研究", "政策", "创新",
        "数字化", "智能化", "转型升级", "高质量发展"
    ]
    found_terms = sum(1 for term in professional_terms if term in content)
    scores["professional_terms"] = min(found_terms / max(1, len(professional_terms) * 0.3), 1.0)

    # 检查逻辑结构（更严格的检查）
    structure_score = 0
    if "## 摘要" in content or "## 正文" in content or "## 结论" in content:
        structure_score = 1.0
    elif "摘要" in content and "结论" in content:
        structure_score = 0.8
    elif "分析" in content or "研究" in content:
        structure_score = 0.6
    else:
        structure_score = 0.3

    scores["logical_structure"] = structure_score

    # 检查内容连贯性
    coherence_score = 0.5  # 基础分数

    # 检查段落结构
    paragraphs = content.split('\n\n')
    if len(paragraphs) >= 3:
        coherence_score += 0.2

    # 检查是否有数据引用
    if any(char.isdigit() for char in content):
        coherence_score += 0.1

    # 检查是否有专业分析
    analysis_indicators = ["因此", "根据", "研究显示", "数据显示", "发展趋势"]
    if any(indicator in content for indicator in analysis_indicators):
        coherence_score += 0.2

    scores["content_coherence"] = min(coherence_score, 1.0)

    # 计算总体分数（加权计算）
    if scores:
        weights = {
            "structure_摘要": 1.5,
            "structure_正文": 1.5,
            "structure_结论": 1.5,
            "content_length": 1.0,
            "professional_terms": 1.0,
            "logical_structure": 1.2,
            "content_coherence": 1.0
        }

        weighted_sum = 0
        total_weight = 0

        for key, score in scores.items():
            weight = weights.get(key, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        overall_score = 0

    return {
        "overall_score": round(overall_score, 2),
        "criteria_scores": scores,
        "issues": issues,
        "content_length": content_length
    }

def run_performance_tests():
    """运行所有性能测试"""
    print("🧪 开始后端性能测试")
    print("=" * 60)

    # 检查服务状态
    print("\n1. 检查服务状态...")

    # 检查后端API
    try:
        response = requests.get("http://localhost:3000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端API: 运行正常")
        else:
            print("❌ 后端API: 状态异常")
            return
    except:
        print("❌ 后端API: 连接失败，请确保后端服务已启动")
        print("   运行命令: cd QWEN3-8B/QWEN3-8B/ZJU-SEM-Project-master/backend && npm start")
        return

    print("✅ 模型集成: 通过本地调用（无需独立模型服务器）")

    # 查找测试文件
    test_files = [f for f in os.listdir('.') if f.startswith('test_backend_performance_') and f.endswith('.json')]
    test_files.sort()

    if not test_files:
        print("❌ 未找到测试文件")
        return

    print(f"\n2. 发现 {len(test_files)} 个测试用例")

    # 运行测试
    results = []

    for i, test_file in enumerate(test_files, 1):
        print(f"\n{'='*40}")
        print(f"测试 {i}: {test_file}")
        print('='*40)

        # 加载测试用例
        test_case = load_test_case(test_file)
        print(f"📋 测试名称: {test_case['test_name']}")
        print(f"📝 描述: {test_case['description']}")

        # 发送请求
        response = send_to_backend(test_case)

        if response["success"]:
            print("✅ 请求成功")
            print(".1f")
            print(f"📊 Token使用: {response['tokens']}")

            # 评估响应质量
            evaluation = evaluate_response(test_case, response)

            print("\n🎯 质量评估:")
            print(".2f")
            print(f"📏 内容长度: {evaluation['content_length']} 字符")

            if evaluation["issues"]:
                print("⚠️  发现问题:")
                for issue in evaluation["issues"]:
                    print(f"   - {issue}")

            # 显示部分内容
            content_preview = response["content"][:300] + "..." if len(response["content"]) > 300 else response["content"]
            print("\n📄 内容预览:")
            print(content_preview)

        else:
            print("❌ 请求失败")
            print(f"错误: {response['error']}")
            evaluation = {"overall_score": 0, "issues": [response['error']]}

        results.append({
            "test_file": test_file,
            "test_name": test_case["test_name"],
            "success": response["success"],
            "response_time": response.get("response_time", 0),
            "evaluation": evaluation
        })

    # 生成总结报告
    print("\n" + "="*60)
    print("📊 测试总结报告")
    print("="*60)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    avg_score = sum(r["evaluation"]["overall_score"] for r in results) / total_tests if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"成功测试: {successful_tests}")
    print(".1f")
    print(".2f")
    # 详细结果
    print("\n📋 详细结果:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        score = result["evaluation"]["overall_score"]
        time_taken = result["response_time"]
        print(".1f")
    # 保存完整报告
    report = {
        "test_run_time": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_score": avg_score
        },
        "results": results,
        "recommendations": [
            "定期运行性能测试以监控AI质量",
            "根据测试结果调整提示词和参数",
            "关注响应时间和资源使用情况",
            "持续优化AI模型的输出质量"
        ]
    }

    with open("backend_performance_test_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n✅ 测试报告已保存: backend_performance_test_results.json")
    print("\n🎉 后端性能测试完成！")

if __name__ == "__main__":
    run_performance_tests()
