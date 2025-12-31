# 环境变量配置说明

## 翻译功能错误解决方案

您遇到的翻译错误是因为缺少必要的环境变量配置。请按照以下步骤解决：

### 1. 创建 .env 文件

在 `backend` 目录下创建 `.env` 文件，内容如下：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=050228
DB_NAME=smartdigest

# JWT 密钥
JWT_SECRET=your_jwt_secret_key_here

# SiliconFlow API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn

# N8N 配置
N8N_WEBHOOK_URL=http://localhost:5678/webhook/ai-qa
```

### 2. 获取 SiliconFlow API 密钥

1. 访问 [SiliconFlow 官网](https://siliconflow.cn/)
2. 注册账号并登录
3. 在控制台中创建 API 密钥
4. 将密钥替换 `your_siliconflow_api_key_here`

### 3. 重启后端服务

配置完成后，重启后端服务：

```bash
cd backend
npm start
```

### 4. 测试翻译功能

在文章详情页面点击"翻译文章"按钮测试功能是否正常。

## 注意事项

- `.env` 文件包含敏感信息，不要提交到版本控制系统
- 确保 API 密钥有效且有足够的额度
- 如果仍然出现错误，请检查网络连接和 API 服务状态
