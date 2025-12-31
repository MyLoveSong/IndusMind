#!/usr/bin/env python
"""
RAG系统FastAPI服务（高性能GPU优化版）
提供HTTP API接口供前端调用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from rag_service import RAGSystem
import argparse

app = FastAPI(title="智研通RAG系统API", version="1.0.0")

# CORS配置（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局RAG系统实例
rag_system: Optional[RAGSystem] = None


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    k: int = 5
    rerank_k: Optional[int] = None
    max_length: int = 2048
    temperature: float = 0.3
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    deterministic: bool = False


class QueryResponse(BaseModel):
    """查询响应模型"""
    answer: str
    sources: List[dict]
    query: str
    num_sources: int
    reranked: bool


@app.on_event("startup")
async def startup_event():
    """服务启动时初始化RAG系统"""
    global rag_system
    if rag_system is None:
        import os
        model_path = os.getenv("QWEN_MODEL_PATH", "/path/to/qwen-8b")
        index_path = os.getenv("FAISS_INDEX_PATH", "./dataset-vector")
        metadata_path = os.getenv("METADATA_PATH", "./dataset-vector")
        
        print("正在初始化RAG系统...")
        rag_system = RAGSystem(
            model_path=model_path,
            index_path=index_path,
            metadata_path=metadata_path,
            use_gpu=True,
            use_reranker=True
        )
        print("RAG系统初始化完成！")


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "service": "智研通RAG系统API",
        "version": "1.0.0",
        "status": "running",
        "gpu_count": rag_system.model.get_memory_footprint() if rag_system else 0
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "rag_system_loaded": rag_system is not None}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """RAG查询接口
    
    Args:
        request: 查询请求，包含查询文本和参数
        
    Returns:
        QueryResponse: 包含回答和来源的响应
    """
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    try:
        result = rag_system.query(
            query_text=request.query,
            k=request.k,
            rerank_k=request.rerank_k,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            repetition_penalty=request.repetition_penalty,
            deterministic=getattr(request, "deterministic", False)
        )
        
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")


@app.post("/batch_query")
async def batch_query(queries: List[str], k: int = 5):
    """批量查询接口（充分利用GPU并行处理）
    
    Args:
        queries: 查询文本列表
        k: 每个查询返回的chunk数量
        
    Returns:
        List[QueryResponse]: 批量查询结果
    """
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    results = []
    for query_text in queries:
        try:
            result = rag_system.query(query_text, k=k)
            results.append(QueryResponse(**result))
        except Exception as e:
            results.append({
                "error": str(e),
                "query": query_text
            })
    
    return results


@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    import torch
    
    stats = {
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "gpu_info": []
    }
    
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            stats["gpu_info"].append({
                "device_id": i,
                "name": torch.cuda.get_device_name(i),
                "memory_allocated": f"{torch.cuda.memory_allocated(i) / 1024**3:.2f} GB",
                "memory_reserved": f"{torch.cuda.memory_reserved(i) / 1024**3:.2f} GB"
            })
    
    stats["index_size"] = rag_system.index.ntotal if hasattr(rag_system, 'index') else 0
    stats["reranker_enabled"] = rag_system.use_reranker if rag_system else False
    
    return stats


def main():
    """启动API服务"""
    parser = argparse.ArgumentParser(description='RAG系统FastAPI服务')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务地址')
    parser.add_argument('--port', type=int, default=8000, help='服务端口')
    parser.add_argument('--model_path', type=str, required=True, help='Qwen-8B模型路径')
    parser.add_argument('--index_path', type=str, default='./dataset-vector', help='FAISS索引路径')
    parser.add_argument('--metadata_path', type=str, default='./dataset-vector', help='元数据路径')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数（GPU服务建议为1）')
    
    args = parser.parse_args()
    
    # 设置环境变量
    import os
    os.environ["QWEN_MODEL_PATH"] = args.model_path
    os.environ["FAISS_INDEX_PATH"] = args.index_path
    os.environ["METADATA_PATH"] = args.metadata_path
    
    # 启动服务
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()

