#!/usr/bin/env python3
import subprocess, json, time, os, sys, math
from pathlib import Path

PROMPTS = [
    "请用中文简短介绍量子计算的主要应用场景：",
    "简述区块链在金融行业的典型应用与挑战：",
    "请总结云原生架构对中小企业的好处：",
    "解释联邦学习的基本原理和适用场景：",
    "概述自动驾驶中感知模块的主要技术点：",
    "请列出提升推荐系统质量的5个方法：",
    "简述大模型微调（Fine-tuning）的常见策略：",
    "说明元学习（meta-learning）在少样本学习中的作用：",
    "介绍半监督学习在工业应用中的案例：",
    "请写一段关于绿色计算的政策建议（中文）:"
]

OUT_PATH = Path("/home/xzy/QWEN3-8B/finetune/batch_generation_report.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def run_generate(prompt, max_new_tokens=128, diag=False):
    py = "/home/xzy/anaconda3/envs/XZY/bin/python"
    cmd = [py, str(Path(__file__).resolve().parent / "local_generate.py"),
           "--prompt", prompt, "--max_new_tokens", str(max_new_tokens)]
    if diag:
        cmd.append("--diag")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def repetition_rate(text):
    toks = text.split()
    if not toks: return 0.0
    return 1.0 - (len(set(toks)) / len(toks))

def main():
    results = []
    for p in PROMPTS:
        t0 = time.time()
        rc, out, err = run_generate(p, max_new_tokens=128, diag=False)
        dt = time.time() - t0
        if rc != 0:
            results.append({"prompt": p, "error": err, "rc": rc, "time": dt})
            continue
        length = len(out)
        rep = repetition_rate(out)
        results.append({"prompt": p, "output": out, "length": length, "repetition_rate": rep, "time_s": round(dt,3)})
        print(f"Done prompt (len={length}, rep={rep:.3f})")

    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for item in results:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    print("Wrote report to", OUT_PATH)

if __name__ == "__main__":
    main()


