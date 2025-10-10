# Film Media Search API 部署指南

## 概述

本文档介绍如何部署 Film Media Search API 到生产环境。支持多种部署方式，包括Docker、云服务等。

## 环境要求

### 系统要求
- Python 3.11+
- 至少 2GB RAM
- 至少 10GB 存储空间
- 网络访问权限（用于访问Azure OpenAI和AWS S3）

### 依赖服务
- Azure OpenAI 服务
- AWS S3 存储
- 域名（可选，用于HTTPS）

## 部署方式

### 1. Docker 部署（推荐）

#### 使用 Docker Compose

1. **克隆代码**
   ```bash
   git clone <your-repo-url>
   cd film-media-web-service
   ```

2. **配置环境变量**
   ```bash
   cp env.example .env
   # 编辑 .env 文件，填入实际配置
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **检查服务状态**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

#### 使用 Docker 命令

1. **构建镜像**
   ```bash
   docker build -t film-media-api .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name film-media-api \
     -p 5000:5000 \
     -e SECRET_KEY=your-secret-key \
     -e API_KEYS=your-api-key-1,your-api-key-2 \
     -e AZURE_OPENAI_API_KEY_EASTUS=your-azure-key \
     -e AZURE_OPENAI_API_ENDPOINT_EASTUS=your-endpoint \
     -e AWS_ACCESS_KEY_ID=your-aws-key \
     -e AWS_SECRET_ACCESS_KEY=your-aws-secret \
     -e AWS_REGION=ap-east-1 \
     -e AWS_BUCKET=your-bucket \
     -v $(pwd)/downloads:/app/downloads \
     -v $(pwd)/logs:/app/logs \
     film-media-api
   ```

### 2. 直接部署

#### 系统要求
- Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+
- Python 3.11+
- pip

#### 部署步骤

1. **安装依赖**
   ```bash
   # 安装Python依赖
   pip install -r requirements.txt
   
   # 安装系统依赖（如果需要）
   sudo apt-get update
   sudo apt-get install -y curl
   ```

2. **配置环境变量**
   ```bash
   export SECRET_KEY="your-secret-key"
   export API_KEYS="your-api-key-1,your-api-key-2"
   export AZURE_OPENAI_API_KEY_EASTUS="your-azure-key"
   export AZURE_OPENAI_API_ENDPOINT_EASTUS="your-endpoint"
   export AWS_ACCESS_KEY_ID="your-aws-key"
   export AWS_SECRET_ACCESS_KEY="your-aws-secret"
   export AWS_REGION="ap-east-1"
   export AWS_BUCKET="your-bucket"
   ```

3. **创建必要目录**
   ```bash
   mkdir -p downloads logs
   ```

4. **启动服务**
   ```bash
   python app.py
   ```

### 3. 使用进程管理器（生产环境推荐）

#### 使用 systemd

1. **创建服务文件**
   ```bash
   sudo nano /etc/systemd/system/film-media-api.service
   ```

2. **服务配置**
   ```ini
   [Unit]
   Description=Film Media Search API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/film-media-web-service
   Environment=SECRET_KEY=your-secret-key
   Environment=API_KEYS=your-api-key-1,your-api-key-2
   Environment=AZURE_OPENAI_API_KEY_EASTUS=your-azure-key
   Environment=AZURE_OPENAI_API_ENDPOINT_EASTUS=your-endpoint
   Environment=AWS_ACCESS_KEY_ID=your-aws-key
   Environment=AWS_SECRET_ACCESS_KEY=your-aws-secret
   Environment=AWS_REGION=ap-east-1
   Environment=AWS_BUCKET=your-bucket
   Environment=PORT=5000
   Environment=HOST=0.0.0.0
   ExecStart=/usr/bin/python3 app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **启动服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable film-media-api
   sudo systemctl start film-media-api
   sudo systemctl status film-media-api
   ```

#### 使用 PM2

1. **安装 PM2**
   ```bash
   npm install -g pm2
   ```

2. **创建配置文件**
   ```bash
   nano ecosystem.config.js
   ```

3. **PM2 配置**
   ```javascript
   module.exports = {
     apps: [{
       name: 'film-media-api',
       script: 'app.py',
       interpreter: 'python3',
       env: {
         SECRET_KEY: 'your-secret-key',
         API_KEYS: 'your-api-key-1,your-api-key-2',
         AZURE_OPENAI_API_KEY_EASTUS: 'your-azure-key',
         AZURE_OPENAI_API_ENDPOINT_EASTUS: 'your-endpoint',
         AWS_ACCESS_KEY_ID: 'your-aws-key',
         AWS_SECRET_ACCESS_KEY: 'your-aws-secret',
         AWS_REGION: 'ap-east-1',
         AWS_BUCKET: 'your-bucket',
         PORT: 5000,
         HOST: '0.0.0.0'
       },
       instances: 1,
       exec_mode: 'fork',
       watch: false,
       max_memory_restart: '1G',
       error_file: './logs/err.log',
       out_file: './logs/out.log',
       log_file: './logs/combined.log',
       time: true
     }]
   };
   ```

4. **启动服务**
   ```bash
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup
   ```

## 云服务部署

### 1. AWS EC2 部署

1. **创建 EC2 实例**
   - 选择 Ubuntu 20.04 LTS
   - 实例类型：t3.medium 或更高
   - 安全组：开放端口 5000

2. **安装 Docker**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   ```

