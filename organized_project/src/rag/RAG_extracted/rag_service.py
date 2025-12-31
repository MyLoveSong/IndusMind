#!/usr/bin/env python
"""
RAG系统服务（高性能GPU优化版）：结合Qwen-8B和FAISS向量检索
针对4×RTX 4090环境优化，包含重排序、多GPU支持、高级prompt工程
"""
import json
import numpy as np
import faiss
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
try:
    from .hybrid_retriever import HybridRetriever
except Exception:
    # allow running as script where relative import may fail
    from hybrid_retriever import HybridRetriever
try:
    from cross_encoder import CrossEncoder
    RERANKER_AVAILABLE = True
except Exception:
    try:
        from sentence_transformers.cross_encoder import CrossEncoder  # type: ignore
        RERANKER_AVAILABLE = True
    except Exception:
        RERANKER_AVAILABLE = False
        print("警告: cross-encoder 未安装，且 sentence-transformers 中的 CrossEncoder 不可用，将跳过重排序功能")

class RAGSystem:
    def __init__(self, model_path, index_path, metadata_path, 
                 encoder_model="BAAI/bge-large-zh-v1.5",
                 use_gpu=True, use_reranker=True, max_memory_per_gpu="20GiB"):
        """初始化RAG系统（高性能GPU优化版）
        
        Args:
            model_path: Qwen-8B模型路径
            index_path: FAISS索引文件所在目录
            metadata_path: metadata.json文件所在目录
            encoder_model: 查询向量化模型
            use_gpu: 是否使用GPU加速FAISS
            use_reranker: 是否启用重排序
            max_memory_per_gpu: 每张GPU最大显存使用
        """
        print(f"检测到 {torch.cuda.device_count()} 张GPU")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        
        print("\n初始化检索器（FAISS + 词汇回退）...")
        # HybridRetriever负责加载FAISS索引与metadata，并在可用时使用sentence-transformers进行编码
        self.retriever = HybridRetriever(index_path, metadata_path, encoder_model=encoder_model)

        print("加载Qwen-8B模型（多GPU自动分配）...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
        # 多GPU配置
        max_memory = {i: max_memory_per_gpu for i in range(torch.cuda.device_count())} if torch.cuda.is_available() else None
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,  # 使用BFloat16获得更好精度
            device_map="auto",
            max_memory=max_memory,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # expose index and metadata for compatibility
        try:
            self.index = getattr(self.retriever, "index", None)
            self.metadata = getattr(self.retriever, "metadata", {})
        except Exception:
            self.index = None
            self.metadata = {}
        
        # 初始化重排序器
        self.use_reranker = use_reranker and RERANKER_AVAILABLE
        if self.use_reranker:
            print("加载重排序模型...")
            self.reranker = CrossEncoder('BAAI/bge-reranker-large', device=device)
        else:
            self.reranker = None
        
        print("\n✅ RAG系统初始化完成！")
        print(f"  - 模型: Qwen-8B (分布在 {len(set(str(v.device) for v in self.model.state_dict().values()))} 个设备)")
        print(f"  - 向量化: {encoder_model}")
        print(f"  - FAISS: {'GPU加速' if use_gpu and torch.cuda.is_available() else 'CPU'}")
        print(f"  - 重排序: {'启用' if self.use_reranker else '禁用'}")
    
    def encode_query(self, query_text):
        """将查询文本转换为向量（使用HybridRetriever）"""
        return self.retriever.encode_query(query_text)
    
    def search(self, query_vector, k=5, rerank_k=None):
        """向量检索（支持重排序）
        
        Args:
            query_vector: 查询向量（1024维）
            k: 初始检索数量（如果启用重排序，会先检索更多）
            rerank_k: 重排序后返回的数量（None表示不重排序）
            
        Returns:
            List[Dict]: 检索结果列表，每个结果包含text, file_name, page, score
        """
        # If hybrid retriever available, use it
        try:
            # hybrid_search returns top-k combined candidates
            combined = self.retriever.hybrid_search(query_text, k=k if not self.use_reranker else max(k, (rerank_k or k) * 2))
            # map to expected format
            results = []
            for item in combined:
                idx = item["idx"]
                chunk_info = self.metadata.get('chunks', [])[idx]
                results.append({
                    'text': chunk_info['text'],
                    'file_name': chunk_info.get('file_name', ''),
                    'page': chunk_info.get('page', -1),
                    'chunk_index': chunk_info.get('chunk_index', idx),
                    'score': float(item.get('score', 0.0))
                })
            if self.use_reranker and rerank_k and len(results) > rerank_k:
                return self._rerank(results, rerank_k)
            return results[:k]
        except Exception:
            # fallback to previous behavior if retriever fails
            return []
    
    def _rerank(self, chunks, top_k):
        """使用交叉编码器重排序"""
        query_text = getattr(self, '_last_query', '')
        # If cross-encoder is available, use it
        if self.reranker:
            pairs = [[query_text, chunk['text']] for chunk in chunks]
            scores = self.reranker.predict(pairs)
            reranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
            results = []
            for chunk, new_score in reranked[:top_k]:
                chunk['rerank_score'] = float(new_score)
                chunk['original_score'] = chunk['score']
                results.append(chunk)
            return results

        # Fallback: use retriever to encode query and chunk texts, compute cosine similarity
        try:
            chunk_texts = [c['text'] for c in chunks]
            embeddings = self.retriever.encode_texts([query_text] + chunk_texts)
            q_emb = embeddings[0].reshape(1, -1)
            doc_embs = embeddings[1:]
            from sklearn.metrics.pairwise import cosine_similarity
            sims = cosine_similarity(q_emb, doc_embs)[0]
            scored = []
            for i, c in enumerate(chunks):
                scored.append((c, float(sims[i])))
            scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
            results = []
            for chunk, score in scored_sorted[:top_k]:
                chunk['rerank_score'] = score
                chunk['original_score'] = chunk['score']
                results.append(chunk)
            return results
        except Exception:
            # If reranking fails, return original top-k
            return chunks[:top_k]
    
    def generate(self, query, context_chunks, max_length=2048, temperature=0.3, 
                 top_p=0.9, repetition_penalty=1.1, deterministic: bool = False, max_new_tokens: int = None):
        """基于检索结果生成回答（优化版prompt工程）
        
        Args:
            query: 用户查询
            context_chunks: 检索到的相关chunks
            max_length: 最大生成长度（增加到2048支持更长回答）
            temperature: 生成温度（0.3适合事实性回答）
            top_p: nucleus sampling参数
            repetition_penalty: 重复惩罚系数
            
        Returns:
            str: 生成的回答
        """
        # 智能组织上下文：按文档分组，添加引用标记
        context_parts = []
        doc_groups = {}
        
        for i, chunk in enumerate(context_chunks, 1):
            doc_name = chunk['file_name']
            if doc_name not in doc_groups:
                doc_groups[doc_name] = []
            doc_groups[doc_name].append((i, chunk))
        
        # 按文档组织上下文
        doc_idx = 1
        for doc_name, chunks in doc_groups.items():
            doc_text = f"\n【来源{doc_idx}】{doc_name}\n"
            for ref_num, chunk in chunks:
                # short-term: truncate long chunks to 500 chars to avoid overly long prompts
                chunk_preview = (chunk.get('text', '') or "")[:500]
                doc_text += f"[引用{ref_num}] {chunk_preview}\n"
            context_parts.append(doc_text)
            doc_idx += 1
        
        context = "\n".join(context_parts)
        
        # 简短 prompt 模板以减少长度并提高生成可靠性
        prompt = f"""你是专业分析师。请基于下列上下文回答用户问题，回答要基于上下文并标注引用来源。

上下文：
{context}

问题：
{query}

回答："""
        
        # 生成回答
        inputs = self.tokenizer(prompt, return_tensors="pt")
        # 自动处理设备分配（多GPU环境）
        try:
            # 尝试获取模型设备
            if hasattr(self.model, 'device'):
                device = self.model.device
            else:
                # 如果模型分布在多GPU，找到第一个参数所在的设备
                first_param = next(iter(self.model.parameters()))
                device = first_param.device
            inputs = {k: v.to(device) for k, v in inputs.items()}
        except:
            # 如果无法确定设备，使用默认CUDA设备
            device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            # compute max_new_tokens explicitly to avoid confusion with max_length
            input_len = inputs["input_ids"].shape[1]
            max_new_tokens = max_length - input_len if max_length > input_len else max_length
            gen_kwargs = dict(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=(temperature > 0 and not deterministic),
                repetition_penalty=repetition_penalty,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1
            )
            if deterministic:
                # prefer beam search for deterministic output when requested
                gen_kwargs.update({"num_beams": 5, "do_sample": False})
            if max_new_tokens is not None:
                # override max_new_tokens explicitly
                gen_kwargs["max_new_tokens"] = int(max_new_tokens)
            outputs = self.model.generate(**gen_kwargs)

        # Prefer decoding only the newly generated tokens (safer than splitting on markers)
        try:
            generated_ids = outputs[0][input_len:]
            if generated_ids.numel() == 0:
                # fallback to full decode
                answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            else:
                answer = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        except Exception:
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # If the model included explicit "## 回答：" or "回答：" markers, trim them
        if "## 回答：" in answer:
            answer = answer.split("## 回答：")[-1].strip()
        elif "回答：" in answer:
            answer = answer.split("回答：")[-1].strip()

        return answer
    
    def query(self, query_text, k=5, rerank_k=None, max_length=2048, 
              temperature=0.3, top_p=0.9, repetition_penalty=1.1, deterministic: bool = False, max_new_tokens: int = None):
        """完整的RAG查询流程（高性能优化版）
        
        Args:
            query_text: 用户查询文本
            k: 最终使用的chunk数量（如果启用重排序，会先检索更多）
            rerank_k: 重排序后返回的数量（None表示不重排序，直接使用k）
            max_length: 最大生成长度（增加到2048）
            temperature: 生成温度（0.3适合事实性回答）
            top_p: nucleus sampling参数
            repetition_penalty: 重复惩罚系数
            
        Returns:
            Dict: 包含answer和sources的字典
        """
        # 保存查询文本用于重排序
        self._last_query = query_text
        
        # 1. 向量化查询
        query_vector = self.encode_query(query_text)
        
        # 2. 检索相关chunks（如果启用重排序，会先检索更多）
        if rerank_k is None:
            rerank_k = k
        chunks = self.search(query_vector, k=k if not self.use_reranker else rerank_k*2, rerank_k=rerank_k)
        
        # 3. 生成回答
        answer = self.generate(query_text, chunks, max_length, temperature, top_p, repetition_penalty, deterministic=deterministic, max_new_tokens=max_new_tokens)
        
        return {
            'answer': answer,
            'sources': chunks,
            'query': query_text,
            'num_sources': len(chunks),
            'reranked': self.use_reranker and rerank_k is not None
        }


def main():
    """测试示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG系统测试')
    parser.add_argument('--model_path', type=str, required=True, help='Qwen-8B模型路径')
    parser.add_argument('--index_path', type=str, default='./dataset-vector', help='FAISS索引路径')
    parser.add_argument('--metadata_path', type=str, default='./dataset-vector', help='元数据路径')
    parser.add_argument('--query', type=str, help='测试查询')
    parser.add_argument('--k', type=int, default=5, help='检索chunk数量')
    parser.add_argument('--rerank_k', type=int, default=None, help='重排序后返回数量（启用重排序）')
    parser.add_argument('--max_length', type=int, default=2048, help='最大生成长度')
    parser.add_argument('--temperature', type=float, default=0.3, help='生成温度')
    parser.add_argument('--no-reranker', action='store_true', help='禁用重排序')
    parser.add_argument('--no-gpu-faiss', action='store_true', help='禁用FAISS GPU加速')
    
    args = parser.parse_args()
    
    # 初始化RAG系统
    print("初始化RAG系统（高性能GPU优化版）...")
    rag = RAGSystem(
        model_path=args.model_path,
        index_path=args.index_path,
        metadata_path=args.metadata_path,
        use_gpu=not args.no_gpu_faiss,
        use_reranker=not args.no_reranker
    )
    
    # 测试查询
    if args.query:
        result = rag.query(
            args.query, 
            k=args.k, 
            rerank_k=args.rerank_k,
            max_length=args.max_length,
            temperature=args.temperature
        )
        print("\n" + "="*80)
        print(f"问题：{result['query']}")
        print("="*80)
        print(f"\n回答：\n{result['answer']}")
        print("\n" + "="*80)
        print(f"参考来源（{result['num_sources']}个，{'已重排序' if result['reranked'] else '未重排序'}）：")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n[{i}] {source['file_name']} (第{source['page']}页)")
            if 'rerank_score' in source:
                print(f"    重排序分数: {source['rerank_score']:.4f} | 原始分数: {source['original_score']:.4f}")
            else:
                print(f"    相似度分数: {source['score']:.4f}")
            print(f"    内容预览: {source['text'][:150]}...")
    else:
        # 交互式查询
        print("\n" + "="*80)
        print("RAG系统已就绪（高性能GPU优化版）")
        print("输入查询（输入'quit'退出，输入'settings'查看/修改参数）：")
        print("="*80)
        
        current_k = args.k
        current_rerank_k = args.rerank_k
        current_temp = args.temperature
        
        while True:
            query = input("\n> ")
            if query.lower() in ['quit', 'exit', '退出']:
                break
            elif query.lower() == 'settings':
                print(f"\n当前参数：")
                print(f"  k={current_k}, rerank_k={current_rerank_k}, temperature={current_temp}")
                print("输入 'k=10' 或 'temp=0.5' 修改参数")
                continue
            elif '=' in query:
                # 参数设置
                try:
                    if query.startswith('k='):
                        current_k = int(query.split('=')[1])
                        print(f"已设置 k={current_k}")
                    elif query.startswith('temp='):
                        current_temp = float(query.split('=')[1])
                        print(f"已设置 temperature={current_temp}")
                    elif query.startswith('rerank_k='):
                        current_rerank_k = int(query.split('=')[1])
                        print(f"已设置 rerank_k={current_rerank_k}")
                    continue
                except:
                    print("参数格式错误，请使用 k=10 或 temp=0.5 格式")
                    continue
            
            result = rag.query(
                query, 
                k=current_k, 
                rerank_k=current_rerank_k,
                temperature=current_temp
            )
            print(f"\n{'='*80}")
            print(f"回答：\n{result['answer']}")
            print(f"\n参考来源：{result['num_sources']}个相关文档")
            if result['reranked']:
                print("（已使用重排序优化检索结果）")


if __name__ == "__main__":
    main()

