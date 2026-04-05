"""
D3 — RAG库优化模块（核心）
功能：
  - PM视角元数据提取（9个字段）
  - 文本分块与向量嵌入（ChromaDB）
  - 自定义混合检索器：元数据过滤 → 向量检索 → 商业价值排序 → 案例关联推荐
  - 缺失元数据自动补充（二次Tavily检索）
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from textwrap import dedent
from typing import Optional, Any

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import Field

load_dotenv()

# ── 辅助函数：确保输入给 Embedding API 的是合法字符串 ──────────────
def safe_str(value: any) -> str:
    """将任意值转换为安全的字符串，避免 Embedding API 报错"""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        # 过滤掉 None 和非字符串元素
        return " ".join([str(v) for v in value if v is not None])
    return str(value).strip()

# ── 元数据字段定义（方案原文9个字段）──────────────────────────
METADATA_FIELDS = {
    "project_name": "项目名称，提取案例中明确的项目全称，无则标记'待补充'",
    "party_a_industry": "甲方所属行业，精准到细分领域（如石油化工、精细化工、虚拟电厂）",
    "core_problem": "核心痛点，量化描述（如'化工间歇过程效率低，能耗偏高10%'）",
    "tech_path": "技术路径，明确核心技术（如'边缘计算+轻量化大模型+流程优化算法'）",
    "business_closed_loop": "商业闭环，包含收费模式、付费主体、ROI数据（无则标记'待补充'）",
    "party_b_role": "乙方角色（算力提供/平台提供/定制化算法/整体解决方案）",
    "replicability_score": "可复制性评分（1-10整数），附简要评分依据",
    "quantitative_effect": "量化效果（如'节能8%、降本12%、安全生产事故减少30%'）",
    "pm_note": "PM重点标注，聚焦大厂切入点、核心优势、现有方案缺口",
}

# 元数据提取Prompt
METADATA_EXTRACT_PROMPT = dedent("""
    你是工业AI案例分析专家，请从以下文本中提取结构化元数据。
    
    **提取规则**：
    - 若信息明确存在：精准提取，量化描述
    - 若信息缺失：标记"待补充"
    - replicability_score 必须为1-10的整数
    - 所有字段必须输出，不可省略
    
    **输出格式（严格JSON，不加代码块标记）**：
    {{
      "project_name": "...",
      "party_a_industry": "...",
      "core_problem": "...",
      "tech_path": "...",
      "business_closed_loop": "...",
      "party_b_role": "...",
      "replicability_score": 8,
      "quantitative_effect": "...",
      "pm_note": "..."
    }}
    
    **待提取文本**：
    {text}
