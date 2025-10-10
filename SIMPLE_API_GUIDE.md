# 简化版 Film Media Search API 使用指南

## 🎯 概述

这是一个简化版的媒体搜索API，只需要两个参数：`text`（搜索文本）和 `match_count`（返回结果数量），并提供直接下载到本地目录的功能。

## 🔑 基本配置

### API信息
- **基础URL**: `https://your-domain.com`
- **认证方式**: API Key
- **数据格式**: JSON

### 认证
```http
X-API-Key: your-api-key-here
```

## 📡 API接口

### 1. 搜索媒体接口

**端点**: `POST /api/search`

**输入参数**:
```json
{
  "text": "搜索的文本描述",
  "match_count": 5
}
```

**参数说明**:
- `text` (必需): 搜索的文本描述
- `match_count` (可选): 返回的最大结果数量，默认5

**输出参数**:
```json
{
  "task_id": "12345678-1234-1234-1234-123456789abc"
}
```

### 2. 获取任务状态

**端点**: `GET /api/status/<task_id>`

**输出参数**:
```json
{
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "data": {
    "media_list": [
      {
        "id": "media_001",
        "key": "videos/cat_playing_garden.mp4",
        "watch_url": "https://s3.amazonaws.com/bucket/videos/cat_playing_garden.mp4?signature=..."
      }
    ]
  },
  "created_at": 1704067200.0
}
```

### 3. 下载媒体到本地

**端点**: `POST /api/download-to-local`

**输入参数**:
```json
{
  "media_list": [
    {
      "id": "media_001",
      "key": "videos/cat_playing_garden.mp4"
    }
  ],
  "download_dir": "downloads"
}
```

**输出参数**:
```json
{
  "success": true,
  "downloaded_files": [
    {
      "media_id": "media_001",
      "local_path": "downloads/media_001.mp4",
      "file_size": 1024000
    }
  ],
  "failed_downloads": [],
  "download_dir": "downloads",
  "total_files": 1,
  "successful_downloads": 1,
  "failed_count": 0
}
```

## 💻 代码使用示例

### Python 完整示例

```python
import requests
import time

class SimpleFilmMediaAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def search_media(self, text, match_count=5):
        """搜索媒体文件"""
        url = f"{self.base_url}/api/search"
        data = {'text': text, 'match_count': match_count}
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        url = f"{self.base_url}/api/status/{task_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id, timeout=300):
        """等待任务完成"""
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
    
    def download_media_to_local(self, media_list, download_dir="downloads"):
        """下载媒体文件到本地目录"""
        url = f"{self.base_url}/api/download-to-local"
        data = {
            'media_list': media_list,
            'download_dir': download_dir
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def search_and_download(self, text, match_count=5, download_dir="downloads"):
        """搜索并下载媒体文件的完整流程"""
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
            return {'message': '未找到匹配的媒体'}
        
        # 4. 下载媒体文件
        print(f"📥 开始下载到目录: {download_dir}")
        download_result = self.download_media_to_local(media_list, download_dir)
        
        print(f"✅ 下载完成:")
        print(f"   成功下载: {download_result['successful_downloads']} 个文件")
        print(f"   失败: {download_result['failed_count']} 个文件")
        
        return {
            'search_result': status,
            'download_result': download_result
        }

# 使用示例
def main():
    # 初始化API客户端
    api = SimpleFilmMediaAPI("https://your-domain.com", "your-api-key-here")
    
    try:
        # 搜索并下载媒体
        result = api.search_and_download(
            text="一只可爱的小猫在花园里玩耍",
            match_count=3,
            download_dir="my_downloads"
        )
        
        # 显示结果
        if result.get('download_result'):
            for file_info in result['download_result']['downloaded_files']:
                print(f"✅ 下载成功: {file_info['local_path']}")
                print(f"   文件大小: {file_info['file_size']} 字节")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
```

### JavaScript 示例

