#!/usr/bin/env python3
"""
本地模型调用器 - 直接在Node.js后端中调用
避免HTTP开销，直接集成模型推理
"""

import sys
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import os
import time

class LocalModelCaller:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False

        # 模型路径
        self.base_model_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"
        self.lora_path = "/home/xzy/QWEN3-8B/QWEN3-8B/finetune_output/lora_full"

    def load_model(self):
        """加载模型（延迟加载，避免启动时占用内存）"""
        if self.is_loaded:
            return True

        try:
            print("正在加载Qwen3-8B模型...", file=sys.stderr)

            # 分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)

            # 量化配置
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )

            # 基础模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                torch_dtype=torch.bfloat16,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            # 尝试加载LoRA适配器
            if os.path.exists(self.lora_path):
                try:
                    from peft import PeftModel
                    self.model = PeftModel.from_pretrained(self.model, self.lora_path)
                    print("LoRA适配器加载成功", file=sys.stderr)
                except Exception as e:
                    print(f"LoRA加载失败，使用基础模型: {e}", file=sys.stderr)

            self.model.eval()
            self.is_loaded = True
            print("模型加载完成！", file=sys.stderr)
            return True

        except Exception as e:
            print(f"模型加载失败: {e}", file=sys.stderr)
            return False

    def generate_response(self, messages, max_tokens=1000, temperature=0.7):
        """生成AI回复"""
        if not self.is_loaded:
            if not self.load_model():
                return {"error": "模型加载失败"}

        try:
            start_time = time.time()

            # 构建对话模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 编码输入
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

            # 生成回复
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

            # 提取生成的文本
            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

            processing_time = time.time() - start_time

            return {
                "content": response,
                "processing_time": round(processing_time, 2),
                "model": "Qwen3-8B",
                "device": self.device
            }

        except Exception as e:
            return {"error": f"生成回复失败: {str(e)}"}

def main():
    """主函数，处理Node.js的调用"""
    try:
        # 从stdin读取输入
        input_data = json.loads(sys.stdin.read())

        # 提取参数
        action = input_data.get("action", "generate")
        messages = input_data.get("messages", [])
        max_tokens = input_data.get("max_tokens", 1000)
        temperature = input_data.get("temperature", 0.7)

        # 初始化模型调用器
        caller = LocalModelCaller()

        if action == "generate":
            result = caller.generate_response(messages, max_tokens, temperature)
            print(json.dumps(result, ensure_ascii=False))
        elif action == "health":
            # 健康检查
            loaded = caller.load_model() if not caller.is_loaded else True
            result = {
                "status": "healthy" if loaded else "error",
                "model_loaded": loaded,
                "device": caller.device,
                "cuda_available": torch.cuda.is_available()
            }
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(json.dumps({"error": f"未知操作: {action}"}, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": f"处理请求失败: {str(e)}"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