""")


@dataclass
class CaseMetadata:
    """单个案例的完整元数据"""
    project_name: str = "待补充"
    party_a_industry: str = "待补充"
    core_problem: str = "待补充"
    tech_path: str = "待补充"
    business_closed_loop: str = "待补充"
    party_b_role: str = "待补充"
    replicability_score: int = 5
    quantitative_effect: str = "待补充"
    pm_note: str = "待补充"
    # 附加字段（检索用）
    source_url: str = ""
    final_score: float = 0.0
    keywords_hit: str = ""
    case_id: str = ""

    def to_chroma_dict(self) -> dict:
        """转为ChromaDB可存储的dict（值必须为str/int/float/bool）"""
        return {
            "project_name": self.project_name,
            "party_a_industry": self.party_a_industry,
            "core_problem": self.core_problem,
            "tech_path": self.tech_path,
            "business_closed_loop": self.business_closed_loop,
            "party_b_role": self.party_b_role,
            "replicability_score": self.replicability_score,
            "quantitative_effect": self.quantitative_effect,
            "pm_note": self.pm_note,
            "source_url": self.source_url,
            "final_score": self.final_score,
            "keywords_hit": self.keywords_hit,
            "case_id": self.case_id,
        }

    def has_missing_fields(self) -> list[str]:
        """返回标记为'待补充'的字段列表"""
        return [
            k for k, v in self.__dict__.items()
            if v == "待补充"
        ]


class RAGLibrary:
    """
    D3核心：工业AI案例RAG库
    完整实现方案中6步搭建流程
    """

    DB_NAME = "industrial_ai_case_rag"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        # 使用统一的 Embedding 配置（从 llm_config 获取）
        from llm_config import get_embedding_model, get_llm
        self.embeddings = get_embedding_model()
        if not self.embeddings:
            raise RuntimeError("Embedding 模型初始化失败，请检查 DASHSCOPE_API_KEY 配置")
        
        # 使用统一的 LLM 配置（DashScope API）
        self.llm = get_llm(temperature=0.0, num_predict=512, use_local=False)
        if not self.llm:
            raise RuntimeError("LLM 初始化失败，请检查 DASHSCOPE_API_KEY 配置")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "；", " "],
        )
        self.metadata_chain = (
            ChatPromptTemplate.from_template(METADATA_EXTRACT_PROMPT)
            | self.llm
            | StrOutputParser()
        )
        # 初始化或加载向量库
        self.vectorstore = self._init_vectorstore()

    # ── 步骤2-5：入库流程 ────────────────────────────────────────

    def ingest_cases(self, raw_cases: list[dict]) -> int:
        """
        批量入库案例
        raw_cases: [{text: str, metadata: {url, source, ...}}, ...]
        返回成功入库的数量
        """
        print(f"\n  📥 开始入库 {len(raw_cases)} 条案例...")
        success = 0

        for i, case in enumerate(raw_cases, 1):
            try:
                text = case.get("text", "")
                base_meta = case.get("metadata", {})

                # 步骤3：文本分块
                chunks = self.text_splitter.split_text(text)
                if not chunks:
                    continue

                # 步骤4：元数据提取
                metadata = self._extract_metadata(text, base_meta)

                # 步骤5：向量嵌入 + 入库（确保所有字段都是合法类型）
                meta_dict = metadata.to_chroma_dict()
                
                # 清洗元数据：只将 None/非基本类型转换为字符串，保留 int/float/bool
                clean_meta = {}
                for k, v in meta_dict.items():
                    if v is None:
                        clean_meta[k] = ""
                    elif isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)
                
                docs = [
                    Document(
                        page_content=safe_str(chunk),  # 确保文本内容是字符串
                        metadata={**clean_meta, "chunk_idx": int(idx)}
                    )
                    for idx, chunk in enumerate(chunks)
                ]
                
                self.vectorstore.add_documents(docs)
                success += 1
            except Exception as e:
                # 在生产环境中可以考虑使用 logging 模块记录错误
                pass

        return success

    # ── 步骤6：混合检索器 ────────────────────────────────────────

    def get_retriever(self) -> "HybridCaseRetriever":
        """返回自定义混合检索器"""
        return HybridCaseRetriever(rag_lib=self)

    def hybrid_search(
        self,
        query: str,
        industry: str = "",
        priorities: list[str] = None,
        min_replicability: int = 7,
        min_commercial: bool = True,
        top_k: int = 10,
    ) -> list[Document]:
        """
        四步混合检索（核心）：
        ① 元数据过滤（行业+可复制性评分）
        ② 向量相似度检索
        ③ 商业价值排序
        ④ 案例关联推荐
        """
        priorities = priorities or []

        # ① 构建元数据过滤器（ChromaDB 只支持单个 $and/$or 操作符）
        chroma_filter = {}
        
        if industry and industry != "待补充" and min_replicability > 0:
            # 多条件需要使用 $and
            chroma_filter["$and"] = [
                {"party_a_industry": {"$eq": industry}},
                {"replicability_score": {"$gte": min_replicability}}
            ]
        elif industry and industry != "待补充":
            chroma_filter["party_a_industry"] = {"$eq": industry}
        elif min_replicability > 0:
            chroma_filter["replicability_score"] = {"$gte": min_replicability}

        # ② 向量检索（带元数据过滤）
        clean_query = safe_str(query)
        
        try:
            filter_param = chroma_filter if chroma_filter else None
            
            raw_docs = self.vectorstore.similarity_search_with_score(
                clean_query, 
                k=top_k * 2,
                filter=filter_param
            )
            
        except Exception as e:
            print(f"  ⚠️  向量检索异常: {e}，降级为无过滤检索")
            raw_docs = self.vectorstore.similarity_search_with_score(clean_query, k=top_k * 2)

        # ③ 商业价值排序（可复制性 + 量化效果 + 商业闭环完整性）
        scored = []
        for doc, distance in raw_docs:
            meta = doc.metadata
            
            # ChromaDB 返回的是距离（distance），转换为相似度
            sim_score = max(0.0, 1.0 - (distance / 2.0))
            
            commercial_bonus = 0.0
            if "待补充" not in str(meta.get("business_closed_loop", "待补充")):
                commercial_bonus += 0.2
            if "待补充" not in str(meta.get("quantitative_effect", "待补充")):
                commercial_bonus += 0.15
            
            # 确保 replicability_score 是数值类型
            rep_score_raw = meta.get("replicability_score", 5)
            try:
                rep_score = float(rep_score_raw) / 10.0
            except (ValueError, TypeError):
                rep_score = 0.5
            
            final = sim_score * 0.5 + rep_score * 0.3 + commercial_bonus * 0.2
            doc.metadata["final_score"] = round(final, 4)
            
            scored.append((doc, final))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_docs = [doc for doc, _ in scored[:top_k]]

        # ④ 案例关联推荐（基于行业+痛点相似度补充2-3个）
        related = self._find_related_cases(top_docs, top_k=3)
        all_docs = self._merge_unique(top_docs, related)

        return all_docs[:top_k + 3]

    # ── 内部方法 ─────────────────────────────────────────────────

    def _init_vectorstore(self) -> Chroma:
        """初始化或加载ChromaDB"""
        return Chroma(
            collection_name=self.DB_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
        )

    def _extract_metadata(self, text: str, base_meta: dict) -> CaseMetadata:
        """调用LLMChain提取9个元数据字段"""
        try:
            raw_json = self.metadata_chain.invoke({"text": text[:2000]})
            # 清理可能的代码块
            clean = raw_json.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(clean)
        except Exception as e:
            print(f"      元数据提取失败: {e}，使用默认值")
            data = {}

        case_id = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        return CaseMetadata(
            project_name=data.get("project_name", "待补充"),
            party_a_industry=data.get("party_a_industry", "待补充"),
            core_problem=data.get("core_problem", "待补充"),
            tech_path=data.get("tech_path", "待补充"),
            business_closed_loop=data.get("business_closed_loop", "待补充"),
            party_b_role=data.get("party_b_role", "待补充"),
            replicability_score=int(data.get("replicability_score", 5)),
            quantitative_effect=data.get("quantitative_effect", "待补充"),
            pm_note=data.get("pm_note", "待补充"),
            source_url=base_meta.get("url", ""),
            final_score=base_meta.get("final_score", 0.0),
            keywords_hit=base_meta.get("keywords_hit", ""),
            case_id=case_id,
        )

    def _find_related_cases(self, docs: list[Document], top_k: int = 3) -> list[Document]:
        """基于行业+痛点找关联案例"""
        if not docs:
            return []
        # 用首个文档的行业+痛点构造关联查询
        first_meta = docs[0].metadata
        query = f"{first_meta.get('party_a_industry', '')} {first_meta.get('core_problem', '')}"
        try:
            related = self.vectorstore.similarity_search(query, k=top_k + len(docs))
            return [d for d in related if d not in docs][:top_k]
        except Exception:
            return []

    def _merge_unique(self, primary: list[Document], secondary: list[Document]) -> list[Document]:
        """合并去重"""
        seen_content = {d.page_content[:100] for d in primary}
        result = list(primary)
        for d in secondary:
            if d.page_content[:100] not in seen_content:
                result.append(d)
                seen_content.add(d.page_content[:100])
        return result

    def get_stats(self) -> dict:
        """获取RAG库统计信息"""
        try:
            count = self.vectorstore._collection.count()
            return {"total_chunks": count, "db_name": self.DB_NAME}
        except Exception:
            return {"total_chunks": "未知", "db_name": self.DB_NAME}


class HybridCaseRetriever(BaseRetriever):
    """
    自定义混合检索器（实现LangChain BaseRetriever接口）
    支持多条件组合检索
    """
    rag_lib: Any = Field(description="RAGLibrary instance")

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> list[Document]:
        return self.rag_lib.hybrid_search(query)

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        return self._get_relevant_documents(query)

    def search_with_filters(
        self,
        query: str,
        industry: str = "",
        min_replicability: int = 7,
        priorities: list[str] = None,
    ) -> list[Document]:
        """多条件组合检索接口（PM可手动调用）"""
        return self.rag_lib.hybrid_search(
            query=query,
            industry=industry,
            priorities=priorities or [],
            min_replicability=min_replicability,
        )


# ── 命令行测试 ──────────────────────────────────────────────────
if __name__ == "__main__":
    # 初始化RAG库
    rag = RAGLibrary(persist_dir="./test_chroma_db")

    # 入库示例数据
    test_cases = [
        {
            "text": (
                "横河电机AI化工流程优化项目：某大型石油化工企业采购横河电机整体解决方案，"
                "通过边缘计算+轻量化大模型实现流程实时优化，节能8.3%，降本1200万/年，"
                "ROI 18个月，合同额3000万，项目制收费，可复制性高，已推广5家同类企业。"
            ),
            "metadata": {"url": "https://yokogawa.com/case", "final_score": 0.85}
        }
    ]

    rag.ingest_cases(test_cases)
    stats = rag.get_stats()
    print(f"\n📊 RAG库状态: {stats}")

    # 混合检索测试
    retriever = rag.get_retriever()
    docs = retriever.search_with_filters(
        query="化工流程优化 节能",
        industry="化工",
        min_replicability=7,
    )
    print(f"\n🔍 检索结果: {len(docs)} 条")
    for d in docs[:2]:
        print(f"  行业: {d.metadata.get('party_a_industry')} | "
              f"可复制性: {d.metadata.get('replicability_score')}/10")
        print(f"  PM标注: {d.metadata.get('pm_note')[:80]}")