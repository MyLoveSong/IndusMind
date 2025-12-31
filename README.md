# 🧠 IndusMind - 产业报告智能生成系统

## IndusMind: Industry Intelligence Mind

基于大语言模型的产业报告智能生成平台，融合LoRA微调、RAG检索增强和多Agent协作技术，自动生成专业产业分析报告。

[![GitHub](https://img.shields.io/badge/GitHub-CogniFlow--blue?style=flat-square&logo=github)](https://github.com/MyLoveSong/CogniFlow-)
[![Node.js](https://img.shields.io/badge/Node.js-20+-green?style=flat-square&logo=node.js)](https://nodejs.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-brightgreen?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?style=flat-square&logo=mysql)](https://www.mysql.com/)
[![n8n](https://img.shields.io/badge/n8n-Automation-purple?style=flat-square&logo=n8n)](https://n8n.io/)

## 👥 项目成员 (G02组 - 智研通项目)

### 核心开发者
- **项目组长 & 质量经理**: 段林帅
- **前端开发 & 美术设计**: 陆昊辰 (Github: [@denis-lu](https://github.com/denis-lu))
- **后端开发 & 大模型构建**: 谢泽宇 (Github: [@LoveSong](https://github.com/LoveSong))
- **测试开发**: 王宇佳
- **测试开发**: 朱宇文

### 致谢

衷心感谢 **浙江大学 (ZJU)** 为我们提供了优秀的学习平台和丰富的学术资源。

特别感谢我们小组的所有成员，在这个项目中每个人都付出了巨大的努力和智慧。从需求分析、系统设计、编码实现到测试部署，每一个环节都凝聚着团队成员的心血。没有大家的通力合作和相互支持，这个项目不可能取得如此出色的成果。

**永远铭记这段宝贵的时光！** 🙏

---

## 🎯 项目特色

- **🔬 本地 LoRA 微调**: 基于 Qwen3-8B 的产业报告专用模型 (150轮训练)
- **🔍 RAG 检索增强**: FAISS 向量搜索 + 上下文注入 (12,088个文档块)
- **⚡ 高性能推理**: 4-bit NF4 量化，GPU 内存优化
- **🎨 现代化前端**: Vue 3 + Element Plus + Pinia 状态管理
- **🚀 完整后端**: Node.js + Express + SQLite/MySQL
- **🔗 LangChain 集成**: 完整的链式调用和管理

## 🚀 快速开始

### 一键运行 (推荐)

#### Linux/macOS 用户
```bash
# 使用 Python 脚本
python3 run.py

# 或使用可执行脚本
./run.sh
```

#### Windows 用户
```batch
# 双击运行批处理文件
run.bat

# 或使用命令行
python run.py
```

#### 高级选项
```bash
# 仅启动后端服务 (不启动前端)
python3 run.py --no-frontend

# 启动后自动运行功能测试
python3 run.py --test

# 仅检查服务状态
python3 run.py --check
```

### 手动启动
```bash
# 进入整理后的项目目录
cd organized_project

# 启动完整系统
bash scripts/start_local_industry_report_stack.sh --with-frontend
```

## 🌐 服务架构

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端界面 | 5173 | Vue 3 开发服务器 |
| 后端 API | 3000 | Node.js Express API |
| LoRA 模型 | 8001 | Qwen3-8B 推理服务 |
| RAG 服务 | 8002 | 检索增强生成 |

## 📋 使用指南

1. **启动系统**: 运行 `python3 run.py`
2. **访问前端**: 浏览器打开 http://localhost:5173
3. **创建报告**: 点击"新建产业报告"
4. **填写信息**: 输入行业、场景、目标等
5. **生成报告**: 点击生成，等待 AI 分析完成

## 🏗️ 项目结构

```
QWEN3-8B/
├── run.py                 # 🚀 一键运行脚本 (Python)
├── run.sh                 # 🔧 Linux/macOS 可执行启动器
├── run.bat                # 🪟 Windows 可执行文件 (exe等价)
├── organized_project/     # 📁 标准化的项目结构
│   ├── docs/             # 📚 文档
│   ├── scripts/          # 🛠️ 脚本
│   ├── logs/             # 📋 日志
│   ├── configs/          # ⚙️ 配置
│   ├── models/           # 🤖 模型文件
│   ├── data/             # 💾 数据
│   ├── src/              # 💻 源代码
│   ├── frontend/         # 🎨 前端
│   └── tests/            # 🧪 测试
├── QWEN3-8B/            # 🧠 模型训练相关
├── ZJU-SEM-Project/     # 💼 原始前后端代码
└── docs/                 # 📖 原始文档
```

## 🔧 系统要求

- **Python**: 3.8+
- **Node.js**: 18+
- **CUDA**: 11.8+ (可选，GPU 加速)
- **内存**: 16GB+ RAM
- **存储**: 50GB+ 磁盘空间

## 🧪 测试验证

```bash
# 运行功能测试
cd organized_project
bash scripts/test_functionality.sh

# 或使用 make
make test-func
```

## 📊 技术指标

- **训练轮次**: 150 epochs
- **训练时长**: 23小时 (4卡 DDP)
- **模型大小**: Qwen3-8B + LoRA 适配器
- **量化方式**: 4-bit NF4
- **RAG 文档**: 12,088个文本块
- **响应时间**: 30-120秒/报告

## 🎓 学术背景

本项目是浙江大学软件工程课程的结项项目，展示了现代 AI 技术在产业分析领域的实际应用。

## 📄 许可证

本项目仅供学习和研究使用。

---

**再次感谢所有为这个项目付出努力的同学们！** 🎉

**ZJU SEM 2025 永远铭记这段时光！** 🏫❤️
