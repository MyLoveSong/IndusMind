#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def parse_training_log(log_file):
    """解析训练日志文件，提取loss、step、epoch等信息"""
    steps = []
    losses = []
    avg_losses = []
    epochs = []
    learning_rates = []
    grad_norms = []

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析Transformers Trainer的日志格式
    # {'loss': 1.7931, 'grad_norm': 0.002609371906146407, 'learning_rate': 4.999739583333334e-05, 'epoch': 0.01}
    pattern = r"'loss':\s*([0-9.]+).*?'grad_norm':\s*([0-9.]+).*?'learning_rate':\s*([0-9.e-]+).*?'epoch':\s*([0-9.]+)"
    matches = re.findall(pattern, content)

    for match in matches:
        loss, grad_norm, lr, epoch = map(float, match)
        steps.append(len(steps) + 1)  # 步数从1开始
        losses.append(loss)
        epochs.append(epoch)
        learning_rates.append(lr)
        grad_norms.append(grad_norm)

    # 计算移动平均loss
    window_size = 10
    for i in range(len(losses)):
        start_idx = max(0, i - window_size + 1)
        avg_loss = sum(losses[start_idx:i+1]) / (i - start_idx + 1)
        avg_losses.append(avg_loss)

    return {
        'steps': steps,
        'losses': losses,
        'avg_losses': avg_losses,
        'epochs': epochs,
        'learning_rates': learning_rates,
        'grad_norms': grad_norms
    }

def plot_training_trends(data, output_dir='./'):
    """绘制训练趋势图"""
    os.makedirs(output_dir, exist_ok=True)

    # Set font to support English
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建子图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('LoRA Training Trend Analysis', fontsize=16, fontweight='bold')

    # 1. Loss曲线
    ax1.plot(data['steps'], data['losses'], 'b-', alpha=0.7, label='Raw Loss', linewidth=1)
    ax1.plot(data['steps'], data['avg_losses'], 'r-', linewidth=2, label=f'Moving Average Loss (window={10})')
    ax1.set_xlabel('Training Steps')
    ax1.set_ylabel('Loss Value')
    ax1.set_title('Training Loss Trend')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. 学习率变化
    ax2.plot(data['steps'], data['learning_rates'], 'g-', linewidth=2)
    ax2.set_xlabel('Training Steps')
    ax2.set_ylabel('Learning Rate')
    ax2.set_title('Learning Rate Changes')
    ax2.set_yscale('log')  # 对数尺度
    ax2.grid(True, alpha=0.3)

    # 3. 梯度范数
    ax3.plot(data['steps'], data['grad_norms'], 'orange', linewidth=2)
    ax3.set_xlabel('Training Steps')
    ax3.set_ylabel('Gradient Norm')
    ax3.set_title('Gradient Norm Changes')
    ax3.grid(True, alpha=0.3)

    # 4. Loss分布直方图
    ax4.hist(data['losses'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax4.axvline(np.mean(data['losses']), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(data["losses"]):.4f}')
    ax4.axvline(np.median(data['losses']), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(data["losses"]):.4f}')
    ax4.set_xlabel('Loss Value')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Loss Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存图片
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'training_trends_{timestamp}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Training trend chart saved to: {output_file}")

    # 额外保存单独的loss曲线图
    plt.figure(figsize=(12, 6))
    plt.plot(data['steps'], data['losses'], 'b-', alpha=0.7, label='Raw Loss', linewidth=1)
    plt.plot(data['steps'], data['avg_losses'], 'r-', linewidth=2, label=f'Moving Average Loss (window={10})')
    plt.xlabel('Training Steps', fontsize=12)
    plt.ylabel('Loss Value', fontsize=12)
    plt.title('LoRA Training Loss Curve', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)

    loss_curve_file = os.path.join(output_dir, f'loss_curve_{timestamp}.png')
    plt.savefig(loss_curve_file, dpi=300, bbox_inches='tight')
    print(f"Loss curve chart saved to: {loss_curve_file}")

    plt.show()

def print_training_stats(data):
    """打印训练统计信息"""
    print("=" * 60)
    print("LoRA Training Statistics")
    print("=" * 60)

    losses = np.array(data['losses'])
    print(f"Total training steps: {len(data['steps'])}")
    print(f"Final epoch: {data['epochs'][-1]:.3f}")
    print(f"Loss statistics:")
    print(f"  Minimum: {np.min(losses):.4f}")
    print(f"  Maximum: {np.max(losses):.4f}")
    print(f"  Mean: {np.mean(losses):.4f}")
    print(f"  Standard deviation: {np.std(losses):.4f}")
    print(f"  Median: {np.median(losses):.4f}")

    # 计算loss下降趋势
    if len(losses) > 10:
        first_half = np.mean(losses[:len(losses)//2])
        second_half = np.mean(losses[len(losses)//2:])
        improvement = first_half - second_half
        print(f"Loss improvement: {improvement:.4f} ({improvement/first_half*100:.1f}%)")

    print(f"Learning rate range: {np.min(data['learning_rates']):.2e} - {np.max(data['learning_rates']):.2e}")
    print(f"Gradient norm range: {np.min(data['grad_norms']):.4f} - {np.max(data['grad_norms']):.4f}")
    print("=" * 60)

def main():
    # 训练日志文件路径
    log_file = "/home/xzy/QWEN3-8B/QWEN3-8B/finetune/full_train_ddp.log"

    if not os.path.exists(log_file):
        print(f"Error: Training log file not found {log_file}")
        return

    print(f"Parsing training log: {log_file}")

    # 解析日志
    data = parse_training_log(log_file)

    if not data['steps']:
        print("Error: No valid training data found")
        return

    # 打印统计信息
    print_training_stats(data)

    # 绘制趋势图
    plot_training_trends(data, output_dir='/home/xzy/QWEN3-8B/')

if __name__ == "__main__":
    main()
