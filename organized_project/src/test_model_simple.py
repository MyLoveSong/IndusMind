#!/usr/bin/env python3
"""
Simple test to verify Qwen3-8B model inference works
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def test_model_simple():
    model_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"

    print("🧠 Testing Qwen3-8B model inference...")

    try:
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

        print("Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16
        )

        print("Testing inference...")
        prompt = "你好，请介绍一下你自己。"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=100,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"✅ Model inference successful!")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_simple()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
