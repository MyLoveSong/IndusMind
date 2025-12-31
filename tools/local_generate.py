#!/usr/bin/env python3
import argparse
import sys
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--diag", action="store_true", help="print diagnostics (timing, token ids, topk logits)")
    p.add_argument("--topk", type=int, default=5, help="top-k logits to show for final step")
    p.add_argument("--prompt", type=str, required=True)
    p.add_argument("--max_new_tokens", type=int, default=128)
    p.add_argument("--model_path", type=str, default="/home/xzy/QWEN3-8B/models/Qwen/Qwen3-8B")
    args = p.parse_args()

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except Exception as e:
        print(f"ERROR: missing transformers or torch: {e}", file=sys.stderr)
        sys.exit(2)

    prompt = args.prompt
    model_path = args.model_path

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, device_map="auto", torch_dtype=torch.bfloat16)
        device = next(model.parameters()).device
        import time
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        start = time.time()
        if args.diag:
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False, num_beams=1, return_dict_in_generate=True, output_scores=True)
        else:
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False, num_beams=1)
        elapsed = time.time() - start
        # obtain text
        if args.diag:
            generated_ids = out.sequences[0]
            text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        else:
            text = tokenizer.decode(out[0], skip_special_tokens=True)
        # print only generated portion if possible
        if text.startswith(prompt):
            generated = text[len(prompt):].strip()
        else:
            generated = text.strip()
        if args.diag:
            print("=== DIAGNOSTICS ===")
            print("time(s):", round(elapsed,3))
            print("input_ids:", inputs["input_ids"][0].tolist())
            print("generated_ids:", generated_ids.tolist())
            # show topk logits for final step if available
            if hasattr(out, "scores") and out.scores:
                import torch
                final_scores = out.scores[-1]  # logits for final generation step
                probs = torch.softmax(final_scores, dim=-1)[0]
                topk = torch.topk(probs, k=min(len(probs), args.topk))
                print("topk tokens:", topk.indices.tolist())
                print("topk probs:", [round(float(x),6) for x in topk.values.tolist()])
        print(generated)
    except Exception as e:
        print(f"ERROR: generation failed: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()


