#!/bin/bash

# Film Media Search API 启动脚本

set -e

echo "🚀 启动 Film Media Search API..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要 $required_version 或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查环境变量
echo "🔍 检查环境变量..."

required_vars=(
    "SECRET_KEY"
    "API_KEYS"
    "AZURE_OPENAI_API_KEY_EASTUS"
    "AZURE_OPENAI_API_ENDPOINT_EASTUS"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_REGION"
    "AWS_BUCKET"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ 缺少以下环境变量:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请设置环境变量或创建 .env 文件"
    echo "参考 env.example 文件"
    exit 1
fi

echo "✅ 环境变量检查通过"

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p downloads logs
echo "✅ 目录创建完成"

# 检查依赖
echo "📦 检查Python依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 找不到 requirements.txt 文件"
    exit 1
fi

# 安装依赖（如果需要）
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 安装Python依赖..."
    pip3 install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖检查通过"
fi

# 检查端口占用
port=${PORT:-5000}
echo "🔍 检查端口 $port 占用情况..."

if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 $port 已被占用"
    echo "请停止占用端口的进程或使用其他端口"
    echo "设置环境变量 PORT=其他端口号"
    exit 1
fi

echo "✅ 端口 $port 可用"

# 启动服务
echo "🚀 启动服务..."
echo "   端口: $port"
echo "   主机: ${HOST:-0.0.0.0}"
echo "   环境: ${FLASK_ENV:-production}"
echo ""

# 设置默认值
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}
export FLASK_ENV=${FLASK_ENV:-production}

# 启动应用
python3 app.py
