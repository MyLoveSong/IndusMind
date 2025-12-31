#!/usr/bin/env python
"""
LangChain服务：整合微调QWEN模型 + RAG检索 + LangChain链式调用
实现完整的AI应用流程管理
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import Document

class LocalQWENChat:
    """本地QWEN模型的LangChain包装器"""

    def __init__(self, base_url: str = "http://127.0.0.1:8001", model_name: str = "Qwen/Qwen3-8B"):
        self.base_url = base_url
        self.model_name = model_name
        self.client = ChatOpenAI(
            base_url=base_url + "/v1",
            api_key="local-qwen",  # 本地模型不需要真实API key
            model_name=model_name,
            temperature=0.35,
            max_tokens=2000,
        )

    def __call__(self, messages: List[BaseMessage]) -> str:
        """调用本地QWEN模型"""
        try:
            response = self.client.invoke(messages)
            return response.content
        except Exception as e:
            print(f"本地QWEN调用失败: {e}")
            return f"模型调用失败: {str(e)}"

class EnhancedRAGSystem:
    """增强的RAG系统：基于LangChain实现"""

    def __init__(self, rag_url: str = "http://127.0.0.1:8002"):
        self.rag_url = rag_url
        self.llm = LocalQWENChat()
        self.vectorstore = None
        self.memory = ConversationBufferWindowMemory(
            k=5,  # 保留最近5轮对话
            return_messages=True
        )

        # 初始化向量存储（如果有本地FAISS索引）
        self._init_vectorstore()

        # 创建RAG检索链
        self.qa_chain = self._create_qa_chain()

    def _init_vectorstore(self):
        """初始化向量存储"""
        try:
            # 尝试加载本地的FAISS索引
            embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-zh-v1.5",
                model_kwargs={'device': 'cpu'},  # 使用CPU以避免显存冲突
                encode_kwargs={'normalize_embeddings': True}
            )

            faiss_path = "/home/xzy/QWEN3-8B/data/rag"
            if os.path.exists(os.path.join(faiss_path, "faiss.index")):
                self.vectorstore = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
                print("✅ LangChain向量存储初始化成功")
            else:
                print("⚠️ 未找到本地FAISS索引，使用RAG API")
        except Exception as e:
            print(f"⚠️ 向量存储初始化失败: {e}，将使用RAG API")

    def _create_qa_chain(self):
        """创建问答链"""
        if self.vectorstore:
            # 使用本地向量存储
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

            template = """基于以下上下文信息回答用户的问题。如果你无法从上下文中找到答案，就说你不知道。

上下文信息:
{context}

用户问题: {question}

请提供准确、专业的回答:"""

            prompt = ChatPromptTemplate.from_template(template)

            chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
        else:
            # 使用RAG API（降级方案）
            chain = self._create_api_based_chain()

        return chain

    def _create_api_based_chain(self):
        """创建基于RAG API的链"""
        def rag_retrieve_and_answer(question: str) -> str:
            try:
                import requests
                response = requests.post(
                    f"{self.rag_url}/query",
                    json={
                        "query": question,
                        "k": 3,
                        "max_length": 1500,
                        "temperature": 0.3
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    context = ""
                    if data.get("sources"):
                        context = "\n\n".join([
                            f"[来源: {source.get('title', '未知')}]\n{source.get('content', '')}"
                            for source in data["sources"][:3]
                        ])

                    # 构建增强prompt
                    enhanced_prompt = f"""基于以下参考资料回答用户的问题：

{context}

用户问题：{question}

请基于以上资料提供准确、专业的回答。如果资料中没有相关信息，请说明无法找到相关信息。"""

                    # 调用本地模型
                    messages = [HumanMessage(content=enhanced_prompt)]
                    return self.llm(messages)
                else:
                    # RAG失败，直接调用本地模型
                    messages = [HumanMessage(content=f"请回答以下问题：{question}")]
                    return self.llm(messages)

            except Exception as e:
                print(f"RAG API调用失败: {e}")
                # 降级到直接调用本地模型
                messages = [HumanMessage(content=f"请回答以下问题：{question}")]
                return self.llm(messages)

        return rag_retrieve_and_answer

    def chat(self, user_input: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """执行对话"""
        try:
            # 转换对话历史格式
            messages = []
            if conversation_history:
                for msg in conversation_history[-10:]:  # 只保留最近10条消息
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # 添加当前用户输入
            messages.append(HumanMessage(content=user_input))

            # 调用链
            if callable(self.qa_chain):
                # API-based chain
                response = self.qa_chain(user_input)
            else:
                # LangChain chain
                response = self.qa_chain.invoke(user_input)

            # 更新记忆
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response)

            return {
                "answer": response,
                "sources": [],  # TODO: 从RAG结果中提取来源
                "conversation_id": "default",
                "usage": {"tokens": len(response.split())}
            }

        except Exception as e:
            error_msg = f"对话处理失败: {str(e)}"
            print(error_msg)
            return {
                "answer": "抱歉，系统暂时无法处理您的请求。请稍后重试。",
                "sources": [],
                "conversation_id": "default",
                "error": error_msg,
                "usage": {"tokens": 0}
            }

    def generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成产业报告"""
        try:
            # 构建报告生成prompt
            industry = params.get("industry", "")
            scenario = params.get("scenario", "")
            objective = params.get("objective", "")

            report_prompt = f"""请基于{industry}行业，针对{scenario}场景，{objective}目标，生成一份完整的产业研究报告。

报告结构要求：
## 摘要

## 正文

## 结论

请确保内容专业、数据详实、分析深入。"""

            # 使用RAG增强的回答
            if callable(self.qa_chain):
                response = self.qa_chain(report_prompt)
            else:
                response = self.qa_chain.invoke(report_prompt)

            return {
                "success": True,
                "content": response,
                "metadata": {
                    "industry": industry,
                    "scenario": scenario,
                    "objective": objective,
                    "generated_at": "2024-12-29"
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "报告生成失败，请稍后重试。"
            }

# 全局实例
rag_system = None

def get_rag_system():
    """获取RAG系统实例"""
    global rag_system
    if rag_system is None:
        rag_system = EnhancedRAGSystem()
    return rag_system

if __name__ == "__main__":
    # 测试代码
    print("🧪 测试LangChain RAG系统...")

    system = get_rag_system()

    # 测试对话
    result = system.chat("中国数字经济的发展现状如何？")
    print("对话测试结果:")
    print(result["answer"][:200] + "...")

    # 测试报告生成
    report_params = {
        "industry": "人工智能",
        "scenario": "企业应用",
        "objective": "分析市场机会和投资建议"
    }

    report = system.generate_report(report_params)
    print(f"\n报告生成测试: {'成功' if report['success'] else '失败'}")
    if report["success"]:
        print("报告内容预览:")
        print(report["content"][:300] + "...")

    print("✅ LangChain RAG系统测试完成!")
