<<<<<<< HEAD
=======
# -AI-agent
一个可以基于需求对工业AI落地情况进行调研的agent
>>>>>>> a5724efe890d671065fd767d1315e8a3d14fa774
，hu# 🏭 工业 AI 调研 Agent API

> **一个基于 LangChain + CrewAI 的智能工业 AI 案例调研系统（后端 API）**  
> 前后端分离架构，提供 RESTful API 接口，支持任意前端框架调用

---

## 📋 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [API 接口文档](#api-接口文档)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [配置说明](#配置说明)
- [前端集成示例](#前端集成示例)
- [输出报告](#输出报告)
- [贡献指南](#贡献指南)

---

## 🎯 项目简介

**工业 AI 调研 Agent** 是一个智能化的工业 AI 案例调研系统后端 API，专为产品经理、行业研究员和企业决策者设计。通过结合大语言模型（LLM）、智能搜索、RAG 知识库和多智能体协作技术，系统能够：

✅ **自动解析**用户调研需求，提取关键信息  
✅ **精准检索**高价值的工业 AI 落地案例  
✅ **深度分析**案例的技术架构、商业价值和落地路径  
✅ **生成标准化**的调研报告，支持定制化输出  

### 核心亮点

- 🧠 **渐进式推理架构**：D1→D2→D3→D4→D5 五阶段流水线
- 🔍 **混合检索机制**：元数据过滤 + 向量检索 + 商业价值排序
- 🤖 **多智能体协作**：4 个专业角色（解决方案分析师、行业研究员、商业分析师、机会扫描员）
- 📊 **PM 视角输出**：聚焦大厂切入点、商业闭环、可复制性评估
- 🔌 **前后端分离**：RESTful API 设计，支持任意前端框架集成
- 🔒 **本地化部署**：支持 Ollama 本地模型，保护数据隐私

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端应用 (任意框架)                       │
│         React / Vue / Angular / 移动端 / CLI                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
    ┌────────────────▼────────────────┐
    │     FastAPI 后端服务 (端口 8000)   │
    │     - RESTful API 接口            │
    │     - CORS 跨域支持              │
    │     - 自动 API 文档 (/docs)       │
    └────────────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │  D1: 需求解析模块                 │
    │  - LLM 提取核心字段               │
    │  - 规则引擎补充多维度信息         │
    │  - 输出结构化需求对象             │
    └────────────────┬────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │  D2: 精准检索模块                 │
    │  - Tavily API 全网检索           │
    │  - 三重过滤（时效性/商业价值/相关性）│
    │  - Mock 模式（无 API Key 可用）   │
    └────────────────┬────────────────
                     │
    ┌────────────────▼────────────────┐
    │  D3: RAG 知识库                   │
    │  - 9 字段元数据提取               │
    │  - ChromaDB 向量存储             │
    │  - 混合检索（过滤→检索→排序→推荐） │
    └────────────────┬────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │  D4: CrewAI 深度分析              │
    │  - 4 角色串行协作                 │
    │  - 解决方案拆解 / 行业适配 / 商业价值│
    │  - 大厂切入点专项分析             │
    └────────────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │  D5: 质量审核层                   │
    │  - 100 分制规则评分              │
    │  - 5 维度质量检测                │
    │  - 自动反馈与优化                 │
    └────────────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │         返回 JSON 响应             │
    │  { status, report, error }       │
    └─────────────────────────────────┘
```

---

## ✨ 核心功能

### 1️⃣ D1 需求解析（Requirement Parser）

- **混合解析策略**：LLM 提取核心字段 + 规则引擎补充多维度信息
- **支持维度**：
  - 主行业 / 细分行业（化工→石油化工、虚拟电厂、钢铁等）
  - 技术领域（算法/AI、硬件/设备、软件/平台、数据/集成）
  - 公司范围（国内/国外/头部企业/中小企业）
  - 地域范围（华东/华北/华南/全国/全球）
- **模糊需求处理**：自动识别并提供补充引导

### 2️⃣ D2 精准检索（Search Tool）

- **三重过滤机制**（纯规则代码，零 LLM 调用成本）：
  - ⏰ 时效性评分：优先最新案例（2024-2025）
  - 💰 商业价值评分：识别 ROI、节能数据、合同额等关键指标
  - 🎯 相关性评分：关键词匹配 + 优先级权重
- **Tavily API 集成**：支持真实全网检索（可选）
- **Mock 模式**：内置行业演示数据，无需 API Key 即可运行

### 3️⃣ D3 RAG 知识库（RAG Library）

- **PM 视角元数据提取**（9 个核心字段）：
  - 项目名称、甲方行业、核心痛点、技术路径
  - 商业闭环、乙方角色、可复制性评分
  - 量化效果、PM 重点标注
- **混合检索流程**：
  1. 元数据过滤（行业 + 可复制性阈值）
  2. 向量相似度检索（ChromaDB）
  3. 商业价值排序（可复制性 + 量化数据完整性）
  4. 案例关联推荐（基于行业 + 痛点相似度）
- **数据清洗保护**：保留数值类型，避免过度转换

### 4️⃣ D4 CrewAI 深度分析（Analysis Crew）

**四角色协作流水线**：

| 角色 | 职责 | 输出维度 |
|------|------|---------|
| ‍💻 AI 产品解决方案分析师 | 深度拆解技术架构、优劣势、落地门槛 | 8 维度解决方案拆解 |
| 🔬 工业领域行业研究员 | 行业适配性、痛点覆盖度、政策环境 | 行业深度分析 |
| 💼 商业分析师 | 收费模式、ROI、市场规模、付费决策逻辑 | 商业价值量化 |
| 🎯 互联网大厂机会扫描员 | 现有方案缺口、差异化优势、切入路径 | **核心输出**：大厂切入点专项分析 |

### 5️⃣ D5 质量审核（Review Layer）

**100 分制规则评分**：

| 维度 | 权重 | 检测标准 |
|------|------|---------|
| 解决方案深度 | 25 分 | 包含技术架构 + 优劣势分析 |
| 量化数据 | 25 分 | ≥3 个量化指标（数字 + 单位） |
| 大厂切入点 | 20 分 | 包含切入点专项分析 |
| 商业逻辑 | 15 分 | 包含 ROI/收费模式/商业闭环 |
| 报告长度 | 15 分 | ≥1000 字 |

**合格线**：75 分

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Windows / macOS / Linux

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/chenweiting482-ux/-AI-agent.git
cd -AI-agent
```

2. **创建虚拟环境**

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件（在项目根目录）：

```bash
# 阿里云 DashScope API Key（必需，用于 LLM 和 Embedding）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Tavily API Key（可选，用于真实网络检索）
TAVILY_API_KEY=your_tavily_api_key_here
```

> 📌 **获取 API Key**：
> - DashScope: [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)
> - Tavily: [https://tavily.com/](https://tavily.com/)

5. **启动后端 API 服务**

```bash
python app.py
```

服务将在 `http://localhost:8000` 启动

6. **访问 API 文档**

浏览器打开：[http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔌 API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **API 文档**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

### 接口列表

#### 1. 健康检查

```http
GET /health
```

**响应示例**：
```json
{
  "status": "healthy",
  "service": "industrial-ai-agent"
}
```

#### 2. 执行调研

```http
POST /api/research
Content-Type: application/json

{
  "query": "AI+化工落地方向案例，产出报告，优先找有明确节能效果的标杆案例",
  "skip_clarification": false
}
```

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 调研需求描述 |
| skip_clarification | boolean | ❌ | 是否跳过澄清步骤（默认 false） |

**响应示例**：
```json
{
  "status": "success",
  "report": "# 化工行业 AI 落地案例深度调研报告\n\n...",
  "error": null
}
```

#### 3. 快速调研（跳过澄清）

```http
POST /api/quick-research
Content-Type: application/json

{
  "query": "AI+化工案例"
}
```

等同于调用 `/api/research` 并设置 `skip_clarification: true`

---

## 💻 前端集成示例

### JavaScript / TypeScript (Fetch API)

```javascript
// 执行调研
async function runResearch(query) {
  try {
    const response = await fetch('http://localhost:8000/api/research', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        skip_clarification: false
      })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      console.log('调研报告：', result.report);
      // 在页面上显示报告内容
      document.getElementById('report').innerHTML = marked.parse(result.report);
    } else {
      console.error('调研失败：', result.error);
    }
  } catch (error) {
    console.error('请求失败：', error);
  }
}

// 使用示例
runResearch('AI+化工落地方向案例');
```

### Python (requests)

```python
import requests

def run_research(query):
    url = "http://localhost:8000/api/research"
    payload = {
        "query": query,
        "skip_clarification": False
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result["status"] == "success":
        print("调研报告：")
        print(result["report"])
    else:
        print("调研失败：", result["error"])

# 使用示例
run_research("AI+化工落地方向案例")
```

### cURL

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI+化工落地方向案例",
    "skip_clarification": false
  }'
```

### React 组件示例

```jsx
import { useState } from 'react';

function ResearchAgent() {
  const [query, setQuery] = useState('');
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);

  const handleResearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, skip_clarification: false })
      });
      const result = await response.json();
      if (result.status === 'success') {
        setReport(result.report);
      }
    } catch (error) {
      console.error('调研失败：', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        value={query} 
        onChange={(e) => setQuery(e.target.value)}
        placeholder="输入调研需求..."
      />
      <button onClick={handleResearch} disabled={loading}>
        {loading ? '调研中...' : '开始调研'}
      </button>
      {report && <div dangerouslySetInnerHTML={{ __html: report }} />}
    </div>
  );
}

