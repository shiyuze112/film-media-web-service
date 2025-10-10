# Film Media Search API - 外部API封装方案

## 概述

本项目将原本需要敏感配置的脚本封装成了安全的REST API，供外部人员使用。通过API密钥认证、频率限制、错误处理等机制，确保服务的安全性和稳定性。

## 🚀 主要特性

### 🔐 安全认证
- **API密钥认证**: 支持多个API密钥，通过环境变量配置
- **频率限制**: 每小时最多100次API调用，防止滥用
- **请求验证**: 自动验证API密钥和请求参数

### 📊 完整功能
- **文本转向量**: 使用Azure OpenAI将文本转换为向量
- **媒体搜索**: 基于向量相似度搜索匹配的媒体文件
- **文件下载**: 支持直接下载和在线观看
- **异步处理**: 大文件处理采用异步任务模式

### 🛡️ 错误处理
- **全局错误处理**: 统一的错误响应格式
- **详细日志**: 完整的请求和错误日志记录
- **健康检查**: 服务状态监控接口

### 📚 完整文档
- **API文档**: 详细的接口说明和使用示例
- **部署指南**: 多种部署方式说明
- **测试工具**: 完整的API测试脚本

## 📁 项目结构

```
film-media-web-service/
├── app.py                    # 主应用文件
├── requirements.txt          # Python依赖
├── env.example              # 环境变量示例
├── Dockerfile               # Docker配置
├── docker-compose.yml       # Docker Compose配置
├── start.sh                 # 启动脚本
├── test_api.py              # API测试脚本
├── API_DOCUMENTATION.md     # API文档
├── DEPLOYMENT.md            # 部署指南
├── README_API.md           # 项目说明
├── templates/              # Web界面模板
│   ├── base.html
│   └── index.html
└── downloads/              # 下载文件目录
```

## 🔧 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

### 2. 安装依赖

```bash
# 使用pip安装
pip install -r requirements.txt

# 或使用Docker
docker-compose up -d
```

### 3. 启动服务

```bash
# 使用启动脚本
./start.sh

# 或直接运行
python app.py
```

### 4. 测试API

```bash
# 运行测试脚本
python test_api.py

# 或手动测试
curl -X GET "http://localhost:5000/api/health"
```

## 🔑 API使用示例

### 基本认证

```bash
# 方式1: 请求头
curl -H "X-API-Key: your-api-key" \
     -X POST "http://localhost:5000/api/search" \
     -d '{"text": "搜索描述"}'

# 方式2: URL参数
curl -X POST "http://localhost:5000/api/search?api_key=your-api-key" \
     -d '{"text": "搜索描述"}'
```

### 完整流程

```python
import requests

# 1. 搜索媒体
response = requests.post(
    "http://localhost:5000/api/search",
    headers={"X-API-Key": "your-api-key"},
    json={"text": "一只可爱的小猫", "match_count": 5}
)
task_id = response.json()["task_id"]

# 2. 等待完成
while True:
    status = requests.get(
        f"http://localhost:5000/api/status/{task_id}",
        headers={"X-API-Key": "your-api-key"}
    ).json()
    
    if status["status"] == "completed":
        break
    elif status["status"] == "error":
        print("搜索失败")
        break
    
    time.sleep(2)

# 3. 获取结果
media_list = status["data"]["media_list"]
print(f"找到 {len(media_list)} 个匹配的媒体")

# 4. 下载文件
for media in media_list:
    download_url = f"http://localhost:5000/api/download-direct/{media['id']}"
    # 使用download_url下载文件
```

## 🛠️ 部署选项

### Docker部署（推荐）

```bash
# 使用Docker Compose
docker-compose up -d

# 检查状态
docker-compose ps
docker-compose logs -f
```

### 直接部署

```bash
# 设置环境变量
export SECRET_KEY="your-secret-key"
export API_KEYS="your-api-key-1,your-api-key-2"
# ... 其他环境变量

# 启动服务
python app.py
```

### 云服务部署

- **AWS EC2**: 使用Docker或直接部署
- **Google Cloud**: Compute Engine + Docker
- **Azure**: 虚拟机 + Docker
- **容器服务**: ECS、GKE、AKS等

## 🔒 安全配置

### API密钥管理

```bash
# 设置多个API密钥
export API_KEYS="key1,key2,key3"

# 或使用环境变量文件
echo "API_KEYS=key1,key2,key3" >> .env
```

### 频率限制

- 默认限制：每小时100次调用
- 可配置：通过环境变量调整
- 自动重置：每小时重置计数器

### 网络安全

```bash
# 配置防火墙
sudo ufw allow 5000
sudo ufw enable

# 使用HTTPS（推荐）
# 配置Nginx反向代理 + SSL证书
```

## 📊 监控和维护

### 日志查看

```bash
# 应用日志
tail -f app.log

# Docker日志
docker-compose logs -f

# 系统日志
journalctl -u film-media-api -f
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/api/health

# 检查API信息
curl http://localhost:5000/api/info
```

### 性能监控

```bash
# 监控资源使用
htop
docker stats

# 监控网络连接
netstat -tulpn | grep :5000
```

## 🐛 故障排除

### 常见问题

1. **API密钥无效**
   - 检查环境变量API_KEYS配置
   - 确认请求头X-API-Key正确

2. **频率限制**
   - 检查每小时调用次数
   - 等待重置时间或调整限制

3. **服务无法启动**
   - 检查环境变量配置
   - 查看错误日志
   - 验证端口占用

4. **文件下载失败**
   - 检查AWS S3配置
   - 验证文件权限
   - 查看S3日志

### 调试命令

```bash
# 检查服务状态
systemctl status film-media-api

# 查看详细日志
journalctl -u film-media-api -f

# 测试API连接
curl -X GET "http://localhost:5000/api/health"

# 检查端口占用
netstat -tulpn | grep :5000
```

## 📈 性能优化

### 1. 缓存优化
- 文本向量缓存（1小时TTL）
- API响应缓存
- 静态文件缓存

### 2. 并发处理
- 异步任务处理
- 多线程下载
- 连接池管理

### 3. 资源优化
- 内存使用监控
- 磁盘空间管理
- 网络带宽优化

## 🔄 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建（Docker）
docker-compose build
docker-compose up -d

# 重启服务
systemctl restart film-media-api
```

### 定期维护

- 清理旧日志文件
- 更新依赖包
- 检查安全补丁
- 监控资源使用

## 📞 技术支持

### 文档资源
- [API文档](API_DOCUMENTATION.md)
- [部署指南](DEPLOYMENT.md)
- [测试脚本](test_api.py)

### 联系方式
如有问题，请联系开发团队或查看项目文档。

## 🎯 总结

通过本方案，您已经成功将敏感配置的脚本封装成了安全的REST API：

✅ **安全性**: API密钥认证 + 频率限制  
✅ **易用性**: 完整的文档和测试工具  
✅ **可扩展性**: 支持多种部署方式  
✅ **监控性**: 详细的日志和健康检查  
✅ **维护性**: 清晰的错误处理和故障排除  

现在外部人员可以通过简单的API调用使用您的服务，而无需了解底层的敏感配置！
