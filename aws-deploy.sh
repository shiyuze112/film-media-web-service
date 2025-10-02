#!/bin/bash
# AWS EC2 部署脚本

echo "🚀 开始部署Film Media Web服务到AWS EC2..."

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 3. 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 安装Git
sudo apt install -y git

# 5. 克隆代码
git clone https://github.com/your-username/film-media-web-service.git
cd film-media-web-service

# 6. 创建环境变量文件
cat > .env << EOF
SECRET_KEY=your-production-secret-key-$(openssl rand -hex 32)
AZURE_OPENAI_API_KEY_EASTUS=your-azure-openai-api-key
AZURE_OPENAI_API_ENDPOINT_EASTUS=https://your-resource.openai.azure.com/
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-east-1
AWS_BUCKET=your-bucket-name
EOF

# 7. 构建和启动服务
sudo docker-compose up -d --build

# 8. 检查服务状态
sudo docker-compose ps

echo "✅ 部署完成！"
echo "🌐 服务地址: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
