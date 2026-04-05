# LLM 配置说明

## 架构概览

本项目采用**混合 LLM 架构**，不同模块使用不同的模型后端，以平衡成本、速度和质量：

| 模块 | 用途 | 模型后端 | 配置方式 |
|------|------|----------|----------|
| **D1** | 需求解析 | 本地 Ollama | `get_llm(use_local=True)` |
| **D2** | 搜索增强 | - | Tavily API |
| **D3** | RAG 入库/检索 | 阿里云 DashScope | `get_llm(use_local=False)` + `get_embedding_model()` |
| **D4/D5** | 深度分析/审核 | 阿里云 DashScope | 环境变量配置 (CrewAI) |

---

## 环境变量配置 (.env)

请确保项目根目录下的 `.env` 文件包含以下配置：

```env
# 阿里云 DashScope API Key（用于 D3/D4-5）
# 获取地址: https://dashscope.console.aliyun.com/apiKey
DASHSCOPE_API_KEY=sk-10a0d08a2ece457899aa5574b4f38bea

# Tavily 搜索 API Key（用于 D2）
# 获取地址: https://app.tavily.com/home
TAVILY_API_KEY=tvly-dev-xxx

# Google API Key（可选，若 D1 切换为 Gemini 时需配置）
# GOOGLE_API_KEY=AIzaSy...
```

> **注意**: 修改 `.env` 后，请重启 Python 进程或重新加载环境变量以使更改生效。

---

## 模型配置详情

### D1 - 需求解析（本地模型）