```javascript
class SimpleFilmMediaAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }
    
    async searchMedia(text, matchCount = 5) {
        const response = await fetch(`${this.baseUrl}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({ text, match_count: matchCount })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async getTaskStatus(taskId) {
        const response = await fetch(`${this.baseUrl}/api/status/${taskId}`, {
            headers: { 'X-API-Key': this.apiKey }
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async waitForCompletion(taskId, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const status = await this.getTaskStatus(taskId);
            
            if (status.status === 'completed') return status;
            if (status.status === 'error') throw new Error(`任务失败: ${status.message}`);
            
            console.log(`任务状态: ${status.status}, 进度: ${status.progress}%`);
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        throw new Error('任务超时');
    }
    
    async downloadMediaToLocal(mediaList, downloadDir = 'downloads') {
        const response = await fetch(`${this.baseUrl}/api/download-to-local`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({
                media_list: mediaList,
                download_dir: downloadDir
            })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async searchAndDownload(text, matchCount = 5, downloadDir = 'downloads') {
        console.log(`🔍 搜索媒体: '${text}'`);
        
        // 1. 搜索媒体
        const searchResult = await this.searchMedia(text, matchCount);
        const taskId = searchResult.task_id;
        console.log(`✅ 搜索任务已创建: ${taskId}`);
        
        // 2. 等待任务完成
        console.log('⏳ 等待搜索完成...');
        const status = await this.waitForCompletion(taskId);
        
        if (status.status !== 'completed') {
            throw new Error(`搜索失败: ${status.message || '未知错误'}`);
        }
        
        // 3. 获取媒体列表
        const mediaList = status.data.media_list;
        console.log(`✅ 找到 ${mediaList.length} 个匹配的媒体`);
        
        if (mediaList.length === 0) {
            return { message: '未找到匹配的媒体' };
        }
        
        // 4. 下载媒体文件
        console.log(`📥 开始下载到目录: ${downloadDir}`);
        const downloadResult = await this.downloadMediaToLocal(mediaList, downloadDir);
        
        console.log(`✅ 下载完成:`);
        console.log(`   成功下载: ${downloadResult.successful_downloads} 个文件`);
        console.log(`   失败: ${downloadResult.failed_count} 个文件`);
        
        return {
            searchResult: status,
            downloadResult: downloadResult
        };
    }
}

// 使用示例
async function main() {
    const api = new SimpleFilmMediaAPI('https://your-domain.com', 'your-api-key-here');
    
    try {
        const result = await api.searchAndDownload(
            '一只可爱的小猫在花园里玩耍',
            3,
            'my_downloads'
        );
        
        if (result.downloadResult) {
            result.downloadResult.downloaded_files.forEach(fileInfo => {
                console.log(`✅ 下载成功: ${fileInfo.local_path}`);
                console.log(`   文件大小: ${fileInfo.file_size} 字节`);
            });
        }
        
    } catch (error) {
        console.error(`❌ 错误: ${error.message}`);
    }
}

main();
```

### cURL 示例

```bash
#!/bin/bash

# 配置
BASE_URL="https://your-domain.com"
API_KEY="your-api-key-here"
SEARCH_TEXT="一只可爱的小猫在花园里玩耍"
MATCH_COUNT=3
DOWNLOAD_DIR="downloads"

echo "🔍 搜索媒体: $SEARCH_TEXT"

# 1. 搜索媒体
SEARCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "{\"text\": \"${SEARCH_TEXT}\", \"match_count\": ${MATCH_COUNT}}")

echo "搜索响应: $SEARCH_RESPONSE"

# 提取任务ID
TASK_ID=$(echo $SEARCH_RESPONSE | jq -r '.task_id')
echo "任务ID: $TASK_ID"

# 2. 等待任务完成
echo "⏳ 等待任务完成..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/status/${TASK_ID}" \
    -H "X-API-Key: ${API_KEY}")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress')
  
  echo "任务状态: $STATUS, 进度: $PROGRESS%"
  
  if [ "$STATUS" = "completed" ]; then
    echo "✅ 任务完成"
    break
  elif [ "$STATUS" = "error" ]; then
    echo "❌ 任务失败"
    exit 1
  fi
  
  sleep 2
done

# 3. 获取媒体列表
MEDIA_LIST=$(echo $STATUS_RESPONSE | jq -c '.data.media_list')
echo "找到的媒体: $MEDIA_LIST"

# 4. 下载媒体文件到本地
echo "📥 下载媒体文件到目录: $DOWNLOAD_DIR"
DOWNLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/download-to-local" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "{\"media_list\": ${MEDIA_LIST}, \"download_dir\": \"${DOWNLOAD_DIR}\"}")

echo "下载响应: $DOWNLOAD_RESPONSE"

# 显示下载结果
SUCCESS_COUNT=$(echo $DOWNLOAD_RESPONSE | jq -r '.successful_downloads')
FAILED_COUNT=$(echo $DOWNLOAD_RESPONSE | jq -r '.failed_count')

echo "✅ 下载完成: 成功 $SUCCESS_COUNT 个文件, 失败 $FAILED_COUNT 个文件"
```

## 🚀 快速开始

### 1. 使用Python示例脚本

```bash
# 运行简化版示例
python simple_api_example.py
```

### 2. 手动测试

```bash
# 测试健康检查
curl -X GET "https://your-domain.com/api/health"

# 测试搜索
curl -X POST "https://your-domain.com/api/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "一只可爱的小猫", "match_count": 3}'
```

## 📊 输入输出参数总结

### 搜索接口
- **输入**: `text` (搜索文本), `match_count` (结果数量)
- **输出**: `task_id` (任务ID)

### 任务状态
- **输入**: `task_id` (任务ID)
- **输出**: `status` (状态), `progress` (进度), `data.media_list` (媒体列表)

### 下载接口
- **输入**: `media_list` (媒体列表), `download_dir` (下载目录)
- **输出**: `downloaded_files` (成功下载的文件), `failed_downloads` (失败的文件)

## ⚠️ 注意事项

1. **API密钥**: 请妥善保管您的API密钥
2. **频率限制**: 每小时最多100次API调用
3. **文件大小**: 媒体文件可能较大，请确保有足够存储空间
4. **下载目录**: 确保有写入权限
5. **网络超时**: 大文件下载可能需要较长时间

现在您可以使用这个简化的API，只需要提供搜索文本和结果数量，就能搜索并下载媒体文件到本地目录！
