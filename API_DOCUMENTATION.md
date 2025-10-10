# Film Media Search API 文档

## 概述

Film Media Search API 是一个基于文本转向量的媒体搜索和下载服务。用户可以通过文本描述搜索相关的媒体文件，并获取下载链接。

## 基础信息

- **服务名称**: Film Media Search API
- **版本**: 1.0.0
- **基础URL**: `https://your-domain.com` (请替换为您的实际域名)
- **认证方式**: API Key
- **数据格式**: JSON

## 认证

所有API请求都需要提供有效的API密钥。您可以通过以下两种方式提供API密钥：

### 方式1: HTTP请求头
```http
X-API-Key: your-api-key-here
```

### 方式2: URL参数
```
?api_key=your-api-key-here
```

## 频率限制

- **限制**: 每小时最多100次API调用
- **重置时间**: 每小时重置一次
- **超出限制**: 返回HTTP 429状态码

## API端点

### 1. 获取API信息

**端点**: `GET /api/info`

**描述**: 获取API的基本信息和可用端点列表

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/info"
```

**响应示例**:
```json
{
  "service": "Film Media Search API",
  "version": "1.0.0",
  "description": "基于文本转向量的媒体搜索和下载服务",
  "endpoints": {
    "search": "/api/search - 搜索媒体",
    "status": "/api/status/<task_id> - 获取任务状态",
    "download": "/api/download-direct/<media_id> - 下载媒体文件",
    "info": "/api/info - API信息",
    "health": "/api/health - 健康检查"
  },
  "authentication": {
    "method": "API Key",
    "header": "X-API-Key",
    "parameter": "api_key"
  },
  "rate_limit": {
    "max_requests_per_hour": 100,
    "reset_interval": "1小时"
  }
}
```

### 2. 健康检查

**端点**: `GET /api/health`

**描述**: 检查服务运行状态和配置

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/health"
```

**响应示例**:
```json
{
  "status": "healthy",
  "message": "服务运行正常",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0"
}
```

### 3. 搜索媒体

**端点**: `POST /api/search`

**描述**: 根据文本描述搜索匹配的媒体文件

**认证**: 需要API密钥

**请求头**:
```http
Content-Type: application/json
X-API-Key: your-api-key-here
```

**请求体**:
```json
{
  "text": "搜索的文本描述",
  "match_threshold": 0.0,
  "match_count": 5
}
```

**参数说明**:
- `text` (必需): 搜索的文本描述
- `match_threshold` (可选): 匹配阈值，默认0.0
- `match_count` (可选): 返回的最大结果数量，默认5

**请求示例**:
```bash
curl -X POST "https://your-domain.com/api/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "一只可爱的小猫在花园里玩耍",
    "match_threshold": 0.0,
    "match_count": 3
  }'
```

**响应示例**:
```json
{
  "task_id": "12345678-1234-1234-1234-123456789abc"
}
```

### 4. 获取任务状态

**端点**: `GET /api/status/<task_id>`

**描述**: 获取搜索任务的处理状态和结果

**认证**: 需要API密钥

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/status/12345678-1234-1234-1234-123456789abc" \
  -H "X-API-Key: your-api-key-here"
```

**响应示例**:

**处理中**:
```json
{
  "status": "processing",
  "progress": 60,
  "message": "找到 3 个匹配的媒体...",
  "data": null,
  "created_at": 1704067200.0
}
```

**完成**:
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
      },
      {
        "id": "media_002", 
        "key": "videos/cute_cat.mp4",
        "watch_url": "https://s3.amazonaws.com/bucket/videos/cute_cat.mp4?signature=..."
      }
    ]
  },
  "created_at": 1704067200.0
}
```

**错误**:
```json
{
  "status": "error",
  "progress": 0,
  "message": "文本转向量失败",
  "data": null,
  "created_at": 1704067200.0
}
```

### 5. 下载媒体文件

**端点**: `GET /api/download-direct/<media_id>`

**描述**: 获取媒体文件的直接下载链接

**认证**: 需要API密钥

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/download-direct/media_001" \
  -H "X-API-Key: your-api-key-here"
```

**响应**: 重定向到S3预签名URL，直接开始下载文件

### 6. 强制下载文件

**端点**: `GET /api/download-file/<media_id>`

**描述**: 强制下载文件（设置Content-Disposition为attachment）

**认证**: 需要API密钥

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/download-file/media_001" \
  -H "X-API-Key: your-api-key-here"
```

## 错误处理

### 常见错误码

| 状态码 | 错误类型 | 描述 |
|--------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | API密钥无效或缺失 |
| 404 | Not Found | 资源不存在 |
| 429 | Too Many Requests | API调用频率超限 |
| 500 | Internal Server Error | 服务器内部错误 |

