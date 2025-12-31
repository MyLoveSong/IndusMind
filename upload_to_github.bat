@echo off
echo IndusMind - 上传到GitHub脚本
echo =================================

cd /d "d:\ZJU\软件工程管理\QWEN3-8B"

echo 步骤1: 初始化Git仓库
git init

echo 步骤2: 配置用户信息
git config user.name "谢泽宇"
git config user.email "xiezeyu@zju.edu.cn"

echo 步骤3: 添加.gitignore文件 (排除大文件)
echo # 大模型文件
*.safetensors
*.bin
*.pth
*.pt
*.7z
*.zip

echo # Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd

echo # Node.js
node_modules/
npm-debug.log*

echo # 日志文件
*.log
logs/

echo # 临时文件
*.tmp
*.temp

echo # 环境文件
venv/
.venv/

echo # IDE文件
.vscode/
.idea/

echo # 数据文件 (可选排除)
data/
models/
*.sqlite3 > .gitignore

echo 步骤4: 添加核心文件到Git
git add .

echo 步骤5: 提交初始版本
git commit -m "Initial commit: IndusMind - 产业报告智能生成系统

核心功能:
- 基于Qwen3-8B的LoRA微调模型
- RAG检索增强生成系统
- LangChain多Agent协作框架
- Vue3前端 + Node.js后端架构
- 完整的产业报告自动化生成流程

技术亮点:
- 本地化AI部署，无需外部API
- 150轮专业领域微调训练
- FAISS向量检索优化
- 4-bit量化推理加速"

echo 步骤6: 添加远程仓库
git branch -M main
git remote add origin https://github.com/MyLoveSong/IndusMind.git

echo 步骤7: 推送代码到GitHub
git push -u origin main

echo =================================
echo 上传完成！请注意:
echo 1. 大模型文件已被排除在版本控制外
echo 2. 如需分享模型，请通过GitHub Release上传
echo 3. 建议添加项目说明文档
echo =================================

pause
