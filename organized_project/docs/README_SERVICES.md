# 🚀 SmartDigest 智能产业报告生成系统

基于AI大模型的产业报告智能生成平台，支持多轮对话式需求澄清、自动数据抓取与结构化写作。

## 🎯 当前状态

✅ **前后端服务已启动并运行正常**
- 前端界面: http://localhost:5173
- 后端API: http://localhost:3000
- 数据库: SQLite (自动配置)

## 🔧 快速启动

### 方法1: 一键启动脚本
```bash
cd /home/xzy/QWEN3-8B
./start_services.sh
```

### 方法2: 手动启动

**终端1 - 启动后端:**
```bash
cd QWEN3-8B/ZJU-SEM-Project-master/backend
USE_SQLITE=true SQLITE_DB_PATH=../data.sqlite3 node server.js
```

**终端2 - 启动前端:**
```bash
cd QWEN3-8B/ZJU-SEM-Project-master/frontend/final-project
npm run dev -- --host 0.0.0.0 --port 5173
```

## 📊 服务状态检查

```bash
cd /home/xzy/QWEN3-8B
./check_services.sh
```

## 🎮 使用指南

### 1. 访问系统
打开浏览器访问: **http://localhost:5173**

### 2. 测试账号
- 用户名: `testuser`
- 密码: `testpass123`

### 3. 核心功能体验

#### 📄 分页浏览
- 报告列表自动分页显示
- 支持每页10/20/50条记录

#### 🔍 智能搜索
- 实时搜索报告标题和内容
- 支持产业、状态筛选
- 标签云筛选

#### 📊 数据统计
- 实时统计报告数量
- 对话统计和活跃度分析
- 产业分布可视化

#### 🏷️ 标签管理
- 为报告添加自定义标签
- 标签筛选和分类
- 智能标签建议

#### 🔄 批量操作
- 批量选择多个报告
- 批量删除功能
- 操作确认和反馈

#### 📤 内容导出
- PDF专业格式导出
- Markdown轻量格式导出
- 自动文件下载

## 🏗️ 系统架构

### 后端技术栈
- **框架**: Node.js + Express.js
- **数据库**: SQLite (自动降级)
- **认证**: JWT Token
- **AI集成**: 本地QWEN-3B模型

### 前端技术栈
- **框架**: Vue 3 + Composition API
- **UI库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite

### AI能力
- 🤖 **本地大模型**: QWEN-3B (4-bit量化)
- 🔍 **RAG检索**: FAISS向量搜索
- 🧠 **智能对话**: LangChain多轮对话
- 📝 **报告生成**: 结构化写作

## 🎯 核心特性

### 1. 智能报告生成
- 多轮对话需求澄清
- 自动大纲生成
- 结构化内容写作
- 实时进度跟踪

### 2. 数据管理
- 文件上传和解析
- 数据源管理
- 内容版本控制
- 导出多种格式

### 3. 用户体验
- 现代化毛玻璃设计
- 响应式布局适配
- 实时状态反馈
- 直观的操作流程

## 📋 API文档

### 核心接口
```
POST   /api/auth/login          # 用户登录
GET    /api/reports             # 获取报告列表 (支持分页/搜索)
POST   /api/reports             # 创建新报告
PUT    /api/reports/:id/tags    # 更新报告标签
POST   /api/reports/batch-delete # 批量删除
GET    /api/reports/:id/export  # 导出报告
GET    /api/reports/stats       # 统计信息
```

### 响应格式
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

## 🔧 故障排除

### 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep -E ":(3000|5173)"

# 杀死占用进程
kill -9 <PID>

# 重新启动
./start_services.sh
```

### 数据库连接问题
系统会自动使用SQLite数据库，无需额外配置。

### 前端构建问题
```bash
cd QWEN3-8B/ZJU-SEM-Project-master/frontend/final-project
rm -rf node_modules
npm install
npm run dev
```

## 📈 性能优化

- **数据库**: SQLite轻量级，读写性能优秀
- **前端**: Vite快速构建，热重载开发体验
- **缓存**: 智能分页减少数据传输
- **压缩**: 自动Gzip压缩传输数据

## 🎉 立即体验

现在就可以访问 http://localhost:5173 开始体验完整的AI驱动产业报告生成功能！

### 推荐体验流程
1. **登录系统** - 使用测试账号
2. **浏览报告** - 查看分页和搜索功能
3. **创建报告** - 体验AI生成流程
4. **管理内容** - 尝试标签和批量操作
5. **导出内容** - 下载PDF或Markdown格式

---

**🚀 祝您使用愉快！如有问题请查看服务日志或重新运行启动脚本。**