### 错误响应格式

```json
{
  "error": "错误类型",
  "message": "详细错误信息"
}
```

### 错误示例

**缺少API密钥**:
```json
{
  "error": "缺少API密钥",
  "message": "请在请求头中添加 X-API-Key 或使用 api_key 参数"
}
```

**无效API密钥**:
```json
{
  "error": "无效的API密钥",
  "message": "请检查您的API密钥是否正确"
}
```

**频率超限**:
```json
{
  "error": "API调用频率超限",
  "message": "每小时最多允许100次API调用，请稍后再试"
}
```

## 使用流程

### 完整的搜索和下载流程

1. **获取API信息** (可选)
   ```bash
   curl -X GET "https://your-domain.com/api/info"
   ```

2. **搜索媒体**
   ```bash
   curl -X POST "https://your-domain.com/api/search" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key-here" \
     -d '{"text": "搜索描述", "match_count": 5}'
   ```

3. **检查任务状态**
   ```bash
   curl -X GET "https://your-domain.com/api/status/task-id" \
     -H "X-API-Key: your-api-key-here"
   ```

4. **下载媒体文件**
   ```bash
   curl -X GET "https://your-domain.com/api/download-direct/media-id" \
     -H "X-API-Key: your-api-key-here"
   ```

## 集成示例

### Python示例

```python
import requests
import time

class FilmMediaAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def search_media(self, text, match_threshold=0.0, match_count=5):
        """搜索媒体"""
        url = f"{self.base_url}/api/search"
        data = {
            'text': text,
            'match_threshold': match_threshold,
            'match_count': match_count
        }
        
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
            
            time.sleep(2)  # 等待2秒后重试
        
        raise Exception("任务超时")
    
    def download_media(self, media_id):
        """下载媒体文件"""
        url = f"{self.base_url}/api/download-direct/{media_id}"
        response = requests.get(url, headers=self.headers, allow_redirects=True)
        response.raise_for_status()
        return response.content

# 使用示例
api = FilmMediaAPI("https://your-domain.com", "your-api-key-here")

# 搜索媒体
result = api.search_media("一只可爱的小猫")
task_id = result['task_id']

# 等待完成
status = api.wait_for_completion(task_id)

# 获取媒体列表
media_list = status['data']['media_list']
print(f"找到 {len(media_list)} 个匹配的媒体")

# 下载第一个媒体文件
if media_list:
    media_id = media_list[0]['id']
    file_content = api.download_media(media_id)
    
    # 保存文件
    with open(f"{media_id}.mp4", "wb") as f:
        f.write(file_content)
```

### JavaScript示例

```javascript
class FilmMediaAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async searchMedia(text, matchThreshold = 0.0, matchCount = 5) {
        const response = await fetch(`${this.baseUrl}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({
                text,
                match_threshold: matchThreshold,
                match_count: matchCount
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getTaskStatus(taskId) {
        const response = await fetch(`${this.baseUrl}/api/status/${taskId}`, {
            headers: {
                'X-API-Key': this.apiKey
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async waitForCompletion(taskId, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const status = await this.getTaskStatus(taskId);
            
            if (status.status === 'completed') {
                return status;
            } else if (status.status === 'error') {
                throw new Error(`任务失败: ${status.message}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        throw new Error('任务超时');
    }
}

// 使用示例
const api = new FilmMediaAPI('https://your-domain.com', 'your-api-key-here');

async function searchAndDownload() {
    try {
        // 搜索媒体
        const result = await api.searchMedia('一只可爱的小猫');
        const taskId = result.task_id;
        
        // 等待完成
        const status = await api.waitForCompletion(taskId);
        
        // 获取媒体列表
        const mediaList = status.data.media_list;
        console.log(`找到 ${mediaList.length} 个匹配的媒体`);
        
        // 显示结果
        mediaList.forEach((media, index) => {
            console.log(`${index + 1}. ${media.id}: ${media.watch_url}`);
        });
        
    } catch (error) {
        console.error('错误:', error.message);
    }
}

searchAndDownload();
```

## 注意事项

1. **API密钥安全**: 请妥善保管您的API密钥，不要在客户端代码中暴露
2. **频率限制**: 请注意API调用频率限制，避免超出限制
3. **文件大小**: 下载的媒体文件可能较大，请确保有足够的存储空间
4. **网络超时**: 大文件下载可能需要较长时间，请设置合适的超时时间
5. **错误处理**: 请实现适当的错误处理机制

## 技术支持

如有问题或需要技术支持，请联系开发团队。
