# Film Media 搜索 Web 服务

这是一个基于 Flask 的 Web 服务，提供文本转向量媒体匹配和文件下载功能。用户可以通过 Web 界面输入文本描述，系统会自动将文本转换为向量，搜索匹配的媒体文件，并提供下载功能。

## 功能特性

- 🔍 **文本转向量搜索**：使用 Azure OpenAI 将文本转换为向量
- 🎬 **媒体匹配**：基于向量相似度搜索匹配的媒体文件
- 📥 **文件下载**：自动从 AWS S3 下载匹配的媒体文件
- 📊 **实时进度**：显示处理进度和状态
- 🎨 **响应式界面**：支持桌面和移动设备
- ⚡ **异步处理**：后台处理，不阻塞用户界面

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并填入正确的配置：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```env
# Flask 配置
SECRET_KEY=your-secret-key-here

# Azure OpenAI 配置
AZURE_OPENAI_API_KEY_EASTUS=your-azure-openai-api-key
AZURE_OPENAI_API_ENDPOINT_EASTUS=https://your-resource.openai.azure.com/

# AWS S3 配置
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-east-1
AWS_BUCKET=one2x-share
```

### 3. 运行服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

## 使用说明

### 基本使用

1. **输入搜索文本**：在文本框中输入要搜索的媒体内容描述
2. **调整参数**：
   - **匹配阈值**：0-1之间，数值越高匹配越严格
   - **返回数量**：最多返回的媒体数量
3. **开始搜索**：点击"开始搜索"按钮
4. **等待处理**：系统会显示实时进度
5. **下载文件**：处理完成后可以下载匹配的媒体文件

### 搜索示例

- "一个人在跑步的场景"
- "美丽的日落风景"
- "城市夜景灯光"
- "海浪拍打沙滩"
- "森林中的小径"

## API 接口

### 搜索媒体

```
POST /api/search
Content-Type: application/json

{
  "text": "搜索文本",
  "match_threshold": 0.5,
  "match_count": 5
}
```

### 获取任务状态

```
GET /api/status/{task_id}
```

### 下载文件

```
GET /api/download/{task_id}/{filename}
```

### 列出下载文件

```
GET /api/downloads/{task_id}
```

## 技术架构

### 后端技术

- **Flask**：Web 框架
- **Azure OpenAI**：文本转向量服务
- **AWS S3**：文件存储和下载
- **one2x-sdk**：媒体匹配 API 客户端
- **asyncio**：异步处理
- **SQLite**：任务状态存储（内存）

### 前端技术

- **Bootstrap 5**：UI 框架
- **Axios**：HTTP 客户端
- **JavaScript**：交互逻辑

## 部署建议

### 开发环境

```bash
python app.py
```

### 生产环境

使用 Gunicorn 部署：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

构建和运行：

```bash
docker build -t film-media-service .
docker run -p 5000:5000 --env-file .env film-media-service
```

## 注意事项

### 安全考虑

- 设置强密码的 SECRET_KEY
- 使用 HTTPS 传输
- 限制文件下载权限
- 定期清理临时文件

### 性能优化

- 调整匹配阈值减少不相关结果
- 限制返回数量提高响应速度
- 使用 CDN 加速文件下载
- 监控内存使用情况

### 错误处理

- 检查环境变量配置
- 确保 AWS 和 Azure 服务可用
- 监控 API 调用限制
- 处理网络超时情况

## 故障排除

### 常见问题

1. **文本转向量失败**
   - 检查 Azure OpenAI 配置
   - 确认 API 密钥有效
   - 检查网络连接

2. **文件下载失败**
   - 检查 AWS S3 配置
   - 确认文件权限
   - 检查存储桶名称

3. **媒体匹配无结果**
   - 降低匹配阈值
   - 尝试不同的搜索文本
   - 检查 API 服务状态

### 日志查看

服务运行时会输出详细日志，包括：
- 文本转向量过程
- API 调用结果
- 文件下载状态
- 错误信息

## 许可证

MIT License
