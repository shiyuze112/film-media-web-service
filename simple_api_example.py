#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 Film Media Search API 使用示例
只需要 text 和 match_count 参数，支持下载到本地目录
"""

import requests
import time
import os
from typing import List, Dict, Any

class SimpleFilmMediaAPI:
    """简化版 Film Media Search API 客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def search_media(self, text: str, match_count: int = 5) -> Dict[str, Any]:
        """
        搜索媒体文件
        
        Args:
            text: 搜索的文本描述
            match_count: 返回的最大结果数量，默认5
            
        Returns:
            Dict: 包含task_id的响应
        """
        url = f"{self.base_url}/api/search"
        data = {
            'text': text,
            'match_count': match_count
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 任务状态信息
        """
        url = f"{self.base_url}/api/status/{task_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），默认300秒
            
        Returns:
            Dict: 完成的任务状态
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if status['status'] == 'completed':
                return status
            elif status['status'] == 'error':
                raise Exception(f"任务失败: {status['message']}")
            
            print(f"任务状态: {status['status']}, 进度: {status['progress']}%")
            time.sleep(2)
        
        raise Exception("任务超时")
    
    def download_media_to_local(self, media_list: List[Dict], download_dir: str = "downloads") -> Dict[str, Any]:
        """
        下载媒体文件到本地目录
        
        Args:
            media_list: 媒体列表，包含id和key字段
            download_dir: 本地下载目录，默认"downloads"
            
        Returns:
            Dict: 下载结果信息
        """
        url = f"{self.base_url}/api/download-to-local"
        data = {
            'media_list': media_list,
            'download_dir': download_dir
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def search_and_download(self, text: str, match_count: int = 5, download_dir: str = "downloads") -> Dict[str, Any]:
        """
        搜索并下载媒体文件的完整流程
        
        Args:
            text: 搜索的文本描述
            match_count: 返回的最大结果数量
            download_dir: 本地下载目录
            
        Returns:
            Dict: 包含搜索结果和下载结果的完整信息
        """
        print(f"🔍 搜索媒体: '{text}'")
        
        # 1. 搜索媒体
        search_result = self.search_media(text, match_count)
        task_id = search_result['task_id']
        print(f"✅ 搜索任务已创建: {task_id}")
        
        # 2. 等待任务完成
        print("⏳ 等待搜索完成...")
        status = self.wait_for_completion(task_id)
        
        if status['status'] != 'completed':
            raise Exception(f"搜索失败: {status.get('message', '未知错误')}")
        
        # 3. 获取媒体列表
        media_list = status['data']['media_list']
        print(f"✅ 找到 {len(media_list)} 个匹配的媒体")
        
        if not media_list:
            return {
                'search_result': status,
                'download_result': None,
                'message': '未找到匹配的媒体'
            }
        
        # 4. 下载媒体文件
        print(f"📥 开始下载到目录: {download_dir}")
        download_result = self.download_media_to_local(media_list, download_dir)
        
        print(f"✅ 下载完成:")
        print(f"   成功下载: {download_result['successful_downloads']} 个文件")
        print(f"   失败: {download_result['failed_count']} 个文件")
        
        return {
            'search_result': status,
            'download_result': download_result,
            'message': '搜索和下载完成'
        }

def main():
    """主函数 - 使用示例"""
    print("🎬 Film Media Search API 简化版使用示例")
    print("=" * 50)
    
    # 配置
    base_url = input("请输入API基础URL (默认: http://localhost:5000): ").strip()
    if not base_url:
        base_url = "http://localhost:5000"
    
    api_key = input("请输入API密钥 (默认: demo-api-key-2024): ").strip()
    if not api_key:
        api_key = "demo-api-key-2024"
    
    search_text = input("请输入搜索文本 (默认: 一只可爱的小猫在花园里玩耍): ").strip()
    if not search_text:
        search_text = "一只可爱的小猫在花园里玩耍"
    
    match_count = input("请输入返回结果数量 (默认: 3): ").strip()
    try:
        match_count = int(match_count) if match_count else 3
    except ValueError:
        match_count = 3
    
    download_dir = input("请输入下载目录 (默认: downloads): ").strip()
    if not download_dir:
        download_dir = "downloads"
    
    print()
    print(f"配置信息:")
    print(f"  API URL: {base_url}")
    print(f"  API Key: {api_key}")
    print(f"  搜索文本: {search_text}")
    print(f"  结果数量: {match_count}")
    print(f"  下载目录: {download_dir}")
    print()
    
    try:
        # 创建API客户端
        api = SimpleFilmMediaAPI(base_url, api_key)
        
        # 执行搜索和下载
        result = api.search_and_download(
            text=search_text,
            match_count=match_count,
            download_dir=download_dir
        )
        
        # 显示结果
        print("\n📋 搜索结果:")
        if result['search_result']['data']['media_list']:
            for i, media in enumerate(result['search_result']['data']['media_list']):
                print(f"  {i+1}. ID: {media['id']}")
                print(f"     文件: {media['key']}")
                print(f"     观看链接: {media['watch_url'][:50]}...")
                print()
        
        # 显示下载结果
        if result['download_result']:
            print("📁 下载结果:")
            for file_info in result['download_result']['downloaded_files']:
                print(f"  ✅ {file_info['media_id']} -> {file_info['local_path']}")
                print(f"     文件大小: {file_info['file_size']} 字节")
                print()
            
            if result['download_result']['failed_downloads']:
                print("❌ 下载失败的文件:")
                for failed in result['download_result']['failed_downloads']:
                    print(f"  - {failed['media'].get('id', 'Unknown')}: {failed['error']}")
        
        print(f"\n🎉 {result['message']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
