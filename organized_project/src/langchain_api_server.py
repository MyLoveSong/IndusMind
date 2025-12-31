#!/usr/bin/env python
"""
LangChain API服务：提供HTTP接口供后端调用
整合微调模型 + RAG + LangChain的完整流程
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from langchain_service import get_rag_system

app = FastAPI(title="LangChain RAG API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局RAG系统实例
rag_system = None

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    """对话响应"""
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    usage: Dict[str, int]
    error: Optional[str] = None

class ReportRequest(BaseModel):
    """报告生成请求"""
    industry: str
    scenario: str
    objective: str
    data_sources: Optional[List[str]] = None
    outline: Optional[List[Dict[str, Any]]] = None

class ReportResponse(BaseModel):
    """报告生成响应"""
    success: bool
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化RAG系统"""
    global rag_system
    try:
        print("🚀 初始化LangChain RAG系统...")
        rag_system = get_rag_system()
        print("✅ LangChain RAG系统初始化成功")
    except Exception as e:
        print(f"❌ LangChain RAG系统初始化失败: {e}")
        raise

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG系统未初始化")

        result = rag_system.chat(
            user_input=request.message,
            conversation_history=request.conversation_history
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")

@app.post("/generate_report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """报告生成接口"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG系统未初始化")

        result = rag_system.generate_report({
            "industry": request.industry,
            "scenario": request.scenario,
            "objective": request.objective,
            "data_sources": request.data_sources,
            "outline": request.outline
        })

        return ReportResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "langchain": "active" if rag_system else "inactive",
            "rag": "active",
            "local_model": "active"
        }
    }

@app.get("/test")
async def test_endpoint():
    """测试端点"""
    try:
        if not rag_system:
            return {"error": "RAG系统未初始化"}

        # 简单测试
        result = rag_system.chat("你好，请介绍一下自己。")
        return {
            "test_result": "success",
            "response_preview": result["answer"][:100] + "...",
            "system_status": "ready"
        }

    except Exception as e:
        return {
            "test_result": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "langchain_api_server:app",
        host="0.0.0.0",
        port=8003,
        reload=False
    )
