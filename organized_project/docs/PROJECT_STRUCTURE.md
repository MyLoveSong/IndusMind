# 项目结构说明

本文档详细说明了 QWEN3-8B 产业报告生成系统的目录结构和文件组织。

## 目录结构

```
organized_project/
├── README.md                    # 项目说明文档
├── Makefile                     # 自动化构建脚本
├── requirements.txt             # Python 依赖
├── .gitignore                   # Git 忽略文件
│
├── docs/                        # 文档目录
│   ├── images/                  # 文档图片
│   ├── *.md                     # 各种文档文件
│   └── PROJECT_STRUCTURE.md     # 本文件
│
├── scripts/                     # 脚本目录
│   ├── start_local_industry_report_stack.sh  # 一键启动脚本
│   ├── stop_local_industry_report_stack.sh   # 一键停止脚本
│   ├── check_services.sh        # 服务状态检查
│   ├── dev-setup.sh             # 开发环境设置
│   └── project-status.sh        # 项目状态检查
│
├── logs/                        # 日志文件目录
│   ├── backend.log              # 后端日志
│   ├── frontend.log             # 前端日志
│   ├── rag_service.log          # RAG 服务日志
│   └── model_server.log        # 模型服务器日志
│
├── configs/                     # 配置文件目录
│   ├── .env.example             # 环境变量模板
│   ├── deepspeed_config.json    # DeepSpeed 配置
│   └── *.json                   # 其他配置文件
│
├── models/                      # 模型文件目录
│   ├── pretrained/              # 预训练模型
│   │   └── Qwen3-8B/           # Qwen3-8B 基础模型
│   └── finetuned/               # 微调后的模型
│       └── lora_full/           # LoRA 微调权重
│
├── data/                        # 数据目录
│   ├── training/                # 训练数据
│   ├── evaluation/              # 评估数据
│   └── processed/               # 处理后的数据
│
├── src/                         # 源代码目录
│   ├── rag/                     # RAG 检索增强服务
│   │   ├── api_server.py       # RAG API 服务
│   │   ├── rag_service.py       # RAG 核心逻辑
│   │   └── requirements.txt     # RAG 服务依赖
│   │
│   ├── model_server/           # 本地模型服务器
│   │   ├── model_server.py     # 模型推理服务
│   │   └── requirements.txt     # 模型服务依赖
│   │
│   ├── langchain/               # LangChain 集成服务
│   │   ├── langchain_api_server.py
│   │   └── langchain_service.py
│   │
│   └── backend/                 # 后端 API 服务
│       ├── routes/              # API 路由
│       ├── middleware/          # 中间件
│       ├── config/              # 后端配置
│       ├── package.json         # Node.js 依赖
│       └── server.js            # 服务器入口
│
├── frontend/                    # 前端应用目录
│   └── main/                    # 主前端应用 (Vue 3)
│       ├── src/                 # 源代码
│       │   ├── components/      # Vue 组件
│       │   ├── views/           # 页面视图
│       │   ├── stores/          # Pinia 状态管理
│       │   ├── router/          # 路由配置
│       │   └── main.js          # 前端入口
│       ├── public/              # 静态资源
│       ├── package.json         # 前端依赖
│       └── vite.config.js       # Vite 配置
│
├── tests/                       # 测试目录
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── e2e/                     # 端到端测试
│
├── docker/                      # Docker 配置
│   ├── docker-compose.yml       # Docker Compose 配置
│   ├── Dockerfile.backend       # 后端镜像
│   ├── Dockerfile.frontend      # 前端镜像
│   ├── Dockerfile.rag           # RAG 服务镜像
│   └── Dockerfile.model         # 模型服务镜像
│
└── tools/                       # 工具和辅助脚本
    ├── evaluation/              # 评估工具
    ├── preprocessing/           # 数据预处理
    └── classmates_projects/     # 同学项目参考
```

## 文件命名规范

### 脚本文件
- 使用 `kebab-case` 命名，如 `start-services.sh`
- 所有脚本文件都需要执行权限 `chmod +x`

### Python 文件
- 使用 `snake_case` 命名，如 `model_server.py`
- 包名使用小写，如 `rag_service.py`

### JavaScript 文件
- 使用 `camelCase` 命名，如 `reportStore.js`
- React/Vue 组件使用 `PascalCase`，如 `ReportCard.vue`

### 配置文件
- 环境变量文件：`.env`
- JSON 配置文件：`config.json`
- YAML 配置文件：`config.yaml`

## 开发工作流

### 1. 初始化项目
```bash
make setup          # 或 bash scripts/dev-setup.sh
```

### 2. 启动开发环境
```bash
make dev           # 或 bash scripts/start_local_industry_report_stack.sh --with-frontend
```

### 3. 检查项目状态
```bash
make status        # 或 bash scripts/project-status.sh
```

### 4. 运行测试
```bash
make test
```

### 5. 清理项目
```bash
make clean
```

## 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 5173 | Vue 3 + Vite 开发服务器 |
| 后端 API | 3000 | Node.js Express API 服务 |
| 本地模型 | 8001 | Qwen3-8B LoRA 模型推理 |
| RAG 服务 | 8002 | 检索增强生成服务 |
| LangChain | 8003 | 链式调用管理服务 |

## 环境变量说明

项目使用 `.env` 文件管理环境变量，主要包括：

- **API 密钥**: 各种 LLM 服务的访问密钥
- **数据库配置**: MySQL/SQLite 连接信息
- **服务地址**: 各微服务的访问地址
- **模型配置**: 本地模型的路径和参数

详细配置请参考 `configs/.env.example`。

## 注意事项

1. **模型文件**: 由于模型文件较大，不包含在版本控制中，需要手动下载或训练
2. **敏感信息**: API 密钥等敏感信息请妥善保管，不要提交到版本控制
3. **日志管理**: 日志文件会自动写入 `logs/` 目录，请定期清理
4. **依赖管理**: Python 和 Node.js 依赖分别管理，注意版本兼容性
