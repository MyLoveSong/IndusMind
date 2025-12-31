# 本地QWEN3-8B模型集成指南

本指南介绍如何将本地训练的QWEN3-8B模型集成到您的前端和后端兼备的网站中。

## 📋 集成概述

系统包含以下组件：
- **Python模型服务器**: 加载微调后的QWEN3-8B模型，提供OpenAI兼容API
- **Node.js后端**: 处理用户请求，调用本地模型服务
- **Vue.js前端**: 提供AI聊天界面，与用户直接交互

## 🚀 快速启动

### 1. 启动本地模型服务器

```bash
cd /home/xzy/QWEN3-8B/QWEN3-8B

# 创建Python虚拟环境（如果还没有）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动模型服务器
python model_server.py
```

模型服务器将在 `http://127.0.0.1:8001` 启动。

### 2. 启动后端服务

```bash
cd ZJU-SEM-Project-master/backend

# 安装依赖
npm install

# 启动后端
npm start
```

后端将在 `http://localhost:3000` 启动。

### 3. 启动前端服务

```bash
cd ZJU-SEM-Project-master/frontend/final-project

# 安装依赖
npm install

# 启动前端开发服务器
npm run dev
```

前端将在 `http://localhost:5173` 启动。

## 🧪 测试步骤

### 步骤1: 检查模型服务器状态

打开浏览器访问: `http://127.0.0.1:8001/health`

应该看到类似响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-12-28T...",
  "model_info": {
    "base_model": "/home/xzy/QWEN3-8B/models/Qwen/Qwen3-8B",
    "lora_adapter": "/home/xzy/QWEN3-8B/finetune_output/lora_full",
    "device": "cuda",
    "cuda_available": true,
    "loaded": true
  }
}
```

### 步骤2: 测试后端AI状态

访问: `http://localhost:3000/api/ai/status`

应该返回模型状态信息。

### 步骤3: 测试前端聊天界面

1. 打开浏览器访问: `http://localhost:5173`
2. 登录系统（如果需要）
3. 导航到AI聊天页面
4. 检查右上角的模型状态指示器是否显示"模型在线"
5. 发送一条测试消息，如"你好，请介绍一下自己"

### 步骤4: 验证API调用

使用curl测试聊天API：

```bash
curl -X POST http://localhost:3000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "测试消息",
    "system": "你是智能助手"
  }'
```

## 🔧 配置说明

### 环境变量配置

确保后端的 `.env` 文件包含以下配置：

```env
# 本地 QWEN3-8B 配置
LOCAL_QWEN_URL=http://127.0.0.1:8001
LOCAL_QWEN_TIMEOUT_MS=30000
LOCAL_QWEN_API_KEY=your_local_model_token

# 模型回退顺序
MODEL_FALLBACK_ORDER=local,mock
```

### Python模型服务器配置

模型服务器的环境变量：

```bash
export LOCAL_QWEN_API_KEY=your_local_model_token  # 可选，用于身份验证
export MODEL_SERVER_PORT=8001                      # 服务器端口
export MODEL_SERVER_HOST=127.0.0.1                # 绑定地址
```

## 🐛 故障排除

### 常见问题

1. **模型加载失败**
   - 检查CUDA是否可用: `python -c "import torch; print(torch.cuda.is_available())"`
   - 检查模型文件路径是否正确
   - 确保有足够的GPU内存

2. **端口冲突**
   - 模型服务器默认端口8001，如有冲突可修改环境变量
   - 后端默认端口3000，前端默认端口5173

3. **前端无法连接**
   - 检查CORS配置
   - 确认后端服务正在运行
   - 检查网络连接

4. **模型回复质量差**
   - 调整temperature参数（0.1-1.0）
   - 检查微调数据质量
   - 验证LoRA适配器是否正确加载

### 日志查看

- 模型服务器日志: 在启动终端查看
- 后端日志: 检查后端控制台输出
- 前端日志: 打开浏览器开发者工具

## 📊 性能优化

1. **量化加载**: 模型已配置4-bit量化以节省内存
2. **批量处理**: 支持并发请求处理
3. **缓存机制**: 考虑添加响应缓存以提升性能

## 🔄 更新模型

当有新的微调模型时：

1. 更新 `finetune_output/lora_full/` 目录
2. 重启模型服务器
3. 测试新模型的响应质量

## 📞 支持

如果遇到问题，请检查：
1. 所有服务是否正常启动
2. 环境变量配置是否正确
3. 模型文件是否存在且完整
4. 网络连接是否正常

集成完成后，您就可以通过网站前端直接与本地训练的QWEN3-8B模型进行对话了！
