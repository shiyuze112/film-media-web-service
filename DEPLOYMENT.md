# Film Media Web 服务部署指南

## 🚀 快速部署方案

### 方案1：Railway部署（推荐）

1. **注册Railway账号**
   - 访问 https://railway.app
   - 使用GitHub账号登录

2. **部署步骤**
   ```bash
   # 1. 将代码推送到GitHub
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/film-media-web-service.git
   git push -u origin main
   
   # 2. 在Railway中连接GitHub仓库
   # 3. 设置环境变量
   # 4. 自动部署
   ```

3. **环境变量配置**
   ```
   SECRET_KEY=your-production-secret-key
   AZURE_OPENAI_API_KEY_EASTUS=your-azure-key
   AZURE_OPENAI_API_ENDPOINT_EASTUS=https://your-resource.openai.azure.com/
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_REGION=ap-east-1
   AWS_BUCKET=your-bucket-name
   ```

### 方案2：Docker部署

1. **本地构建和测试**
   ```bash
   # 构建镜像
   docker build -t film-media-web .
   
   # 运行容器
   docker run -p 8080:8080 --env-file .env film-media-web
   ```

2. **部署到云服务器**
   ```bash
   # 上传到云服务器
   scp -r . user@your-server:/home/user/film-media-web-service
   
   # 在服务器上运行
   docker-compose up -d
   ```

### 方案3：传统VPS部署

1. **服务器准备**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip nginx git
   
   # CentOS/RHEL
   sudo yum update
   sudo yum install python3 python3-pip nginx git
   ```

2. **应用部署**
   ```bash
   # 克隆代码
   git clone https://github.com/your-username/film-media-web-service.git
   cd film-media-web-service
   
   # 安装依赖
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   
   # 配置环境变量
   cp env.example .env
   nano .env
   
   # 启动服务
   gunicorn -w 4 -b 0.0.0.0:8080 app:app
   ```

3. **Nginx配置**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## 🔧 生产环境优化

### 1. 安全配置
- 使用强密码的SECRET_KEY
- 配置HTTPS证书
- 设置防火墙规则
- 定期更新依赖

### 2. 性能优化
- 使用CDN加速静态资源
- 配置Redis缓存
- 设置负载均衡
- 监控服务状态

### 3. 监控和日志
- 配置日志轮转
- 设置健康检查
- 监控资源使用
- 设置告警通知

## 📱 域名和SSL

### 1. 域名配置
- 购买域名
- 配置DNS解析
- 设置A记录指向服务器IP

### 2. SSL证书
```bash
# 使用Let's Encrypt免费证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🚨 注意事项

1. **环境变量安全**
   - 不要将.env文件提交到Git
   - 使用环境变量管理敏感信息
   - 定期轮换API密钥

2. **资源限制**
   - 设置文件上传大小限制
   - 配置请求频率限制
   - 监控磁盘空间使用

3. **备份策略**
   - 定期备份数据库
   - 备份配置文件
   - 测试恢复流程

## 🎯 推荐部署流程

1. **开发环境**：本地测试 ✅
2. **测试环境**：Railway免费版
3. **生产环境**：云服务器 + 域名 + SSL

选择最适合您需求的方案开始部署！
