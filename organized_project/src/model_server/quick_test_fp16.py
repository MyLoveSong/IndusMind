from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

MODEL_PATH = '/home/xzy/QWEN3-8B/models/Qwen/Qwen3-8B'

def main():
    print('Using model path:', MODEL_PATH)
    print('torch version:', torch.__version__)
    print('cuda available:', torch.cuda.is_available())
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map='auto',
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model.eval()

    prompt = "Hello, world"
    inputs = tokenizer(prompt, return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=32)
    print(tokenizer.decode(out[0], skip_special_tokens=True))

if __name__ == '__main__':
    main()


