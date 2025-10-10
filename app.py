#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Film Media 匹配 Web 服务
支持文本转向量、媒体匹配和文件下载的 Web 界面
"""

import asyncio
import os
import uuid
import hashlib
import logging
from datetime import timedelta, datetime
from typing import List, Optional, Dict, Any
from cachetools import TTLCache
from langchain_openai import AzureOpenAIEmbeddings
import boto3
from one2x_sdk.medeo.core_api.core_api_client import CoreApiClient
from flask import Flask, render_template, request, jsonify, send_file, redirect, g
from flask_cors import CORS
import threading
import time
from dotenv import load_dotenv
from functools import wraps

# 加载环境变量
load_dotenv()

# 配置日志（Vercel兼容）
if os.environ.get('VERCEL'):
    # Vercel环境：只使用控制台日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
else:
    # 本地环境：使用文件和控制台日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 启用CORS
CORS(app)

# 全局错误处理器
@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({
        'error': 'Bad Request',
        'message': '请求参数错误',
        'timestamp': datetime.now().isoformat()
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized: {error}")
    return jsonify({
        'error': 'Unauthorized',
        'message': '未授权访问',
        'timestamp': datetime.now().isoformat()
    }), 401

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {error}")
    return jsonify({
        'error': 'Not Found',
        'message': '资源不存在',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(429)
def too_many_requests(error):
    logger.warning(f"Too many requests: {error}")
    return jsonify({
        'error': 'Too Many Requests',
        'message': '请求频率超限',
        'timestamp': datetime.now().isoformat()
    }), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': '服务器内部错误',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': '服务器内部错误',
        'timestamp': datetime.now().isoformat()
    }), 500

# 全局变量存储任务状态
task_status = {}

# API认证和频率限制
api_keys = {}  # 存储有效的API密钥
rate_limit_cache = TTLCache(maxsize=1000, ttl=timedelta(hours=1).total_seconds())

def init_api_keys():
    """初始化API密钥"""
    # 从环境变量读取API密钥，支持多个密钥
    api_key_env = os.getenv('API_KEYS', '')
    if api_key_env:
        keys = api_key_env.split(',')
        for key in keys:
            key = key.strip()
            if key:
                api_keys[key] = {
                    'name': f'key_{hashlib.md5(key.encode()).hexdigest()[:8]}',
                    'created_at': datetime.now(),
                    'requests_count': 0
                }
    else:
        # 如果没有设置环境变量，生成一个默认密钥
        default_key = 'demo-api-key-2024'
        api_keys[default_key] = {
            'name': 'demo_key',
            'created_at': datetime.now(),
            'requests_count': 0
        }
        print(f"警告: 使用默认API密钥，请设置环境变量API_KEYS: {default_key}")

def verify_api_key(api_key: str) -> bool:
    """验证API密钥"""
    return api_key in api_keys

def check_rate_limit(api_key: str, max_requests: int = 100) -> bool:
    """检查API调用频率限制"""
    key = f"rate_limit_{api_key}"
    current_time = time.time()
    
    if key not in rate_limit_cache:
        rate_limit_cache[key] = {'count': 0, 'reset_time': current_time + 3600}  # 1小时重置
    
    rate_data = rate_limit_cache[key]
    
    # 如果超过重置时间，重置计数器
    if current_time > rate_data['reset_time']:
        rate_data['count'] = 0
        rate_data['reset_time'] = current_time + 3600
    
    # 检查是否超过限制
    if rate_data['count'] >= max_requests:
        return False
    
    rate_data['count'] += 1
    return True

def require_api_key(f):
    """API密钥验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'error': '缺少API密钥',
                'message': '请在请求头中添加 X-API-Key 或使用 api_key 参数'
            }), 401
        
        if not verify_api_key(api_key):
            return jsonify({
                'error': '无效的API密钥',
                'message': '请检查您的API密钥是否正确'
            }), 401
        
        if not check_rate_limit(api_key):
            return jsonify({
                'error': 'API调用频率超限',
                'message': '每小时最多允许100次API调用，请稍后再试'
            }), 429
        
        g.api_key = api_key
        return f(*args, **kwargs)
    
    return decorated_function

