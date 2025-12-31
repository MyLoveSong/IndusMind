# QWEN3-8B 产业报告生成系统

一个基于本地 Qwen3-8B 模型的完整产业报告生成系统，集成了 LoRA 微调、RAG 检索增强和 LangChain 链式调用。

## 👥 项目成员

### 核心开发者
- **前端开发**: 陆昊辰 (Github: [@denis-lu](https://github.com/denis-lu))
- **后端及大模型构建训练**: 谢泽宇 (Github: [@LoveSong](https://github.com/LoveSong))

### 致谢

衷心感谢 **浙江大学 (ZJU)** 为我们提供了优秀的学习平台和丰富的学术资源。

特别感谢我们小组的所有成员，在这个项目中每个人都付出了巨大的努力和智慧。从需求分析、系统设计、编码实现到测试部署，每一个环节都凝聚着团队成员的心血。没有大家的通力合作和相互支持，这个项目不可能取得如此出色的成果。

**永远铭记这段宝贵的时光！** 🙏

---

## 🎯 项目特色

## 项目结构

```
project_clean/
├── docs/                    # 项目文档
│   ├── images/             # 文档图片
│   └── *.md                # Markdown 文档
├── scripts/                # 启动和管理脚本
│   ├── start_local_industry_report_stack.sh
│   ├── stop_local_industry_report_stack.sh
│   └── check_services.sh
├── logs/                   # 日志文件
├── configs/                # 配置文件
├── models/                 # 模型文件和数据
├── data/                   # 训练数据
├── src/                    # 源代码
│   ├── rag/               # RAG 服务
│   ├── model_server/     # 本地模型服务器
│   ├── langchain/         # LangChain 集成
│   └── backend/           # 后端 API
├── frontend/               # 前端应用
├── tests/                  # 测试文件
├── docker/                 # Docker 配置
└── tools/                  # 工具和辅助脚本
```

## 核心特性

- **本地 LoRA 微调模型**: 基于 Qwen3-8B 的产业报告生成模型
- **RAG 检索增强**: FAISS 向量搜索 + 上下文注入
- **LangChain 集成**: 完整的链式调用和管理
- **现代化前端**: Vue 3 + Element Plus + Pinia
- **高性能后端**: Node.js + Express + SQLite/MySQL

## 🚀 快速开始

### 一键运行 (推荐)
```bash
# 使用一键运行脚本 (包含完整功能)
python3 run.py

# 或直接运行可执行脚本
./run.sh

# 仅启动后端服务 (不启动前端)
python3 run.py --no-frontend

# 启动后自动运行功能测试
python3 run.py --test
```

### 手动启动
```bash
# 启动 LoRA + RAG + 后端 + 前端
bash scripts/start_local_industry_report_stack.sh --with-frontend
```

### 2. 访问前端
打开浏览器访问: http://127.0.0.1:5173

### 3. 生成产业报告
1. 点击"新建产业报告"
2. 填写行业、场景、目标等信息
3. 点击"生成报告"
4. 系统将使用本地微调模型生成完整的产业分析报告

## 服务架构

- **前端 (5173)**: Vue 3 + Vite 开发服务器
- **后端 (3000)**: Node.js Express API 服务器
- **LoRA 模型服务 (8001)**: 本地 Qwen3-8B 模型推理
- **RAG 服务 (8002)**: 检索增强生成
- **LangChain 服务 (8003)**: 链式调用管理

## 环境要求

- Python 3.8+
- Node.js 18+
- CUDA 11.8+ (GPU 推理)
- 至少 16GB RAM
- 至少 50GB 磁盘空间

## 开发指南

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt
npm install

# 启动开发服务
bash scripts/start_local_industry_report_stack.sh --with-frontend
```

### 测试
```bash
# 运行单元测试
python -m pytest tests/

# 运行功能集成测试
bash scripts/test_functionality.sh

# 或使用 make 命令
make test       # 单元测试
make test-func  # 功能测试

# 检查服务状态
bash scripts/check_services.sh
```

## 许可证

本项目仅供学习和研究使用。
