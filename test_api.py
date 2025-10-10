#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Film Media Search API 测试脚本
用于测试API的各项功能
"""

import requests
import time
import json
from typing import Dict, Any

class FilmMediaAPITester:
    """API测试类"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def test_api_info(self) -> Dict[str, Any]:
        """测试API信息接口"""
        print("🔍 测试API信息接口...")
        try:
            response = requests.get(f"{self.base_url}/api/info")
            response.raise_for_status()
            result = response.json()
            print("✅ API信息获取成功")
            print(f"   服务: {result['service']}")
            print(f"   版本: {result['version']}")
            return result
        except Exception as e:
            print(f"❌ API信息获取失败: {e}")
            return {"error": str(e)}
    
    def test_health_check(self) -> Dict[str, Any]:
        """测试健康检查接口"""
        print("🔍 测试健康检查接口...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            result = response.json()
            print("✅ 健康检查通过")
            print(f"   状态: {result['status']}")
            print(f"   消息: {result['message']}")
            return result
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return {"error": str(e)}
    
    def test_search_media(self, text: str, match_threshold: float = 0.0, match_count: int = 3) -> Dict[str, Any]:
        """测试媒体搜索接口"""
        print(f"🔍 测试媒体搜索接口: '{text}'...")
        try:
            data = {
                'text': text,
                'match_threshold': match_threshold,
                'match_count': match_count
            }
            
            response = requests.post(
                f"{self.base_url}/api/search",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            if 'task_id' in result:
                print("✅ 搜索任务创建成功")
                print(f"   任务ID: {result['task_id']}")
                return result
            else:
                print(f"❌ 搜索任务创建失败: {result}")
                return result
                
        except Exception as e:
            print(f"❌ 媒体搜索失败: {e}")
            return {"error": str(e)}
    
    def test_get_task_status(self, task_id: str) -> Dict[str, Any]:
        """测试获取任务状态接口"""
        print(f"🔍 测试获取任务状态: {task_id}...")
        try:
            response = requests.get(
                f"{self.base_url}/api/status/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ 任务状态获取成功")
            print(f"   状态: {result['status']}")
            print(f"   进度: {result['progress']}%")
            print(f"   消息: {result['message']}")
            
            if result['status'] == 'completed' and result.get('data', {}).get('media_list'):
                media_list = result['data']['media_list']
                print(f"   找到 {len(media_list)} 个匹配的媒体:")
                for i, media in enumerate(media_list):
                    print(f"     {i+1}. ID: {media.get('id')}, Key: {media.get('key')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 获取任务状态失败: {e}")
            return {"error": str(e)}
    
    def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """等待任务完成"""
        print(f"⏳ 等待任务完成: {task_id}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.test_get_task_status(task_id)
            
            if status.get('status') == 'completed':
                print("✅ 任务完成")
                return status
            elif status.get('status') == 'error':
                print(f"❌ 任务失败: {status.get('message')}")
                return status
            
            print("   等待中...")
            time.sleep(3)
        
        print("❌ 任务超时")
        return {"error": "任务超时"}
    
    def test_download_media(self, media_id: str) -> bool:
        """测试媒体下载接口"""
        print(f"🔍 测试媒体下载: {media_id}...")
        try:
            response = requests.get(
                f"{self.base_url}/api/download-direct/{media_id}",
                headers=self.headers,
                allow_redirects=True
            )
            response.raise_for_status()
            
            print("✅ 媒体下载成功")
            print(f"   响应大小: {len(response.content)} 字节")
            return True
            
        except Exception as e:
            print(f"❌ 媒体下载失败: {e}")
            return False
    
    def run_full_test(self, search_text: str = "一只可爱的小猫在花园里玩耍") -> bool:
        """运行完整测试流程"""
        print("🚀 开始完整API测试流程")
        print("=" * 50)
        
        # 1. 测试API信息
        api_info = self.test_api_info()
        if "error" in api_info:
            return False
        
        print()
        
        # 2. 测试健康检查
        health = self.test_health_check()
        if "error" in health:
            return False
        
        print()
        
        # 3. 测试媒体搜索
        search_result = self.test_search_media(search_text)
        if "error" in search_result or "task_id" not in search_result:
            return False
        
        task_id = search_result['task_id']
        print()
        
        # 4. 等待任务完成
        completion_result = self.wait_for_completion(task_id)
        if "error" in completion_result:
            return False
        
        print()
        
        # 5. 测试媒体下载
        if completion_result.get('data', {}).get('media_list'):
            media_list = completion_result['data']['media_list']
            if media_list:
                media_id = media_list[0]['id']
                download_success = self.test_download_media(media_id)
                if not download_success:
                    return False
        
        print()
        print("🎉 所有测试完成!")
        return True

def main():
    """主函数"""
    print("Film Media Search API 测试工具")
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
    
    print()
    print(f"配置信息:")
    print(f"  API URL: {base_url}")
    print(f"  API Key: {api_key}")
    print(f"  搜索文本: {search_text}")
    print()
    
    # 创建测试器
    tester = FilmMediaAPITester(base_url, api_key)
    
    # 运行测试
    success = tester.run_full_test(search_text)
    
    if success:
        print("✅ 所有测试通过!")
    else:
        print("❌ 测试失败!")
        exit(1)

if __name__ == "__main__":
    main()
