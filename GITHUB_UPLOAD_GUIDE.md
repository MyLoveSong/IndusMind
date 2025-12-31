# IndusMind - GitHub上传指南

## 📁 项目概况
- **总大小**: ~56GB
- **文件数量**: 数万个
- **主要大文件**: 模型文件(~40GB)、训练数据、依赖包

## 🚀 上传策略

### 策略一：轻量级代码上传 (推荐)
只上传核心代码和文档，排除大文件到GitHub Release

#### 步骤：
1. **运行自动化脚本**：
   ```batch
   # 双击运行
   upload_to_github.bat
   ```

2. **手动优化** (如有需要)：
   ```bash
   # 1. 初始化仓库
   git init
   git config user.name "谢泽宇"
   git config user.email "xiezeyu@zju.edu.cn"

   # 2. 创建 .gitignore
   # (脚本已自动创建)

   # 3. 添加文件
   git add .

   # 4. 提交
   git commit -m "feat: IndusMind v1.0 - 产业报告智能生成系统"

   # 5. 连接远程仓库
   git remote add origin https://github.com/MyLoveSong/IndusMind.git
   git push -u origin main
   ```

3. **上传大文件到Release**：
   - 去 GitHub仓库 → Releases → Create new release
   - 上传模型文件压缩包：`QWEN3-8B.7z`
   - 添加标签：`v1.0-models`

### 策略二：Git LFS大文件存储
如果需要版本控制大文件，使用Git LFS

#### 安装Git LFS：
```bash
# Windows
choco install git-lfs
git lfs install

# 或下载安装包
# https://git-lfs.github.com/
```

#### 配置大文件跟踪：
```bash
# 跟踪模型文件
git lfs track "*.safetensors"
git lfs track "*.bin"
git lfs track "*.pth"

# 添加到 .gitattributes
git add .gitattributes
```

## 📋 排除的文件类型

### 必须排除 (节省空间)：
- `*.safetensors` - 模型权重文件
- `*.bin` - 二进制模型文件
- `*.pth`/*.pt - PyTorch模型
- `*.7z`/*.zip - 压缩包
- `node_modules/` - Node.js依赖
- `venv/` - Python虚拟环境
- `__pycache__/` - Python缓存

### 可选排除：
- `logs/` - 日志文件
- `*.log` - 训练日志
- `data/` - 原始数据 (如果不想公开)

## 🔧 优化建议

### 1. 仓库结构优化
```
IndusMind/
├── src/                 # 核心源代码
├── docs/                # 项目文档
├── scripts/            # 部署脚本
├── tests/              # 测试文件
├── requirements.txt    # Python依赖
├── package.json       # Node.js配置
├── README.md          # 项目说明
└── .gitignore         # 忽略规则
```

### 2. 分离部署包
- 创建 `models/` 目录但不提交到Git
- 通过脚本自动下载模型：
```python
# 在代码中添加模型下载逻辑
def download_model():
    # 从HuggingFace或私有存储下载
    pass
```

### 3. 使用子模块
```bash
# 如果有独立的组件
git submodule add https://github.com/MyLoveSong/indusmind-models.git models
```

## 📊 上传后的仓库大小预期

### 代码仓库 (Git)：
- **大小**: ~500MB - 2GB
- **内容**: 源代码、文档、脚本、小型数据文件

### Release附件：
- **模型文件**: ~40GB (压缩后~15GB)
- **训练数据**: ~10GB
- **完整部署包**: ~56GB

## 🎯 推荐操作流程

1. **立即执行**: 运行 `upload_to_github.bat`
2. **验证上传**: 检查GitHub仓库内容
3. **创建Release**: 上传大文件包
4. **更新文档**: 添加详细的部署说明
5. **分享链接**: 向老师和同学展示项目

## ⚠️ 注意事项

- **GitHub限制**: 单个文件≤100MB，仓库≤50GB
- **网络因素**: 大文件上传可能需要时间
- **隐私保护**: 注意不要上传敏感数据
- **版本管理**: 为不同阶段创建标签

## 📞 获取帮助

如果上传过程中遇到问题：
1. 检查网络连接
2. 确认Git和GitHub配置正确
3. 查看GitHub状态页面
4. 联系项目维护者

---

**IndusMind - 让AI助力产业决策！** 🚀