3. **部署应用**
   ```bash
   git clone <your-repo-url>
   cd film-media-web-service
   cp env.example .env
   # 编辑 .env 文件
   docker-compose up -d
   ```

### 2. Google Cloud Platform 部署

1. **创建 Compute Engine 实例**
   ```bash
   gcloud compute instances create film-media-api \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-medium \
     --tags=http-server,https-server
   ```

2. **配置防火墙**
   ```bash
   gcloud compute firewall-rules create allow-film-media-api \
     --allow tcp:5000 \
     --source-ranges 0.0.0.0/0 \
     --target-tags http-server
   ```

3. **部署应用**（同AWS步骤）

### 3. Azure 部署

1. **创建虚拟机**
   - 选择 Ubuntu Server 20.04 LTS
   - 大小：Standard_B2s 或更高

2. **配置网络安全组**
   - 添加入站规则：端口 5000，源：Any

3. **部署应用**（同AWS步骤）

### 4. 使用容器服务

#### AWS ECS

1. **创建任务定义**
   ```json
   {
     "family": "film-media-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "film-media-api",
         "image": "your-account.dkr.ecr.region.amazonaws.com/film-media-api:latest",
         "portMappings": [
           {
             "containerPort": 5000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "SECRET_KEY",
             "value": "your-secret-key"
           }
         ],
         "secrets": [
           {
             "name": "API_KEYS",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:api-keys"
           }
         ]
       }
     ]
   }
   ```

2. **创建服务**
   ```bash
   aws ecs create-service \
     --cluster your-cluster \
     --service-name film-media-api \
     --task-definition film-media-api:1 \
     --desired-count 1 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

## 配置 HTTPS

### 使用 Nginx 反向代理

1. **安装 Nginx**
   ```bash
   sudo apt-get install nginx
   ```

2. **配置 Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/film-media-api
   ```

3. **Nginx 配置**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **启用站点**
   ```bash
   sudo ln -s /etc/nginx/sites-available/film-media-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **配置 SSL**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## 监控和日志

### 1. 日志管理

```bash
# 查看应用日志
tail -f app.log

# 使用 Docker 查看日志
docker-compose logs -f

# 使用 PM2 查看日志
pm2 logs film-media-api
```

### 2. 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/api/health

# 使用 Docker 健康检查
docker ps
```

### 3. 性能监控

```bash
# 监控资源使用
htop
docker stats

# 监控网络连接
netstat -tulpn | grep :5000
```

## 安全配置

### 1. 防火墙设置

```bash
# Ubuntu/Debian
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 2. API 密钥管理

- 使用强密码生成API密钥
- 定期轮换API密钥
- 使用环境变量或密钥管理服务存储敏感信息

### 3. 网络安全

- 使用HTTPS加密传输
- 配置适当的CORS策略
- 实施IP白名单（如需要）

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查环境变量配置
   - 查看日志文件
   - 验证端口占用

2. **API调用失败**
   - 检查API密钥配置
   - 验证网络连接
   - 查看错误日志

3. **文件下载失败**
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

## 备份和恢复

### 1. 数据备份

```bash
# 备份配置文件
cp .env .env.backup

# 备份日志文件
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# 备份下载文件
tar -czf downloads-backup-$(date +%Y%m%d).tar.gz downloads/
```

### 2. 恢复步骤

```bash
# 恢复配置文件
cp .env.backup .env

# 恢复数据文件
tar -xzf logs-backup-YYYYMMDD.tar.gz
tar -xzf downloads-backup-YYYYMMDD.tar.gz

# 重启服务
systemctl restart film-media-api
```

## 更新和维护

### 1. 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像（Docker）
docker-compose build
docker-compose up -d

# 重启服务（直接部署）
systemctl restart film-media-api
```

### 2. 定期维护

- 清理旧日志文件
- 更新依赖包
- 检查安全补丁
- 监控资源使用情况

## 联系支持

如有部署问题，请联系技术支持团队。