"""
主入口 文件
触发：输入需求 → D1解析 → D2检索 → D3入库 → D4分析 → D5审核 → 输出报告
"""

import sys
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

# 导入各层模块
from d1_requirement_parser import RequirementParser
from d2_search_tool import IndustrySearchTool
from d3_rag_library import RAGLibrary
from d4_d5_analysis_review import IndustryAnalysisCrew, AutoGenReviewer

def run_agent(user_input: str, skip_clarification: bool = False) -> str:
    """  
    Args:
        user_input: 用户输入的调研需求
        skip_clarification: True=跳过模糊确认（自动化测试用）
    """
    print("\n" + "═" * 65)
    print("   工业AI案例调研Agent 启动")
    print(f"   输入需求: {user_input}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 65)

    # D1：需求解析
    print("\n【D1】需求解析模块...")
    parser = RequirementParser()
    req = parser.parse(user_input)

    if req.is_ambiguous and not skip_clarification:
        print(f"\n⚠️  需求模糊，请补充：\n{req.clarification_prompt}")
        user_clarify = input("\n请输入补充信息（直接回车跳过）: ").strip()
        if user_clarify:
            combined = f"{user_input} {user_clarify}"
            req = parser.parse(combined)

    if req.is_ambiguous:
        print("⚠️  需求仍不明确，使用默认参数继续...")
        req.industry = "化工"
        req.demand_type = "落地方向案例汇总"
        req.output_format = "标准化报告"
        req.priorities = ["标杆案例", "节能数据"]
        req.keyword_combo = ["化工", "AI", "流程优化", "节能", "ROI", "标杆案例"]

    print(f"✅ 解析完成:\n  {req.summary()}")

    #  D2：精准检索 
    print("\n【D2】精准检索模块（三重过滤）...")
    search_tool = IndustrySearchTool()
    cases = search_tool.search_and_filter(
        keyword_combo=req.keyword_combo,
        priorities=req.priorities,
        industry=req.industry,
        max_cases=20,
    )
    print(f"✅ 获取 {len(cases)} 条高价值案例")

    #  D3：RAG入库 + 混合检索 
    print("\n【D3】RAG库入库与混合检索...")
    rag = RAGLibrary(persist_dir="./chroma_db")
    raw_for_rag = search_tool.format_for_rag(cases)
    rag.ingest_cases(raw_for_rag)

    # 混合检索获取最精准案例（供CrewAI分析用）
    retriever = rag.get_retriever()
    query = req.to_search_query()
    top_docs = retriever.search_with_filters(
        query=query,
        industry=req.industry,
        min_replicability=6,
        priorities=req.priorities,
    )
    stats = rag.get_stats()
    print(f"✅ RAG库: {stats['total_chunks']} 个分块 | 检索到 {len(top_docs)} 条精准案例")

    # 拼装供CrewAI使用的案例文本
    cases_text = _format_rag_docs(top_docs)
    if not cases_text.strip():
        # 兜底：直接使用D2原始结果
        cases_text = "\n\n".join([
            f"【案例{i+1}】{c.title}\n{c.content[:1000]}"
            for i, c in enumerate(cases[:8])
        ])

    # D4：CrewAI深度分析
    crew = IndustryAnalysisCrew()
    draft_report = crew.run(
        cases_text=cases_text[:6000],  # 控制Token消耗
        industry=req.industry,
        parsed_req_summary=req.summary(),
    )
    print("✅ CrewAI分析完成，报告初稿生成")

    #  D5：AutoGen质量审核 
    print("\n【D5】AutoGen PM审核层...")
    reviewer = AutoGenReviewer()
    final_report = reviewer.review_and_finalize(draft_report)
    print("✅ 报告审核完成")

    #输出保存 
    output_dir = Path("./output_reports")
    output_dir.mkdir(exist_ok=True)
    
    # 清理行业名称中的非法字符，确保目录名合法
    safe_industry = req.industry.replace("/", "_").replace("\\", "_").replace(":", "_").strip()
    
    # 创建行业子目录
    industry_dir = output_dir / safe_industry
    industry_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = industry_dir / f"{safe_industry}_调研报告_{timestamp}.md"
    filename.write_text(final_report, encoding="utf-8")

    print(f"\n{'═' * 65}")
    print(f"  🎉 报告已保存: {filename}")
    print(f"  📊 报告字数: {len(final_report)} 字")
    print("═" * 65)

    return final_report


def _format_rag_docs(docs) -> str:
    """格式化RAG检索文档"""
    parts = []
    for i, doc in enumerate(docs[:8], 1):
        meta = doc.metadata
        parts.append(
            f"【案例{i}】\n"
            f"行业: {meta.get('party_a_industry', '未知')}\n"
            f"核心痛点: {meta.get('core_problem', '未知')}\n"
            f"技术路径: {meta.get('tech_path', '未知')}\n"
            f"商业闭环: {meta.get('business_closed_loop', '未知')}\n"
            f"量化效果: {meta.get('quantitative_effect', '未知')}\n"
            f"可复制性: {meta.get('replicability_score', '?')}/10\n"
            f"PM标注: {meta.get('pm_note', '未知')}\n"
            f"原文摘要: {doc.page_content[:400]}\n"
        )
    return "\n---\n".join(parts)


#  CLI入口 
if __name__ == "__main__":
    # 支持命令行参数传入需求
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("\n🔍 请输入调研需求（如：AI+化工落地方向案例，产出报告）：\n> ").strip()
        if not user_query:
            # 默认演示需求
            user_query = "AI+化工的落地方向案例，产出报告，优先找有明确节能效果的标杆案例"

    run_agent(user_query)