class EmbeddingService:
    """文本转向量服务"""
    
    def __init__(self):
        api_key = os.getenv("AZURE_OPENAI_API_KEY_EASTUS")
        endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT_EASTUS")
        
        if not api_key or not endpoint:
            raise ValueError("缺少必要的环境变量: AZURE_OPENAI_API_KEY_EASTUS 或 AZURE_OPENAI_API_ENDPOINT_EASTUS")
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-3-small",
            openai_api_key=api_key,
            azure_endpoint=endpoint,
            dimensions=512,
        )
        self.embedding_cache = TTLCache(
            maxsize=1000, ttl=timedelta(hours=1).total_seconds()
        )
    
    async def text_to_embedding(self, text: str) -> Optional[List[float]]:
        """将文本转换为向量"""
        try:
            if text in self.embedding_cache:
                return self.embedding_cache[text]
            
            embedding = await self.embeddings.aembed_query(text)
            self.embedding_cache[text] = embedding
            return embedding
        except Exception as e:
            print(f"文本转向量失败: {str(e)}")
            return None

class S3Downloader:
    """AWS S3 文件下载器"""
    
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "ap-east-1")
        self.bucket_name = os.getenv("AWS_BUCKET", "one2x-share")
        
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("缺少必要的 AWS 环境变量")
        
        from botocore.config import Config
        
        if self.aws_region == 'ap-east-1':
            # ap-east-1需要特殊配置
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                endpoint_url=f'https://s3.{self.aws_region}.amazonaws.com',
                config=Config(s3={'addressing_style': 'virtual'})
            )
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
    
    async def download_file(self, key: str, local_path: str) -> bool:
        """从 S3 下载文件"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return True
        except Exception as e:
            print(f"S3 下载失败: {str(e)}")
            return False
    
    async def download_media_files(self, media_list: List[dict], download_dir: str) -> List[str]:
        """批量下载媒体文件"""
        downloaded_files = []
        
        print(f"开始下载 {len(media_list)} 个媒体文件")
        
        for i, media in enumerate(media_list):
            if 'key' not in media:
                print(f"媒体 {i+1} 缺少key字段: {media}")
                continue
            
            key = media['key']
            media_id = media.get('id', f'media_{i+1}')
            file_extension = os.path.splitext(key)[1] or '.mp4'
            local_filename = f"{media_id}{file_extension}"
            local_path = os.path.join(download_dir, local_filename)
            
            print(f"下载文件 {i+1}: {key} -> {local_path}")
            success = await self.download_file(key, local_path)
            if success:
                downloaded_files.append(local_path)
                print(f"下载成功: {local_path}")
            else:
                print(f"下载失败: {key}")
        
        print(f"下载完成，成功下载 {len(downloaded_files)} 个文件")
        return downloaded_files

class FilmMediaService:
    """Film Media 匹配服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.s3_downloader = S3Downloader()
        self.core_api_client = CoreApiClient(
            base_url="https://medeo-core-api.test-us.one2x.ai", 
            token="token",
            enable_requests=True
        )
    
    async def search_media(self, text: str, match_threshold: float = 0, match_count: int = 5) -> Dict[str, Any]:
        """搜索匹配的媒体"""
        try:
            # 文本转向量
            embedding = await self.embedding_service.text_to_embedding(text)
            if embedding is None:
                return {"error": "文本转向量失败"}
            
            # 调用API
            test_data = {
                "query_embedding": embedding,
                "match_threshold": match_threshold,
                "match_count": match_count
            }
            
            response = self.core_api_client.request(
                'POST', 
                'api/media/match-film-media', 
                json=test_data
            )
            
            return {"success": True, "media_list": response}
            
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}"}
    
    async def download_media(self, media_list: List[dict], task_id: str) -> Dict[str, Any]:
        """下载媒体文件"""
        try:
            download_dir = os.path.join("downloads", task_id)
            downloaded_files = await self.s3_downloader.download_media_files(media_list, download_dir)
            
            return {
                "success": True, 
                "downloaded_files": downloaded_files,
                "download_dir": download_dir
            }
        except Exception as e:
            return {"error": f"下载失败: {str(e)}"}

# 创建服务实例
film_media_service = FilmMediaService()

def update_task_status(task_id: str, status: str, progress: int = 0, message: str = "", data: Any = None):
    """更新任务状态"""
    task_status[task_id] = {
        "status": status,  # pending, processing, completed, error
        "progress": progress,
        "message": message,
        "data": data,
        "created_at": time.time()
    }

