#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Film Media 匹配 Web 服务
支持文本转向量、媒体匹配和文件下载的 Web 界面
"""

import asyncio
import os
import json
import uuid
from datetime import timedelta
from typing import List, Optional, Dict, Any
from cachetools import TTLCache
from langchain_openai import AzureOpenAIEmbeddings
import boto3
from botocore.exceptions import ClientError
from one2x_sdk.medeo.core_api.core_api_client import CoreApiClient
from flask import Flask, render_template, request, jsonify, send_file, session, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 启用CORS
CORS(app)

# 全局变量存储任务状态
task_status = {}

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

@app.route('/api/search', methods=['POST'])
def search_media():
    """搜索媒体接口"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        match_threshold = float(data.get('match_threshold', 0))
        match_count = int(data.get('match_count', 5))
        
        if not text:
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
            return jsonify({"error": f"缺少环境变量: {', '.join(missing_vars)}"}), 500
        
        # 创建任务
        task_id = str(uuid.uuid4())
        update_task_status(task_id, "pending", 0, "任务已创建，等待处理...")
        
        # 异步处理任务
        def run_task():
            asyncio.run(process_search_task(task_id, text, match_threshold, match_count))
        
        thread = threading.Thread(target=run_task)
        thread.start()
        
        return jsonify({"task_id": task_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<task_id>')
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
        file_extension = os.path.splitext(key)[1] or '.mp4'
        filename = f"{media_id}{file_extension}"
        
        print(f"准备下载文件: {key}")
        
        # 检查AWS环境变量
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'ap-east-1')
        aws_bucket = os.environ.get('AWS_BUCKET', 'one2x-share')
        
        print(f"AWS环境变量检查:")
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
            
            # 生成预签名URL，有效期1小时
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
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

if __name__ == '__main__':
    # 确保下载目录存在
    os.makedirs("downloads", exist_ok=True)
    
    # 获取端口（Vercel会设置PORT环境变量）
    port = int(os.environ.get('PORT', 5000))
    
    # 启动服务
    app.run(debug=False, host='0.0.0.0', port=port)