export default ResearchAgent;
```

---

## 📁 项目结构

```
工业AI调研agent/
├── app.py                        # FastAPI 后端接口（端口 9000）
├── main_entra.py                 # Agent 主入口
├── d1_requirement_parser.py      # D1: 需求解析模块
├── d2_search_tool.py             # D2: 精准检索模块
├── d3_rag_library.py             # D3: RAG 知识库
├── d4_d5_analysis_review.py      # D4+D5: 深度分析 + 质量审核
├── llm_config.py                 # LLM 配置中心
│
├── chroma_db/                    # ChromaDB 向量数据库（自动生成）
├── output_reports/               # 输出的调研报告（自动生成）
│   ├── 化工/
│   │   └── 化工_调研报告_20260405_153000.md
│   └── 虚拟电厂/
│       └── 虚拟电厂_调研报告_20260405_154500.md
│
├── Dockerfile                    # Docker 容器镜像配置（阿里云 FC）
├── s.yaml                        # Serverless Devs 部署配置
├── .dockerignore                 # Docker 忽略文件
├── frontend-integration.json     # 前端对接文档
├── FC_DEPLOYMENT.md              # 阿里云 FC 部署指南
│
├── .env                          # 环境变量配置文件（不提交到 Git）
├── .gitignore                    # Git 忽略规则
├── README.md                     # 项目说明文档
└── requirements.txt              # Python 依赖列表