async def process_search_task(task_id: str, text: str, match_threshold: float, match_count: int):
    """处理搜索任务"""
    try:
        update_task_status(task_id, "processing", 20, "正在将文本转换为向量...")
        
        # 搜索媒体
        result = await film_media_service.search_media(text, match_threshold, match_count)
        
        if "error" in result:
            update_task_status(task_id, "error", 0, result["error"])
            return
        
        media_list = result.get("media_list", [])
        update_task_status(task_id, "processing", 60, f"找到 {len(media_list)} 个匹配的媒体...")
        
        # 为每个媒体生成观看URL
        for media in media_list:
            try:
                # 生成观看URL
                s3_downloader = S3Downloader()
                s3_client = s3_downloader.s3_client
                
                bucket_name = os.environ.get('AWS_BUCKET', 'one2x-share')
                key = media['key']
                
                # 生成预签名URL用于观看
                watch_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': key},
                    ExpiresIn=3600
                )
                
                media['watch_url'] = watch_url
                print(f"为媒体 {media['id']} 生成观看URL: {watch_url[:100]}...")
                
            except Exception as e:
                print(f"生成观看URL失败: {str(e)}")
                media['watch_url'] = f"/api/download-direct/{media['id']}"
        
        # 直接返回媒体列表，不预下载文件
        update_task_status(task_id, "completed", 100, "处理完成", {
            "media_list": media_list
        })
        
    except Exception as e:
        update_task_status(task_id, "error", 0, f"处理失败: {str(e)}")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/info')
