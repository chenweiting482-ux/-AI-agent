"""
D2 — 精准检索模块
三重过滤是纯规则代码，完全不需要LLM。
Tavily API可选：有Key则真实检索，无Key则用Mock数据。
"""

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from llm_config import get_llm   # D2实际不用LLM，但统一导入方式保持一致
from langchain_community.tools.tavily_search import TavilySearchResults


COMMERCIAL_SIGNALS = [
    "ROI", "付费", "合同", "节能", "降本", "效率提升",
    "Energy Saving", "Cost Reduction", "Paid", "Revenue",
    "亿元", "万元", "百万", "%", "增长", "减少",
    "商业化", "规模化", "SaaS", "项目制", "订阅"
]
NON_COMMERCIAL_SIGNALS = [
    "政府补贴为主", "纯研究", "概念验证", "POC only",
    "实验室阶段", "无明确收费", "开源免费"
]


@dataclass
class CaseArticle:
    title: str
    url: str
    content: str
    source: str = ""
    commercial_score: float = 0.0
    relevance_score: float = 0.0
    time_score: float = 0.0
    final_score: float = 0.0
    keywords_hit: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


class IndustrySearchTool:
    """
    D2核心：精准检索工具
    注意：三重过滤是纯规则代码，不调用任何LLM，速度快且零成本。
    """

    def __init__(self, max_results_per_query: int = 8):
        # Tavily初始化（可选）
        self.tavily = None
        self.use_mock = False
        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key:
            try:
                self.tavily = TavilySearchResults(
                    max_results=max_results_per_query,
                    api_key=tavily_key,
                    search_depth="advanced",
                    include_answer=False,
                    include_raw_content=True,
                )
                print("  ✅ Tavily API 已连接")
            except Exception as e:
                print(f"  ⚠️  Tavily初始化失败，降级Mock：{str(e)[:60]}")
                self.use_mock = True
        else:
            print("  ⚠️  未配置TAVILY_API_KEY，使用Mock数据")
            self.use_mock = True

    def search_and_filter(
        self,
        keyword_combo: list[str],
        priorities: list[str],
        industry: str,
        max_cases: int = 20,
    ) -> list[CaseArticle]:
        print(f"\n  🔎 开始检索 | 关键词: {' + '.join(keyword_combo[:5])}")

        if self.use_mock:
            print(f"  📦 Mock模式（{industry}行业演示数据）")
            cases = self._get_mock_cases(industry, keyword_combo)
            filtered = self._filter_pipeline(cases, keyword_combo, priorities)
            filtered.sort(key=lambda x: x.final_score, reverse=True)
            print(f"  ✅ Mock返回: {len(filtered[:max_cases])} 条")
            return filtered[:max_cases]

        queries = self._build_queries(keyword_combo, industry)
        raw_results: list[CaseArticle] = []
        for query in queries:
            print(f"  📡 查询: {query}")
            try:
                results = self.tavily.invoke(query)
                for r in results:
                    raw_results.append(CaseArticle(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        content=(r.get("raw_content") or r.get("content", ""))[:3000],
                        source=r.get("url", "").split("/")[2] if r.get("url") else "",
                    ))
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️  查询失败: {e}")
                raw_results.extend(self._get_mock_cases(industry, keyword_combo))

        raw_results = self._deduplicate(raw_results)
        print(f"  📦 去重后: {len(raw_results)} 条")

        filtered = self._filter_pipeline(raw_results, keyword_combo, priorities)
        filtered.sort(key=lambda x: x.final_score, reverse=True)
        result = filtered[:max_cases]
        print(f"  ✅ 过滤后保留: {len(result)} 条")
        return result

    # ── 三重过滤（纯规则，无LLM）────────────────────────────────

    def _filter_pipeline(self, articles, keywords, priorities):
        passed = []
        for art in articles:
            art.time_score = self._score_timeliness(art.content)
            art.commercial_score = self._score_commercial_value(art.content)
            if art.commercial_score < 0.15:
                continue
            art.relevance_score = self._score_relevance(art.content, keywords, priorities)
            art.keywords_hit = [kw for kw in keywords if kw.lower() in art.content.lower()]
            art.final_score = art.relevance_score * 0.5 + art.commercial_score * 0.3 + art.time_score * 0.2
            passed.append(art)
        return passed

    def _score_timeliness(self, text: str) -> float:
        score = 0.3
        months_hits = re.findall(r"(今年|本年|最新|recently|2024|2025|近期|最近)", text, re.IGNORECASE)
        years = re.findall(r"20(2[3-9]|[3-9]\d)", text)
        if months_hits:
            score = 0.8
        elif years:
            latest = max(int(y) for y in years)
            score = 0.7 if latest >= 24 else 0.5
        return min(score, 1.0)

    def _score_commercial_value(self, text: str) -> float:
        for neg in NON_COMMERCIAL_SIGNALS:
            if neg in text:
                return 0.0
        hit_count = sum(1 for sig in COMMERCIAL_SIGNALS if sig.lower() in text.lower())
        has_numbers = bool(re.search(r"\d+[\.\d]*\s*(%|万|亿|MW|GWh|kWh)", text))
        return min(hit_count * 0.12 + (0.3 if has_numbers else 0.0), 1.0)

    def _score_relevance(self, text: str, keywords: list, priorities: list) -> float:
        text_lower = text.lower()
        total = sum(1.0 for kw in keywords if kw.lower() in text_lower)
        total += sum(2.0 for p in priorities if p.lower() in text_lower)
        return min(total / max(len(keywords) + len(priorities) * 2, 1), 1.0)

    def _build_queries(self, keywords: list, industry: str) -> list:
        base = " ".join(keywords[:4])
        return [
            f"{base} case study 2024 2025",
            f"{industry} AI落地方案 标杆案例 商业化",
            f"{industry} artificial intelligence ROI benchmark project",
        ]

    def _deduplicate(self, articles):
        seen, result = set(), []
        for art in articles:
            if art.url not in seen and art.url:
                seen.add(art.url); result.append(art)
        return result

    def _get_mock_cases(self, industry: str, keywords: list) -> list[CaseArticle]:
        mock_data = {
            "化工": [
                ("横河电机石油化工流程优化",
                 "横河电机AI流程优化：边缘计算+轻量化大模型，节能8.3%，降本1200万/年，ROI18个月，合同3000万，已推广5家。"),
                ("精细化工质量预测系统",
                 "精细化工AI质量预测：减少报废35%，年节省800万，SaaS月费30万，14月回本，标杆案例。"),
                ("煤化工能耗优化",
                 "煤化工能耗优化：降能耗12%，年降本2000万，B2B SaaS年费500万，3家头部落地。"),
            ],
            "虚拟电厂": [
                ("特来电VPP聚合平台",
                 "特来电VPP：聚合50MW，月均辅助服务收益300万，SaaS抽佣15%，可复制性8/10。"),
                ("分布式能源管理",
                 "分布式能源管理平台：聚合100MW，月均200万，云边协同+AI调度，ROI2.4年。"),
            ],
        }
        items = mock_data.get(industry, mock_data["化工"])
        return [
            CaseArticle(
                title=title, url=f"https://mock.com/{i}",
                content=content, source="mock",
                commercial_score=0.75, relevance_score=0.70,
                time_score=0.80, final_score=0.74,
                keywords_hit=keywords[:2],
            )
            for i, (title, content) in enumerate(items, 1)
        ]

    def format_for_rag(self, cases: list[CaseArticle]) -> list[dict]:
        return [
            {
                "text": f"标题: {c.title}\n\n{c.content}",
                "metadata": {
                    "url": c.url, "source": c.source,
                    "final_score": round(c.final_score, 3),
                    "keywords_hit": ",".join(c.keywords_hit),
                    "scraped_at": c.scraped_at,
                }
            }
            for c in cases
        ]


if __name__ == "__main__":
    tool = IndustrySearchTool()
    cases = tool.search_and_filter(
        keyword_combo=["化工", "AI", "流程优化", "节能", "ROI"],
        priorities=["标杆案例", "节能数据"],
        industry="化工", max_cases=10,
    )
    print(f"\n✅ 最终保留 {len(cases)} 条")
    for i, c in enumerate(cases[:3], 1):
        print(f"  [{i}] {c.title} | 综合:{c.final_score:.2f}")