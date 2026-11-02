# East-lake Knowledge Base API

> 提供语义搜索、知识图谱查询的 REST API 服务

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --port 8000
```

### Docker 运行

```bash
# 构建镜像
docker build -t east-lake-api .

# 运行容器
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e GITHUB_TOKEN=your-token \
  east-lake-api

# 或使用 docker-compose
docker-compose up -d
```

## API 端点

### 健康检查

```bash
GET /
GET /health
```

### 语义搜索

```bash
POST /search
Content-Type: application/json

{
  "query": "什么是 RAG 技术?",
  "top_k": 5,
  "category": "技术分析"
}
```

### 知识图谱

```bash
# 获取完整图谱
GET /graph

# 获取 Mermaid 格式
GET /graph/mermaid

# 获取特定节点
GET /graph/node/{node_id}?depth=2
```

### 统计信息

```bash
GET /stats
GET /stats/categories
GET /stats/tags?limit=20
```

## 认证

默认情况下，API 使用 `X-API-Key` 头进行认证：

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/stats
```

设置环境变量 `ADMIN_API_KEY` 来启用认证。

## 部署

### Vercel

```bash
# 使用 Vercel CLI
vercel --prod
```

### Railway

```bash
# 使用 Railway CLI
railway up
```

### Render

1. 连接 GitHub 仓库
2. 设置构建命令: `pip install -r requirements.txt`
3. 设置启动命令: `gunicorn main:app -k uvicorn.workers.UvicornWorker`

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EASTLAKE_ANTHROPIC_API_KEY` | Anthropic API Key | - |
| `EASTLAKE_GITHUB_TOKEN` | GitHub Token | - |
| `EASTLAKE_ADMIN_API_KEY` | API 认证 Key | - |
| `EASTLAKE_DEBUG` | 调试模式 | false |
| `EASTLAKE_RATE_LIMIT_PER_MINUTE` | API 速率限制 | 60 |

## 速率限制

默认每分钟 60 次请求，可在环境变量中配置。

## 示例

### Python SDK

```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}

# 搜索
response = requests.post(
    f"{BASE_URL}/search",
    json={"query": "RAG 技术", "top_k": 5},
    headers=headers
)
print(response.json())

# 获取图谱
response = requests.get(f"{BASE_URL}/graph", headers=headers)
print(response.json())
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000";
const API_KEY = "your-api-key";

const headers = { "X-API-Key": API_KEY };

// 搜索
const searchResponse = await fetch(`${BASE_URL}/search`, {
  method: "POST",
  headers: { ...headers, "Content-Type": "application/json" },
  body: JSON.stringify({ query: "RAG 技术", top_k: 5 })
});
const results = await searchResponse.json();
```