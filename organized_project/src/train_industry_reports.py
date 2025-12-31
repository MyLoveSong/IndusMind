#!/usr/bin/env python3
"""
产业报告生成专项微调训练脚本
针对QWEN3-8B模型进行产业报告生成能力的专项训练
"""

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer, 
    DataCollatorForLanguageModeling
)
from peft import get_peft_model, LoraConfig, TaskType
from transformers import TrainerCallback

def load_industry_reports_data(data_path):
    """加载产业报告训练数据"""
    data = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line.strip())
                data.append(item)
    
    return data

def format_instruction_sample(sample):
    """格式化指令微调样本"""
    instruction = sample['instruction']
    input_text = sample.get('input', '')
    output = sample['output']
    
    if input_text:
        prompt = f"指令：{instruction}\n输入：{input_text}\n输出："
    else:
        prompt = f"指令：{instruction}\n输出："
    
    # 构建完整的对话格式
    full_prompt = f"<|im_start|>system\n你是一个专业的产业研究员，负责生成高质量的产业研究报告结构和大纲。请严格按照JSON格式输出。\n<|im_end|>\n<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n{output}\n<|im_end|>"
    
    return {"text": full_prompt}

def main():
    # 配置路径
    model_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"
    data_path = "/home/xzy/QWEN3-8B/data/industry_reports/train_data.jsonl"
    output_dir = "/home/xzy/QWEN3-8B/QWEN3-8B/finetune_output/industry_reports_lora"
    
    print("🚀 开始产业报告生成专项训练...")
    print(f"📂 模型路径: {model_path}")
    print(f"📄 数据路径: {data_path}")
    print(f"💾 输出路径: {output_dir}")
    
    # 1. 加载数据
    print("\n📚 加载训练数据...")
    raw_data = load_industry_reports_data(data_path)
    print(f"✅ 加载了 {len(raw_data)} 条训练样本")
    
    # 转换为Dataset格式
    dataset = Dataset.from_list(raw_data)
    print(f"📊 数据集大小: {len(dataset)}")
    
    # 2. 格式化数据
    print("\n🔧 格式化训练样本...")
    formatted_dataset = dataset.map(format_instruction_sample)
    print("✅ 数据格式化完成")
    
    # 3. 加载tokenizer
    print("\n🔤 加载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        padding_side="left"
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("✅ Tokenizer加载完成")
    
    # 4. 数据分词
    print("\n✂️ 对数据进行分词...")
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=2048,
            padding="max_length"
        )
    
    tokenized_dataset = formatted_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text", "instruction", "input", "output"]
    )
    print("✅ 数据分词完成")
    
    # 5. 加载模型
    print("\n🤖 加载基础模型...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=None,  # 训练时不使用量化
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    print("✅ 基础模型加载完成")
    
    # 6. 配置LoRA
    print("\n🎯 配置LoRA参数...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,  # LoRA rank
        lora_alpha=32,  # LoRA alpha
        lora_dropout=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("✅ LoRA配置完成")
    
    # 7. 配置训练参数
    print("\n⚙️ 配置训练参数...")
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_steps=100,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        eval_strategy="no",
        fp16=True,
        dataloader_num_workers=2,
        remove_unused_columns=False,
        label_names=["input_ids", "attention_mask"],
    )
    
    # 8. 创建Trainer
    print("\n🎓 初始化训练器...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        callbacks=[
            # 自定义回调：显示训练进度
            TrainerCallback()
        ]
    )
    
    # 9. 开始训练
    print("\n🏃 开始训练...")
    print("=" * 60)
    
    trainer.train()
    
    # 10. 保存模型
    print("\n💾 保存训练好的模型...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    print("\n🎉 产业报告生成专项训练完成!")
    print("=" * 60)
    print("📊 训练总结:")
    print(f"   • 训练轮数: {training_args.num_train_epochs}")
    print(f"   • 训练样本: {len(raw_data)}")
    print(f"   • LoRA rank: {lora_config.r}")
    print(f"   • 输出路径: {output_dir}")
    print("\n🚀 现在可以使用训练好的模型进行产业报告生成了!")

if __name__ == "__main__":
    main()