**配置位置**: [`llm_config.py`](llm_config.py) → [`get_llm(use_local=True)`](llm_config.py#L10-L36)

**模型选择逻辑**（自动回退）:
1. `qwen2.5:7b` - 首选（能力强，平衡性好）
2. `qwen2.5:3b` - 备选（速度快，显存占用低）
3. `qwen2.5:1.5b` - 轻量版
4. `llama3.2:3b` - 最后备选

**初始化代码**:
```python
from llm_config import get_llm
llm = get_llm(temperature=0.1, num_predict=512, use_local=True)
```

**前置要求**:
```bash
# 1. 确保 Ollama 服务正在运行
ollama serve

# 2. 拉取模型（建议至少拉取一个）
ollama pull qwen2.5:7b
# 或者
ollama pull qwen2.5:3b
```

---

### D3 - RAG 库（阿里云 DashScope）

**配置位置**: 
- LLM: [`llm_config.py`](llm_config.py) → [`get_llm(use_local=False)`](llm_config.py#L10-L36)
- Embedding: [`llm_config.py`](llm_config.py) → [`get_embedding_model()`](llm_config.py#L80-L104)

**模型**:
- LLM: `qwen-turbo` (可根据需求改为 `qwen-plus` 或 `qwen-max`)
- Embedding: `text-embedding-v2`

**初始化代码**:
```python
from llm_config import get_llm, get_embedding_model

# LLM 初始化
llm = get_llm(temperature=0.0, num_predict=512, use_local=False)

# Embedding 模型初始化
embeddings = get_embedding_model()
```

**技术实现**:
通过 `langchain-openai` 库的 OpenAI 兼容接口调用 DashScope，无需安装额外的 `dashscope` SDK。
- **API 端点**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **优势**: 统一接口，减少依赖，解决本地 Ollama 不稳定问题。

---

### D4/D5 - 深度分析（阿里云 DashScope via CrewAI）

**配置位置**: [`d4_d5_analysis_review.py`](d4_d5_analysis_review.py)

**环境变量注入**:
CrewAI 框架默认寻找 OpenAI 风格的环境变量。我们在代码中进行了映射：

```python
import os
os.environ["OPENAI_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")
os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
os.environ["OPENAI_MODEL_NAME"] = "qwen-turbo"
```

**说明**: 
- CrewAI 代理将通过上述环境变量自动连接到千问 API。
- 无需在 CrewAI 初始化时显式传入 LLM 对象，简化了配置。
- 避免了因 Pydantic v2 验证导致的潜在兼容性问题。

---

## 数据清洗机制

为避免 Embedding API 报错 `contents is neither str nor list of str`，D3 模块中实现了 `safe_str()` 辅助函数：

**代码实现** ([`d3_rag_library.py`](d3_rag_library.py)):
```python
def safe_str(value: any) -> str:
    """将任意值转换为安全的字符串"""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join([str(v) for v in value if v is not None])
    return str(value).strip()
```

**应用场景**:
- **入库时**: 清洗 `Document.page_content` 和 `metadata` 字段，确保没有 `None` 或非字符串类型。
- **检索时**: 清洗用户查询 `query` 参数。

---

## 常见问题排查

### 1. D1 报错 "llama runner process has terminated"

**原因**: Ollama 模型损坏、显存不足或未正确加载。

**解决方案**:
```bash
# 1. 删除并重新拉取模型
ollama rm qwen2.5:7b
ollama pull qwen2.5:7b

# 2. 如果显存有限，尝试更小的模型
ollama pull qwen2.5:3b
# 并在代码中优先使用 3b 模型
```

### 2. D3 报错 "contents is neither str nor list of str"

**原因**: 传递给 Embedding 模型的数据包含 `None` 或非字符串类型（如整数、列表）。

**解决方案**: 
- 确认已应用 `safe_str()` 清洗逻辑。
- 检查上游数据源，确保没有异常的空值或复杂对象直接传入。

### 3. D3/D4-5 报错 "Invalid API Key" 或 "Authentication Error"

**原因**: `.env` 中 `DASHSCOPE_API_KEY` 配置错误、失效或未加载。

**解决方案**:
1. **检查格式**: 确保 `.env` 文件为 UTF-8 编码，无 `.txt` 后缀，Key 前后无空格。
2. **验证 Key**: 在阿里云控制台确认 Key 状态正常且有余额。
3. **环境变量生效**: 
   - Windows PowerShell: `$env:DASHSCOPE_API_KEY` 检查是否输出 Key。
   - 重启 IDE 或终端，确保重新加载了 `.env`。

### 4. CrewAI 运行缓慢或超时

**原因**: 网络波动或 API 速率限制。

**解决方案**:
- 检查网络连接，确保能访问 `dashscope.aliyuncs.com`。
- 在 CrewAI 配置中适当增加 `timeout` 或重试次数。
- 确认 `max_rpm` (每分钟请求数) 设置合理，默认 100 QPS 通常足够，但并发高时需调整。

---

## 切换模型后端

如需切换到其他模型提供商，只需修改 [`llm_config.py`](llm_config.py) 中的对应分支：

**示例：D3/D4-5 改用 Google Gemini**

1. **安装依赖**: `pip install langchain-google-genai`
2. **修改代码**:
```python
# 在 get_llm() 的 use_local=False 分支中
from langchain_google_genai import ChatGoogleGenerativeAI
return ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.0,
    max_tokens=512,
)
```
3. **更新 .env**: 添加有效的 `GOOGLE_API_KEY`。

---

## 📊 成本估算参考

| 模块 | API | 单次成本估算 | 频率 | 月均成本 (低频) |
|------|-----|--------|------|--------|
| D1 | 本地 Ollama | ¥0 | 1× | ¥0 |
| D3 | 千问 Embedding | ¥0.0002/千字 | 1× | ¥0.01 |
| D3 | 千问 LLM | ¥0.003/千字 | 1× | ¥0.05 |
| D4 | 千问 Turbo | ¥0.01/千字 | 1× | ¥0.5 |
| **总计** | | | | **~¥0.56** |

*注：基于1,000字案例文本、单次调用估算。D1 使用本地模型可进一步降低成本。*

---

*最后更新：2025-05-13*
*关键改进：混合架构说明、数据清洗机制、故障排查指南*
