#!/usr/bin/env python3
"""
Download and test Qwen model directly
"""

import os
from transformers import AutoTokenizer, AutoModelForCausalLM

def download_and_test_model():
    model_name = "Qwen/Qwen2-7B-Instruct"
    local_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"

    print(f"Downloading {model_name} to {local_path}")

    try:
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        tokenizer.save_pretrained(local_path)
        print("✅ Tokenizer downloaded and saved")

        print("Downloading model (this may take a while)...")
        # Use smaller model for testing first
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True
        )

        model.save_pretrained(local_path)
        print("✅ Model downloaded and saved")

        # Test inference
        print("Testing inference...")
        test_text = "Hello, can you help me?"

        inputs = tokenizer(test_text, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_length=50, do_sample=True)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        print(f"Input: {test_text}")
        print(f"Output: {response}")
        print("✅ Model working correctly!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    download_and_test_model()
