#!/usr/bin/env python3
"""
Test script to verify tokenizer loading
"""

import os
from transformers import AutoTokenizer

def test_tokenizer():
    model_path = "/home/xzy/QWEN3-8B/models/pretrained/Qwen3-8B"

    print(f"Testing tokenizer loading from: {model_path}")
    print("Files in directory:")
    for file in os.listdir(model_path):
        print(f"  {file}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        print("✅ Tokenizer loaded successfully!")

        # Test tokenization
        test_text = "Hello, this is a test message."
        tokens = tokenizer.tokenize(test_text)
        print(f"Test text: {test_text}")
        print(f"Tokens: {tokens}")

        # Test encoding/decoding
        encoded = tokenizer.encode(test_text)
        decoded = tokenizer.decode(encoded)
        print(f"Encoded: {encoded}")
        print(f"Decoded: {decoded}")

        return True

    except Exception as e:
        print(f"❌ Tokenizer loading failed: {e}")
        return False

if __name__ == "__main__":
    test_tokenizer()
