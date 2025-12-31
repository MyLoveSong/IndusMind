from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch
import os

adapter_dir = "/home/xzy/QWEN3-8B/finetune_output/lora_dryrun"
base_model = "/home/xzy/QWEN3-8B/models/Qwen/Qwen3-8B"
out_file = "/home/xzy/QWEN3-8B/finetune_output/eval_outputs.txt"

def main():
    print("Loading base model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(base_model, device_map="auto", torch_dtype=torch.bfloat16, trust_remote_code=True, low_cpu_mem_usage=True)

    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, adapter_dir)
    model.eval()

    prompts = [
        "请简要说明中国数字经济在2023年的主要发展趋势。",
        "请基于提供的白皮书摘要，总结三点关键结论。"
    ]

    with open(out_file, "w", encoding="utf-8") as wf:
        for p in prompts:
            inputs = tokenizer(p, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=128)
            text = tokenizer.decode(out[0], skip_special_tokens=True)
            wf.write(f"PROMPT: {p}\n\nRESPONSE:\n{text}\n\n{'='*60}\n")
            print("Generated for prompt:", p)

    print("Saved outputs to", out_file)

if __name__ == "__main__":
    main()


