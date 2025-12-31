#!/bin/bash
set -e
source /home/xzy/anaconda3/etc/profile.d/conda.sh
conda activate XZY
export PYTHONNOUSERSITE=1
# Use accelerate launch to manage distributed environment (recommended)
# Adjust --num_processes to number of GPUs (4 for your A6000 x4)
accelerate launch --num_processes 4 --main_process_port 29500 /home/xzy/QWEN3-8B/finetune/train_lora.py \
  --model_path /home/xzy/QWEN3-8B/models/Qwen/Qwen3-8B \
  --output_dir /home/xzy/QWEN3-8B/finetune_output/lora_full \
  --deepspeed_config /home/xzy/QWEN3-8B/finetune/deepspeed_config.json \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --num_train_epochs 1 \
  --max_train_samples 256 \
  --lora_rank 8 \
  --lora_alpha 16 \
  --lora_dropout 0.1 \
  "$@"


