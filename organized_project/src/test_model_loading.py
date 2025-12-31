#!/usr/bin/env python3
"""
Test script to verify Qwen3-8B model loading and inference
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

def test_model_loading():
    model_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"
    lora_path = "/home/xzy/QWEN3-8B/QWEN3-8B/finetune_output/lora_full"

    print(f"🧠 Testing Qwen3-8B model loading...")
    print(f"Model path: {model_path}")
    print(f"LoRA path: {lora_path}")

    # Check CUDA availability
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"CUDA device name: {torch.cuda.get_device_name()}")

    try:
        print("\n1. Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        print("✅ Tokenizer loaded successfully!")

        print("\n2. Setting up quantization config...")
        # Use 8-bit quantization to reduce memory usage
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=False
        )

        print("\n3. Loading base model with quantization...")
        # For sharded safetensors, try different loading approaches
        try:
            # First try with explicit sharded loading
            base_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                trust_remote_code=True,
                local_files_only=True
            )
        except Exception as e:
            print(f"Standard loading failed: {e}")
            print("Trying with quantization disabled...")
            try:
                base_model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map={"": "cpu"},  # Load to CPU first
                    trust_remote_code=True,
                    local_files_only=True
                )
            except Exception as e2:
                print(f"CPU loading also failed: {e2}")
                print("Checking if model files are accessible...")
                import safetensors
                try:
                    # Try loading one shard to verify file integrity
                    shard_path = os.path.join(model_path, "model-00001-of-00005.safetensors")
                    print(f"Testing safetensors file: {shard_path}")
                    with safetensors.safe_open(shard_path, framework="pt", device="cpu") as f:
                        keys = list(f.keys())[:5]  # Just check first 5 keys
                        print(f"Successfully opened safetensors, found keys: {keys}")
                except Exception as e3:
                    print(f"Safetensors loading failed: {e3}")
                    raise e
        print("✅ Base model loaded successfully!")

        # Check if LoRA adapter exists
        if os.path.exists(lora_path):
            print(f"\n4. Loading LoRA adapter from {lora_path}...")
            try:
                model = PeftModel.from_pretrained(base_model, lora_path)
                print("✅ LoRA adapter loaded successfully!")
            except Exception as e:
                print(f"⚠️  LoRA loading failed: {e}")
                print("Using base model without LoRA adapter")
                model = base_model
        else:
            print(f"\n4. LoRA adapter not found at {lora_path}, using base model only")
            model = base_model

        print(f"\n5. Model loaded successfully!")
        print(f"Model type: {type(model)}")
        print(f"Model parameters: {model.num_parameters() if hasattr(model, 'num_parameters') else 'Unknown'}")

        # Test inference
        print("\n6. Testing inference...")
        test_prompt = "Hello, can you help me with a simple task?"

        inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Test prompt: {test_prompt}")
        print(f"Model response: {response}")
        print("✅ Inference test successful!")

        return True

    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_loading()
    exit(0 if success else 1)
