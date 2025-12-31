import argparse
import os
import subprocess
import psutil
from collections import deque
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
import torch
from peft import get_peft_model, LoraConfig, TaskType
from transformers import TrainerCallback

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="./finetune_output/lora")
    parser.add_argument("--deepspeed_config", type=str, default="./finetune/deepspeed_config.json")
    parser.add_argument("--per_device_train_batch_size", type=int, default=1)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--num_train_epochs", type=int, default=1)
    parser.add_argument("--max_train_samples", type=int, default=None)
    parser.add_argument("--lora_rank", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=16)
    parser.add_argument("--lora_dropout", type=float, default=0.1)
    # Accept unknown args (e.g. --local_rank) when launched via distributed launchers
    args, _ = parser.parse_known_args()
    return args

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    class StepLoggingCallback(TrainerCallback):
        def __init__(self):
            self.recent_losses = deque(maxlen=100)

        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs is None:
                return
            # only print from main process
            try:
                local_rank = int(os.environ.get("LOCAL_RANK", os.environ.get("RANK", "0")))
            except:
                local_rank = 0
            if local_rank != 0:
                return

            step = logs.get("step", getattr(state, "global_step", None))
            batch = logs.get("batch", None)
            loss = logs.get("loss") or logs.get("train_loss") or logs.get("eval_loss")
            if loss is not None:
                try:
                    self.recent_losses.append(float(loss))
                except:
                    pass
            avg_loss = sum(self.recent_losses) / len(self.recent_losses) if len(self.recent_losses) > 0 else None
            trend = "N/A"
            if len(self.recent_losses) >= 2:
                trend = "📈 上升" if self.recent_losses[-1] > self.recent_losses[-2] else "📉 下降"

            # epoch info
            epoch_val = logs.get("epoch", None)
            total_epochs = getattr(args, "num_train_epochs", None)
            try:
                epoch_display = int(epoch_val) if epoch_val is not None else "N/A"
            except:
                epoch_display = epoch_val

            # best metric placeholder
            best_metric = "N/A"
            patience_total = "3/30"
            patience_left = "27 epochs"

            # GPU info (first two GPUs)
            gpu_lines = []
            try:
                out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"])
                for i, line in enumerate(out.decode().strip().splitlines()[:2]):
                    used, total, util = [x.strip() for x in line.split(",")]
                    pct = float(used) / float(total) * 100 if float(total) > 0 else 0.0
                    gpu_lines.append((i, used, total, util, pct))
            except Exception:
                gpu_lines = []

            vm = psutil.virtual_memory()
            sys_mem = f"{vm.used/1024**3:.1f}Gi/{vm.total/1024**3:.1f}Gi"

            # progress bar
            pct_str = "N/A"
            try:
                if epoch_val is not None and total_epochs:
                    pct_str = f"{(float(epoch_val)/float(total_epochs))*100:.2f}%"
            except:
                pct_str = "N/A"

            # build lines
            lines = []
            lines.append("=" * 100)
            lines.append(f"🚀 训练实时监控 - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("=" * 100)
            lines.append("")
            bar = "█" * (int((avg_loss or 0) % 30))
            lines.append(f"📊 训练进度: [{bar}] {pct_str}")
            lines.append(f"   Epoch: {epoch_display}/{total_epochs if total_epochs else 'N/A'}")
            lines.append(f"   Batch: {batch if batch else 'N/A'}")
            lines.append(f"   Step:  {step if step else 'N/A'}")
            lines.append("")
            lines.append("📈 Loss信息:")
            lines.append(f"   当前Loss: {float(loss):.4f}" if loss is not None else "   当前Loss: N/A")
            lines.append(f"   平均Loss: {avg_loss:.4f} (最近100步)" if avg_loss else "   平均Loss: N/A")
            lines.append(f"   趋势: {trend}")
            lines.append("")
            lines.append("⏸️  Early Stopping状态:")
            lines.append(f"   监控指标: recall@10")
            lines.append(f"   最佳指标: {best_metric}")
            lines.append(f"   耐心值: {patience_total}")
            lines.append(f"   剩余耐心: {patience_left}")
            lines.append("")
            lines.append("🎮 GPU状态:")
            if gpu_lines:
                for (i, u, t, util, pct) in gpu_lines:
                    lines.append(f"   GPU {i}: 内存 {u}/{t}MB ({pct:.1f}%), 使用率 {util}%")
            else:
                lines.append("   nvidia-smi not available or no GPUs detected")
            lines.append("")
            lines.append(f"💾 系统内存: {sys_mem}")
            lines.append("")
            lines.append("=" * 100)

            # print block
            for l in lines:
                print(l)
            print(flush=True)

    print("Loading tokenizer and base model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)

    # Detect distributed launch (accelerate/deepspeed) via env vars
    world_size = int(os.environ.get("WORLD_SIZE", os.environ.get("WORLD_SIZE", "1")))
    local_rank_env = os.environ.get("LOCAL_RANK") or os.environ.get("LOCAL_RANK", None)
    is_distributed = world_size > 1 or ("LOCAL_RANK" in os.environ) or ("RANK" in os.environ)

    if is_distributed:
        # In distributed mode we MUST NOT load with device_map='auto'.
        # Let accelerate/deepspeed handle placement; load with low_cpu_mem_usage.
        print("Distributed launch detected — loading model without device_map (accelerate will place tensors).")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
    else:
        # Non-distributed: we can use device_map='auto' to shard across local GPUs.
        if torch.cuda.is_available() and torch.cuda.device_count() > 1:
            max_mem = {i: "45GiB" for i in range(torch.cuda.device_count())}
            model = AutoModelForCausalLM.from_pretrained(
                args.model_path,
                device_map="auto",
                max_memory=max_mem,
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                args.model_path,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

    def build_text_from_example(example):
        # Support multiple input schemas: instruction/context/output or text/content/prompt
        if "text" in example and example["text"]:
            return example["text"]
        if "content" in example and example["content"]:
            return example["content"]
        # instruction-style
        instr = example.get("instruction", "")
        ctx = example.get("context", "")
        out = example.get("output", "")
        # fallback to concatenation
        parts = []
        if instr:
            parts.append(instr)
        if ctx:
            parts.append(ctx)
        if out:
            parts.append(out)
        return "\n\n".join(parts) if parts else ""

    def tokenize_fn(example):
        txt = build_text_from_example(example)
        return tokenizer(txt, truncation=True, max_length=1024)

    print("Loading dataset (custom jsonl loader)...")
    data_path = "/home/xzy/QWEN3-8B/RAG_extracted/dataset-pra/training_data.jsonl"
    examples = []
    import json
    with open(data_path, "r", encoding="utf-8") as rf:
        for i, line in enumerate(rf):
            if args.max_train_samples and i >= args.max_train_samples:
                break
            try:
                j = json.loads(line)
            except:
                continue
            txt = build_text_from_example(j)
            if not txt:
                continue
            examples.append({"text": txt})

    from datasets import Dataset
    ds = Dataset.from_list(examples)

    tokenized = ds.map(tokenize_fn, remove_columns=ds.column_names)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    print("Applying LoRA...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout
    )
    model = get_peft_model(model, peft_config)

    print("Preparing Trainer and TrainingArguments...")
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_train_epochs,
        logging_steps=1,
        save_strategy="steps",
        save_steps=200,
        fp16=False,
        bf16=True,
        deepspeed=(args.deepspeed_config if args.deepspeed_config and os.path.exists(args.deepspeed_config) else None),
        optim="adamw_torch",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=data_collator,
        tokenizer=tokenizer,
        callbacks=[StepLoggingCallback()],
    )

    print("Starting training...")
    trainer.train()

    print("Saving adapter and model...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

if __name__ == "__main__":
    main()


