# 已删除文件恢复清单

## 📊 删除统计总览
- **原始目录大小**: 56GB
- **清理后大小**: 309MB
- **删除数据总量**: 约55.7GB
- **保留的前端文件**: 255MB (node_modules + ZJU-SEM-Project-master)
- **压缩包大小**: 19MB (仅包含源代码)

## 🗂️ 已删除的主要目录及文件

### 1. 模型权重文件 (总计: 39.4GB)
```
models/pretrained/           # 16.0GB - Qwen预训练模型权重
├── pytorch_model.bin       # 主要模型权重文件
├── tokenizer.json          # 分词器配置
├── config.json             # 模型配置
├── vocab.txt              # 词汇表
└── [其他模型文件]

models/finetuned/           # 7.4GB - 微调后的模型权重
├── pytorch_model.bin      # 微调模型权重
├── optimizer.pt           # 优化器状态
├── scheduler.pt           # 学习率调度器
├── trainer_state.json     # 训练状态
└── [检查点文件]

QWEN3-8B/models/           # 16.0GB - 项目本地模型文件
├── [完整的模型权重目录]
└── [相关配置文件]
```

### 2. 训练输出文件 (7.4GB)
```
QWEN3-8B/finetune_output/   # 7.4GB - 微调训练输出
├── checkpoint-*/          # 训练检查点
├── logs/                  # 训练日志
├── runs/                  # TensorBoard日志
└── [评估结果]
```

### 3. Python虚拟环境 (7.1GB)
```
QWEN3-8B/venv/             # 7.1GB - Python虚拟环境
├── bin/                   # 可执行文件
├── lib/                   # Python库文件
├── include/               # 头文件
├── share/                 # 共享数据
└── pyvenv.cfg            # 环境配置
```

### 4. RAG提取数据 (2.1GB)
```
QWEN3-8B/RAG_extracted/    # 2.1GB - RAG系统提取的文档数据
├── documents/            # 提取的文档
├── embeddings/           # 文档向量嵌入
├── index/                # 向量索引文件
├── metadata/             # 文档元数据
└── [处理后的数据文件]
```

### 5. 前端相关文件 (255MB)
```
node_modules/              # 90MB - 前端Node.js依赖包
├── @vue/                  # Vue.js相关包
├── element-plus/          # UI组件库
├── vite/                  # 构建工具
├── axios/                 # HTTP客户端
├── pinia/                 # 状态管理
└── [其他前端依赖]

ZJU-SEM-Project-master/    # 165MB - 前端项目主目录
├── frontend/              # Vue.js前端应用
│   ├── final-project/     # 主要前端代码
│   ├── src/              # 源代码
│   ├── node_modules/     # 前端依赖
│   ├── package.json      # 项目配置
│   └── vite.config.js    # Vite配置
├── backend/              # 前端后端API
├── data.sqlite3          # 前端数据库
└── [项目文档和配置]
```

### 6. 备份和存档文件 (206MB)
```
node.js/                   # 206MB - Node.js运行时备份
└── [Node.js运行时文件和工具]
```

## 📋 删除时间线
```
22:00 - 开始清理大文件
22:01 - 删除 models/pretrained/ (16GB)
22:02 - 删除 models/finetuned/ (7.4GB)
22:03 - 删除 QWEN3-8B/models/ (16GB)
22:04 - 删除 QWEN3-8B/finetune_output/ (7.4GB)
22:05 - 删除 QWEN3-8B/venv/ (7.1GB)
22:06 - 删除 QWEN3-8B/RAG_extracted/ (2.1GB)
22:07 - 删除备份文件 (444MB)
22:08 - 重新压缩为19MB
```

## 🔄 恢复计划

### 优先级1: 核心模型权重 (39.4GB)
```bash
# 下载Qwen预训练模型
huggingface-cli download Qwen/Qwen2-7B-Instruct --local-dir models/pretrained/

# 下载微调模型 (如果有的话)
# 从训练输出恢复或重新训练
```

### 优先级2: 训练环境 (7.1GB)
```bash
# 重新创建虚拟环境
cd QWEN3-8B
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 优先级3: RAG数据 (2.1GB)
```bash
# 重新运行RAG数据提取脚本
# 需要原始文档数据源
python scripts/extract_rag_data.py
```

### 优先级4: 训练输出 (7.4GB)
```bash
# 重新运行微调训练
python train_lora.py
# 或从云端恢复检查点
```

## 💾 存储建议
- **短期存储**: 保留19MB压缩包作为最小备份
- **长期存储**: 考虑将大文件存储在云端(Git LFS, Hugging Face, AWS S3)
- **版本控制**: 使用Git LFS管理大文件

## ⚠️ 重要提醒
- 所有删除的文件已**永久删除**，无法从本地恢复
- 需要从外部源重新下载模型权重
- 建议设置自动备份策略
- 考虑使用符号链接管理大文件
- **前端符号链接**: `frontend/` → `ZJU-SEM-Project/frontend/final-project/`

## 📝 前端文件说明
- **符号链接**: `QWEN3-8B/frontend` 指向 `ZJU-SEM-Project-master/frontend/final-project`
- **依赖管理**: `node_modules` 包含所有前端运行依赖
- **项目结构**: 采用前后端分离架构，前端使用Vue.js + Vite

---
*生成时间: 2025-12-28*
*清理前大小: 56GB*
*清理后大小: 309MB*
