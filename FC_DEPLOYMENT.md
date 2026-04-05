# 🚀 阿里云函数计算 FC 3.0 部署指南

> **后端 API 部署到阿里云 Serverless 平台的完整指南**

---

## 📋 目录

- [部署前准备](#部署前准备)
- [方式一：控制台部署（推荐新手）](#方式一控制台部署推荐新手)
- [方式二：Serverless Devs 部署（推荐高级用户）](#方式二serverless-devs-部署推荐高级用户)
- [方式三：Docker 镜像部署](#方式三docker-镜像部署)
- [环境变量配置](#环境变量配置)
- [前后端联调](#前后端联调)
- [常见问题](#常见问题)

---

## 🛠️ 部署前准备

### 1. 确认文件完整

确保你的项目包含以下文件：

```
工业AI调研agent/
├── app.py                      # FastAPI 后端（端口 9000）
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 镜像配置
├── s.yaml                      # Serverless Devs 配置
├── .dockerignore               # Docker 忽略文件
├── frontend-integration.json   # 前端对接文档
└── [其他核心代码文件]
```

### 2. 准备 API Key

- ✅ **DASHSCOPE_API_KEY**: 阿里云 DashScope API Key
- ⚠️ **TAVILY_API_KEY**: Tavily 搜索 API（可选）

> 🔒 **重要**：API Key 通过环境变量配置，不要写在代码里！

---

## 方式一：控制台部署（推荐新手）

### 步骤 1：创建 Web 应用

1. 登录 [阿里云函数计算控制台](https://fcnext.console.aliyun.com/)
2. 点击 **创建应用** → 选择 **Web 应用**
3. 填写信息：
   - **应用名称**: `industrial-ai-agent`
   - **地域**: 选择靠近你用户的地域（如 `华东2（上海）`）
   - **代码来源**: 选择 **GitHub 仓库**

### 步骤 2：关联 GitHub 仓库

1. **授权 GitHub**（首次需要）
2. **选择仓库**: `chenweiting482-ux/-AI-agent`
3. **选择分支**: `main`
4. **代码目录**: 留空（代码在根目录）

### 步骤 3：配置运行环境

- **运行时**: 选择 `Custom Container`（自定义容器）
- **镜像构建**: 选择 **自动构建**（使用 Dockerfile）
- **实例规格**:
  - CPU: `2 核`
  - 内存: `4 GB`（LLM 推理需要较大内存）
  - 磁盘: `512 MB`
- **超时时间**: `300 秒`（AI 推理可能较慢）
- **并发实例数**: `10`

### 步骤 4：配置环境变量

在 **环境变量** 标签页添加：

```bash
PORT=9000
DASHSCOPE_API_KEY=sk-你的key
TAVILY_API_KEY=你的key（可选）
```

### 步骤 5：配置网络

- **公网访问**: 开启
- **跨域 (CORS)**: 开启（允许前端调用）
- **认证方式**: 匿名访问（或按需配置）

### 步骤 6：部署

点击 **创建并部署**，等待 3-5 分钟。

部署成功后，你会获得一个公网域名：
```
https://your-app.cn-shanghai.fc.aliyuncs.com
```

---

## 方式二：Serverless Devs 部署（推荐高级用户）

### 步骤 1：安装 Serverless Devs

```bash
# macOS/Linux
curl -o- -L https://cli.serverless-devs.com/install.sh | bash

# Windows (PowerShell)
iwr https://cli.serverless-devs.com/install.ps1 -useb | iex
```

### 步骤 2：配置阿里云账号

```bash
# 交互式配置
s config add

# 依次输入：
# - Provider: Alibaba Cloud (alibaba)
# - AccessKey ID: 你的 AccessKey ID
# - AccessKey Secret: 你的 AccessKey Secret
# - Account ID: 你的阿里云账号 ID
# - Alias: default
```

### 步骤 3：部署应用

```bash
# 进入项目目录
cd 工业AI调研agent

# 部署应用
s deploy

# 查看部署状态
s info
```

### 步骤 4：配置环境变量（通过控制台）

部署后，登录阿里云控制台添加环境变量（见 [环境变量配置](#环境变量配置)）

---

## 方式三：Docker 镜像部署

### 步骤 1：构建 Docker 镜像

```bash
# 构建镜像
docker build -t industrial-ai-agent:latest .

# 测试本地运行
docker run -p 9000:9000 \
  -e DASHSCOPE_API_KEY=sk-你的key \
  industrial-ai-agent:latest
```

### 步骤 2：推送到阿里云容器镜像服务

```bash
# 登录阿里云容器镜像服务
docker login --username=你的用户名 registry.cn-shanghai.aliyuncs.com

# 打标签
docker tag industrial-ai-agent:latest registry.cn-shanghai.aliyuncs.com/你的命名空间/industrial-ai-agent:latest

# 推送镜像
docker push registry.cn-shanghai.aliyuncs.com/你的命名空间/industrial-ai-agent:latest
```

### 步骤 3：在 FC 控制台创建函数

1. 选择 **容器镜像** 作为代码来源
2. 选择刚才推送的镜像
3. 配置环境变量和端口（9000）

---

## 🔧 环境变量配置

### 必需的环境变量

| 变量名 | 必填 | 说明 | 获取方式 |
|--------|------|------|---------|
| `PORT` | ✅ | 服务端口 | 固定为 `9000` |
| `DASHSCOPE_API_KEY` | ✅ | DashScope API Key | [阿里云控制台](https://dashscope.console.aliyun.com/) |
| `TAVILY_API_KEY` | ⚠️ | Tavily 搜索 API | [Tavily 官网](https://tavily.com/) |

### 配置位置

**方式一：控制台配置**

1. 进入函数计算控制台
2. 选择你的应用
3. 点击 **配置** → **环境变量**
4. 添加变量并保存

**方式二：s.yaml 配置**（不推荐，容易泄露）

```yaml
environmentVariables:
  DASHSCOPE_API_KEY: 'sk-你的key'  # 不推荐硬编码
```

---

## 🔗 前后端联调

### 步骤 1：获取后端 API 地址

部署成功后，在控制台查看公网域名：
```
https://your-app.cn-shanghai.fc.aliyuncs.com
```

### 步骤 2：修改前端代码

在前端代码中，将 API 地址改为阿里云域名：

```javascript
// 将这个：
const API_URL = "http://localhost:9000/api/research";

// 改为这个：
const API_URL = "https://your-app.cn-shanghai.fc.aliyuncs.com/api/research";
```

### 步骤 3：测试跨域 (CORS)

后端已配置 CORS 允许所有域名访问：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 步骤 4：前端调用示例

```javascript
// 执行调研
async function runResearch(query) {
  const response = await fetch(
    'https://your-app.cn-shanghai.fc.aliyuncs.com/api/research',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        skip_clarification: false
      })
    }
  );
  
  const result = await response.json();
  console.log('调研报告：', result.report);
}

// 使用示例
runResearch('AI+化工落地方向案例');
```

---

## ❓ 常见问题

### 1. 部署超时怎么办？

**原因**: AI 推理时间较长（可能超过默认 60 秒）

**解决**: 
- 在控制台增加 **超时时间** 到 `300 秒`
- 在 [s.yaml](file://c:\Users\vicky\Desktop\工业AI调研agent\s.yaml) 中设置 `timeout: 300`

### 2. 内存不足报错？

**原因**: LLM 推理需要较大内存

**解决**:
- 增加实例内存到 `4 GB` 或更高
- 在控制台调整 **实例规格**

### 3. 跨域 (CORS) 错误？

**现象**: 浏览器报错 `Access-Control-Allow-Origin`

**解决**:
- 后端已配置 CORS，检查是否生效
- 确保前端请求正确设置了 `Content-Type: application/json`

### 4. API Key 未配置？

**现象**: 报错 `DASHSCOPE_API_KEY not found`

**解决**:
- 在控制台 **环境变量** 中添加 `DASHSCOPE_API_KEY`
- 重启函数实例

### 5. 冷启动延迟？

**原因**: Serverless 函数首次调用需要加载环境

**解决**:
- 设置 **预留实例**（产生费用）
- 或使用 **定时任务** 保持函数活跃

### 6. 如何查看日志？

```bash
# 通过 Serverless Devs 查看
s logs

# 或在控制台查看
# 函数计算控制台 → 应用 → 日志管理
```

---

## 📊 性能优化建议

### 1. 并发配置

- **单实例并发数**: `10`（已配置）
- **最大实例数**: 根据流量自动伸缩
- **预留实例**: 按需配置（减少冷启动）

### 2. 成本控制

- ✅ **按需付费**: 不调用不扣钱
- ✅ **空闲零成本**: 无请求时不产生费用
- ⚠️ **预留实例**: 会产生固定费用

### 3. 监控告警

在控制台配置：
- **QPS 监控**: 请求频率
- **错误率监控**: 失败请求比例
- **延迟监控**: 响应时间
- **费用告警**: 超出预算时通知

---

## 🎯 部署检查清单

- [ ] 代码已推送到 GitHub `main` 分支
- [ ] [app.py](file://c:\Users\vicky\Desktop\工业AI调研agent\app.py) 监听端口 `9000`
- [ ] [Dockerfile](file://c:\Users\vicky\Desktop\工业AI调研agent\Dockerfile) 存在且正确
- [ ] API Key 通过环境变量配置（不在代码中）
- [ ] CORS 已配置（允许前端调用）
- [ ] 超时时间设置为 `300 秒`
- [ ] 内存设置为 `4 GB`
- [ ] 前端代码中的 API 地址已更新
- [ ] 测试 API 接口正常工作

---

## 📞 技术支持

- **阿里云函数计算文档**: https://help.aliyun.com/product/50980.html
- **Serverless Devs 文档**: https://www.serverless-devs.com/
- **GitHub 仓库**: https://github.com/chenweiting482-ux/-AI-agent

---

**部署完成后，你的后端 API 将可以通过公网访问，前端只需调用对应的 URL 即可！** 
