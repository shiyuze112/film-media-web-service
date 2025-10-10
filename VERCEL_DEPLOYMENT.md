# Vercel 部署指南

## 🚀 部署到 Vercel

### 1. 准备工作

确保您的代码已经推送到GitHub仓库，并且包含以下文件：
- `app.py` - 主应用文件
- `vercel.json` - Vercel配置文件
- `requirements.txt` - Python依赖
- `.env` - 环境变量（不要提交到仓库）

### 2. 环境变量配置

在Vercel控制台中设置以下环境变量：

#### 必需的环境变量：
```
SECRET_KEY=your-secret-key-here
API_KEYS=your-api-key-1,your-api-key-2,your-api-key-3
AZURE_OPENAI_API_KEY_EASTUS=your-azure-openai-api-key
AZURE_OPENAI_API_ENDPOINT_EASTUS=https://your-resource.openai.azure.com/
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=ap-east-1
AWS_BUCKET=your-s3-bucket-name
```

### 3. 部署步骤

1. **连接GitHub仓库**
   - 登录 [Vercel](https://vercel.com)
   - 点击 "New Project"
   - 选择您的GitHub仓库

2. **配置项目**
   - Framework Preset: Other
   - Root Directory: `film-media-web-service`
   - Build Command: 留空
   - Output Directory: 留空

3. **设置环境变量**
   - 在项目设置中添加上述环境变量
   - 确保所有敏感信息都通过环境变量设置

4. **部署**
   - 点击 "Deploy"
   - 等待部署完成

### 4. 部署后测试

部署完成后，您会得到一个类似 `https://your-project.vercel.app` 的URL。

#### 测试API连接：

```bash
# 1. 健康检查
curl https://your-project.vercel.app/api/health

# 2. API信息
curl https://your-project.vercel.app/api/info

# 3. 搜索测试（需要API密钥）
curl -X POST https://your-project.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "测试搜索", "match_count": 3}'
```

### 5. 外部调用示例

部署成功后，外部人员可以这样使用：

```python
import requests

# 配置
BASE_URL = "https://your-project.vercel.app"
API_KEY = "your-api-key"

# 搜索媒体
response = requests.post(f"{BASE_URL}/api/search", 
    headers={"X-API-Key": API_KEY},
    json={"text": "一只可爱的小猫", "match_count": 3}
)

task_id = response.json()["task_id"]
print(f"任务ID: {task_id}")

# 等待完成并获取结果
while True:
    status = requests.get(f"{BASE_URL}/api/status/{task_id}",
        headers={"X-API-Key": API_KEY}).json()
    
    if status["status"] == "completed":
        media_list = status["data"]["media_list"]
        print(f"找到 {len(media_list)} 个匹配的媒体")
        break
    elif status["status"] == "error":
        print("搜索失败")
        break
    
    time.sleep(2)

# 下载到本地
if media_list:
    download_response = requests.post(f"{BASE_URL}/api/download-to-local",
        headers={"X-API-Key": API_KEY},
        json={
            "media_list": media_list,
            "download_dir": "downloads"
        }
    )
    
    result = download_response.json()
    print(f"下载完成: 成功 {result['successful_downloads']} 个文件")
```

### 6. 注意事项

#### Vercel限制：
- **执行时间**: 最大30秒（已配置）
- **内存**: 1GB
- **文件系统**: 只读，不能写入本地文件
- **并发**: 1000个并发请求

#### 解决方案：
1. **文件下载**: 使用S3预签名URL，不通过Vercel下载
2. **大文件处理**: 异步处理，返回任务ID
3. **存储**: 使用S3存储，不依赖本地文件系统

### 7. 故障排除

#### 常见问题：

1. **部署失败**
   - 检查 `requirements.txt` 中的依赖版本
   - 确保所有环境变量都已设置
   - 查看Vercel构建日志

2. **API调用失败**
   - 检查API密钥是否正确
   - 确认环境变量配置
   - 查看Vercel函数日志

3. **超时错误**
   - 检查任务处理时间
   - 考虑优化算法
   - 使用异步处理

#### 调试命令：

```bash
# 检查部署状态
vercel ls

# 查看日志
vercel logs

# 本地测试
vercel dev
```

### 8. 监控和维护

1. **性能监控**
   - 使用Vercel Analytics
   - 监控API响应时间
   - 跟踪错误率

2. **日志查看**
   - Vercel Dashboard > Functions
   - 查看实时日志
   - 设置告警

3. **更新部署**
   - 推送代码到GitHub
   - Vercel自动重新部署
   - 测试新版本

现在您的API已经可以在Vercel上运行，外部人员可以通过HTTPS URL直接调用API接口！