def api_info():
    """API信息接口"""
    return jsonify({
        'service': 'Film Media Search API',
        'version': '1.0.0',
        'description': '基于文本转向量的媒体搜索和下载服务',
        'endpoints': {
            'search': '/api/search - 搜索媒体',
            'status': '/api/status/<task_id> - 获取任务状态',
            'download_to_local': '/api/download-to-local - 下载媒体文件到本地',
            'download_direct': '/api/download-direct/<media_id> - 直接下载媒体文件',
            'info': '/api/info - API信息',
            'health': '/api/health - 健康检查'
        },
        'authentication': {
            'method': 'API Key',
            'header': 'X-API-Key',
            'parameter': 'api_key'
        },
        'rate_limit': {
            'max_requests_per_hour': 100,
            'reset_interval': '1小时'
        }
    })

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    try:
        # 检查必要的环境变量
        required_vars = [
            'AZURE_OPENAI_API_KEY_EASTUS',
            'AZURE_OPENAI_API_ENDPOINT_EASTUS',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            return jsonify({
                'status': 'unhealthy',
                'message': f'缺少环境变量: {", ".join(missing_vars)}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return jsonify({
            'status': 'healthy',
            'message': '服务运行正常',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'健康检查失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/search', methods=['POST'])
@require_api_key
def search_media():
    """搜索媒体接口"""
    try:
        logger.info(f"收到搜索请求，API Key: {g.api_key[:8]}...")
        
        data = request.get_json()
        text = data.get('text', '').strip()
        match_count = int(data.get('match_count', 5))
        
        logger.info(f"搜索参数: text='{text}', count={match_count}")
        
        if not text:
            logger.warning("搜索请求缺少文本参数")
            return jsonify({"error": "请输入搜索文本"}), 400
        
        # 检查环境变量
        required_env_vars = [
            'AZURE_OPENAI_API_KEY_EASTUS',
            'AZURE_OPENAI_API_ENDPOINT_EASTUS',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'AWS_BUCKET'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"缺少环境变量: {missing_vars}")
            return jsonify({"error": f"缺少环境变量: {', '.join(missing_vars)}"}), 500
        
        # 创建任务
        task_id = str(uuid.uuid4())
        logger.info(f"创建搜索任务: {task_id}")
        update_task_status(task_id, "pending", 0, "任务已创建，等待处理...")
        
        # 异步处理任务
        def run_task():
            try:
                logger.info(f"开始处理任务: {task_id}")
                asyncio.run(process_search_task(task_id, text, 0.0, match_count))
                logger.info(f"任务处理完成: {task_id}")
            except Exception as e:
                logger.error(f"任务处理失败: {task_id}, 错误: {str(e)}", exc_info=True)
                update_task_status(task_id, "error", 0, f"处理失败: {str(e)}")
        
        thread = threading.Thread(target=run_task)
        thread.start()
        
        logger.info(f"任务已提交: {task_id}")
        return jsonify({"task_id": task_id})
        
    except Exception as e:
        logger.error(f"搜索接口错误: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<task_id>')
@require_api_key
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in task_status:
        return jsonify({"error": "任务不存在"}), 404
    
    return jsonify(task_status[task_id])

@app.route('/api/download/<task_id>/<filename>')
def download_file(task_id, filename):
    """下载文件"""
    try:
        file_path = os.path.join("downloads", task_id, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/downloads/<task_id>')
def list_downloads(task_id):
    """列出下载的文件"""
    try:
        download_dir = os.path.join("downloads", task_id)
        if not os.path.exists(download_dir):
            return jsonify({"files": []})
        
        files = []
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "download_url": f"/api/download/{task_id}/{filename}"
                })
        
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-direct/<media_id>')
def download_direct(media_id):
    """直接从S3下载文件"""
    try:
        print(f"开始处理下载请求，媒体ID: {media_id}")
        
        # 从任务状态中查找对应的媒体信息
        media_info = None
        print(f"当前任务状态数量: {len(task_status)}")
        
        for task_id, task_data in task_status.items():
            print(f"检查任务 {task_id}: {task_data.get('status')}")
            if task_data.get('status') == 'completed' and task_data.get('data', {}).get('media_list'):
                print(f"任务 {task_id} 有媒体列表: {len(task_data['data']['media_list'])} 个")
                for media in task_data['data']['media_list']:
                    print(f"检查媒体: {media.get('id')}")
                    if media.get('id') == media_id:
                        media_info = media
                        print(f"找到匹配的媒体信息: {media_info}")
                        break
                if media_info:
                    break
        
        if not media_info:
            print("未找到媒体信息")
            return jsonify({"error": "媒体信息不存在"}), 404
        
        key = media_info['key']
        
        print(f"准备下载文件: {key}")
        
        # 检查AWS环境变量
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'ap-east-1')
        aws_bucket = os.environ.get('AWS_BUCKET', 'one2x-share')
        
        print("AWS环境变量检查:")
        print(f"  ACCESS_KEY_ID: {'已设置' if aws_access_key else '未设置'}")
        print(f"  SECRET_ACCESS_KEY: {'已设置' if aws_secret_key else '未设置'}")
        print(f"  REGION: {aws_region}")
        print(f"  BUCKET: {aws_bucket}")
        
        if not aws_access_key or not aws_secret_key:
            return jsonify({"error": "AWS环境变量未正确配置"}), 500
        
        # 直接从S3生成预签名URL进行下载
        try:
            # 直接创建S3客户端，避免使用S3Downloader类
            import boto3
            from botocore.config import Config
            
            # 为ap-east-1区域配置正确的端点
            region = os.environ.get('AWS_REGION', 'ap-east-1')
            if region == 'ap-east-1':
                # ap-east-1需要特殊配置
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=region,
                    endpoint_url=f'https://s3.{region}.amazonaws.com',
                    config=Config(s3={'addressing_style': 'virtual'})
                )
            else:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=region
                )
            
            bucket_name = os.environ.get('AWS_BUCKET', 'one2x-share')
            print(f"S3客户端创建成功，bucket: {bucket_name}")
            
            # 生成预签名URL，有效期1小时（用于在线观看）
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name, 
                    'Key': key
                },
                ExpiresIn=3600
            )
            
            print(f"预签名URL生成成功: {presigned_url[:100]}...")
            
            # 重定向到预签名URL
            return redirect(presigned_url)
            
        except Exception as e:
            print(f"S3预签名URL生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"文件下载失败: {str(e)}"}), 500
        
    except Exception as e:
        print(f"下载直接API错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-to-local', methods=['POST'])
@require_api_key
def download_media_to_local():
    """下载媒体文件到本地目录"""
    try:
        logger.info(f"收到下载请求，API Key: {g.api_key[:8]}...")
        
        data = request.get_json()
        media_list = data.get('media_list', [])
        download_dir = data.get('download_dir', 'downloads')
        
        if not media_list:
            return jsonify({"error": "请提供媒体列表"}), 400
        
        logger.info(f"下载参数: 媒体数量={len(media_list)}, 目录={download_dir}")
        
        # 检查环境变量
        required_env_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'AWS_BUCKET'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"缺少环境变量: {missing_vars}")
            return jsonify({"error": f"缺少环境变量: {', '.join(missing_vars)}"}), 500
        
        # 创建下载目录
        os.makedirs(download_dir, exist_ok=True)
        
        # 下载文件
        downloaded_files = []
        failed_downloads = []
        
        for i, media in enumerate(media_list):
            try:
                if 'key' not in media:
                    logger.warning(f"媒体 {i+1} 缺少key字段: {media}")
                    failed_downloads.append({"media": media, "error": "缺少key字段"})
                    continue
                
                key = media['key']
                media_id = media.get('id', f'media_{i+1}')
                
                # 生成本地文件名
                file_extension = os.path.splitext(key)[1] or '.mp4'
                local_filename = f"{media_id}{file_extension}"
                local_path = os.path.join(download_dir, local_filename)
                
                logger.info(f"下载文件 {i+1}: {key} -> {local_path}")
                
                # 使用S3Downloader下载文件
                s3_downloader = S3Downloader()
                success = asyncio.run(s3_downloader.download_file(key, local_path))
                
                if success:
                    downloaded_files.append({
                        "media_id": media_id,
                        "local_path": local_path,
                        "file_size": os.path.getsize(local_path) if os.path.exists(local_path) else 0
                    })
                    logger.info(f"下载成功: {local_path}")
                else:
                    failed_downloads.append({"media": media, "error": "下载失败"})
                    logger.error(f"下载失败: {key}")
                    
            except Exception as e:
                logger.error(f"下载媒体 {i+1} 时出错: {str(e)}")
                failed_downloads.append({"media": media, "error": str(e)})
        
        result = {
            "success": True,
            "downloaded_files": downloaded_files,
            "failed_downloads": failed_downloads,
            "download_dir": download_dir,
            "total_files": len(media_list),
            "successful_downloads": len(downloaded_files),
            "failed_count": len(failed_downloads)
        }
        
        logger.info(f"下载完成: 成功={len(downloaded_files)}, 失败={len(failed_downloads)}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"下载接口错误: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-file/<media_id>')
def download_file_direct(media_id):
    """强制下载文件"""
    try:
        print(f"开始处理强制下载请求，媒体ID: {media_id}")
        
        # 从任务状态中查找对应的媒体信息
        media_info = None
        for task_id, task_data in task_status.items():
            if task_data.get('status') == 'completed' and task_data.get('data', {}).get('media_list'):
                for media in task_data['data']['media_list']:
                    if media.get('id') == media_id:
                        media_info = media
                        break
                if media_info:
                    break
        
        if not media_info:
            return jsonify({"error": "媒体信息不存在"}), 404
        
        key = media_info['key']
        file_extension = os.path.splitext(key)[1] or '.mp4'
        filename = f"{media_id}{file_extension}"
        
        # 检查AWS环境变量
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_bucket = os.environ.get('AWS_BUCKET', 'one2x-share')
        
        if not aws_access_key or not aws_secret_key:
            return jsonify({"error": "AWS环境变量未正确配置"}), 500
        
        # 生成强制下载的预签名URL
        try:
            import boto3
            from botocore.config import Config
            
            region = os.environ.get('AWS_REGION', 'ap-east-1')
            if region == 'ap-east-1':
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=region,
                    endpoint_url=f'https://s3.{region}.amazonaws.com',
                    config=Config(s3={'addressing_style': 'virtual'})
                )
            else:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=region
                )
            
            # 生成强制下载的预签名URL
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': aws_bucket, 
                    'Key': key,
                    'ResponseContentDisposition': f'attachment; filename="{filename}"'
                },
                ExpiresIn=3600
            )
            
            return redirect(presigned_url)
            
        except Exception as e:
            print(f"强制下载URL生成失败: {str(e)}")
            return jsonify({"error": f"文件下载失败: {str(e)}"}), 500
        
    except Exception as e:
        print(f"强制下载API错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 初始化API密钥（仅在非Vercel环境中）
if not os.environ.get('VERCEL'):
    try:
        init_api_keys()
    except Exception as e:
        print(f"API密钥初始化失败: {e}")

# 确保下载目录存在（仅在非Vercel环境中）
if not os.environ.get('VERCEL'):
    try:
        os.makedirs("downloads", exist_ok=True)
    except Exception as e:
        print(f"创建下载目录失败: {e}")

# 部署时间戳 - 用于触发重新部署
DEPLOYMENT_TIMESTAMP = "2024-01-15-15:30:00"

# Vercel WSGI 支持
def handler(request):
    """Vercel WSGI 处理器"""
    return app(request)

# 导出应用实例（Vercel需要）
application = app

if __name__ == '__main__':
    # 获取端口（Vercel会设置PORT环境变量）
    port = int(os.environ.get('PORT', 5000))
    
    # 启动服务
    app.run(debug=False, host='0.0.0.0', port=port)
