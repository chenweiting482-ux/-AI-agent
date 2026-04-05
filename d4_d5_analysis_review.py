"""
D4 — CrewAI深度分析层 + D5 AutoGen审核层
CrewAI角色：AI产品解决方案分析师 / 行业研究员 / 商业分析师 / 机会扫描员
AutoGen角色：PM Reviewer（打回重写直到达标）`
"""

import os
import re
from textwrap import dedent
from datetime import datetime

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

load_dotenv()

# ── 配置 CrewAI 使用千问 API ────────────────────────────────────
os.environ["OPENAI_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "")
os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
os.environ["OPENAI_MODEL_NAME"] = "qwen-turbo"


# ═══════════════════════════════════════════════════════════════
# D4：CrewAI 四角色分析层
# ═══════════════════════════════════════════════════════════════

class IndustryAnalysisCrew:
    """
    四角色协作分析流水线（方案升级版）：
    AI产品解决方案分析师 → 行业研究员 → 商业分析师 → 机会扫描员
    重点：产品解决方案深度拆解（区别于普通案例汇总）
    """

    def __init__(self):
        # CrewAI will use environment-configured LLM or defaults
        self._build_agents()

    def _build_agents(self):
        # ── Agent 1：AI产品解决方案分析师（新增核心角色）────────
        self.solution_analyst = Agent(
            role="AI产品解决方案分析师",
            goal=(
                "从案例中深度拆解AI产品解决方案的核心架构，"
                "提炼可复用的解决方案亮点，对比不同案例的方案差异，"
                "识别现有方案的技术短板和改进空间。"
            ),
            backstory=dedent("""
                你有8年AI产品落地经验，深度参与过工业场景下10+个AI解决方案的设计与实施。
                你擅长从产品视角拆解解决方案：核心功能是什么？技术架构如何设计？
                适配哪些场景？实施门槛多高？与竞品方案相比优劣势如何？
                你的分析必须有具体数据支撑，拒绝模糊描述。
            """),
            verbose=True,
            allow_delegation=False,
        )

        # ── Agent 2：工业领域行业研究员 ──────────────────────────
        self.industry_researcher = Agent(
            role="工业领域行业研究员",
            goal=(
                "结合工业细分领域特性（化工/电力/钢铁），"
                "分析AI解决方案的行业适配性、痛点覆盖度和优化空间，"
                "补充行业背景知识，让分析更具行业深度。"
            ),
            backstory=dedent("""
                你有5年工业行业研究经验，曾深度调研过化工、电力、钢铁等多个制造业细分领域。
                你熟悉各行业的生产流程、核心痛点、数字化程度和决策者关注点。
                你的分析需体现行业适配性：该方案是否真正解决了行业核心痛点？
                在该行业推广的难点和阻力在哪里？
            """),
            verbose=True,
            allow_delegation=False,
        )

        # ── Agent 3：商业分析师 ───────────────────────────────────
        self.commercial_analyst = Agent(
            role="商业分析师",
            goal=(
                "分析每个案例的商业闭环逻辑、收费模式和ROI提升路径，"
                "评估解决方案的商业可行性和市场规模，"
                "输出具体的商业价值量化数据。"
            ),
            backstory=dedent("""
                你有6年B2B科技产品商业化经验，擅长分析工业AI项目的商业模式。
                你特别关注：客户付费意愿/付费能力如何？收费模式（项目制/SaaS/数据订阅）哪种更适配？
                ROI回收周期是否合理？规模化后的单位经济能否成立？
                每个商业结论必须有数据支撑，如：合同额、节省成本/年、ROI周期。
            """),
            verbose=True,
            allow_delegation=False,
        )

        # ── Agent 4：大厂机会扫描员 ──────────────────────────────
        self.opportunity_scanner = Agent(
            role="互联网大厂机会扫描员",
            goal=(
                "站在互联网大厂（云原生/大模型/算力）视角，"
                "识别现有AI解决方案的能力缺口，"
                "给出具体的大厂切入思路、差异化优势和落地难点建议。"
            ),
            backstory=dedent("""
                你曾在某头部互联网大厂工业AI业务线担任产品总监，
                深度了解大厂在工业场景的优势（云原生部署/大模型能力/算力资源）
                和劣势（行业Know-how不足/场景适配成本高/销售周期长）。
                你的切入点分析必须具体：大厂能做什么？怎么做比现有方案更好？
                在哪个环节切入最有效率？落地会遇到哪些阻力？
            """),
            verbose=True,
            allow_delegation=False,
        )

    def _build_tasks(self, cases_text: str, industry: str, parsed_req_summary: str) -> list[Task]:
        """构建四个串行任务"""

        # ── Task 1：解决方案深度拆解 ─────────────────────────────
        task_solution = Task(
            description=dedent(f"""
                基于以下高价值工业AI案例，进行产品解决方案深度拆解。
                
                调研背景：{parsed_req_summary}
                目标行业：{industry}
                
                案例内容：
                {cases_text}
                
                分析维度（每个案例必须覆盖）：
                1. **核心功能**：AI解决方案的主要功能模块
                2. **技术架构**：数据层→算法层→应用层的技术路径
                3. **适配场景**：适用的具体生产场景和前提条件
                4. **实施流程**：从立项到上线的关键步骤和时间周期
                5. **核心优势**：相比传统方案/竞品的明确优势（有数据）
                6. **核心劣势**：现有方案的技术短板和局限性
                7. **落地门槛**：数据要求/硬件要求/人员要求
                8. **方案对比**：不同案例间的解决方案差异对比
                
                输出：结构化的解决方案拆解报告（每个案例单独分析）
            """),
            agent=self.solution_analyst,
            expected_output="每个案例的产品解决方案拆解报告，含技术架构、优劣势、落地门槛",
        )

        # ── Task 2：行业适配性分析 ───────────────────────────────
        task_industry = Task(
            description=dedent(f"""
                基于解决方案拆解结果，分析{industry}行业的适配性和优化空间。
                
                分析要点：
                1. 该行业核心生产痛点（量化描述，如"能耗偏高X%、安全事故率Y‰"）
                2. 案例中的AI方案是否真正覆盖了核心痛点
                3. 行业特殊性对方案落地的制约因素（如安全合规、数据孤岛）
                4. {industry}细分场景中，哪些子场景AI方案最成熟/最有推广潜力
                5. 行业政策环境对AI落地的影响（利好/利空）
                
                要求：每个结论必须引用具体行业数据，拒绝泛泛而谈。
            """),
            agent=self.industry_researcher,
            expected_output="行业适配性分析报告，含核心痛点、适配评估、政策环境",
            context=[task_solution],
        )

        # ── Task 3：商业价值深度分析 ─────────────────────────────
        task_commercial = Task(
            description=dedent(f"""
                基于前两步分析，对{industry}行业AI方案进行商业价值量化分析。
                
                分析框架：
                1. **收费模式对比**：案例中各种收费模式（项目制/SaaS/数据订阅）
                   的优劣势和适用条件
                2. **ROI分析**：
                   - 客户侧ROI：节省成本/年、回收周期
                   - 乙方侧ROI：合同额、毛利率估算
                3. **市场规模估算**：
                   - 目标客户量级（如：全国化工企业约X家，潜在市场Y亿）
                4. **付费决策逻辑**：工业客户如何做AI采购决策（关键因素、关键人）
                5. **商业风险**：竞争风险、政策风险、技术替代风险
                
                输出：商业价值分析 + 关键商业指标汇总表
            """),
            agent=self.commercial_analyst,
            expected_output="商业价值量化分析，含收费模式、ROI数据、市场规模、商业风险",
            context=[task_solution, task_industry],
        )

        # ── Task 4：大厂切入点分析（核心输出）───────────────────
        task_opportunity = Task(
            description=dedent(f"""
                综合前三步分析，给出互联网大厂切入{industry}场景的专项分析。
                
                切入点分析框架（方案原文标准）：
                1. **现有方案缺口**：传统方案（如横河电机、Honeywell）的技术局限
                2. **大厂差异化优势**：云原生部署/大模型能力/算力/生态资源
                3. **具体切入思路**（每个方向给出具体路径）：
                   - 切入角色：平台提供商/算力赋能/大模型供应商/整体方案商
                   - 切入时机：哪个阶段介入（如：数据底座阶段）
                   - 切入产品：具体产品/服务形态
                4. **落地难点与应对**：
                   - 难点1：行业Know-how不足 → 应对：...
                   - 难点2：数据安全顾虑 → 应对：...
                5. **优先推荐方向**（TOP3，排序并说明理由）
                
                参考案例背景（来自解决方案分析）：[引用上下文中的具体案例数据]
                
                输出：大厂切入点专项分析报告（这是整个报告最核心的部分）
            """),
            agent=self.opportunity_scanner,
            expected_output="大厂切入点专项分析，含差异化优势、具体切入路径、落地难点、TOP3推荐方向",
            context=[task_solution, task_industry, task_commercial],
        )

        return [task_solution, task_industry, task_commercial, task_opportunity]

    def run(
        self,
        cases_text: str,
        industry: str,
        parsed_req_summary: str,
    ) -> str:
        """执行四角色分析，返回完整Markdown报告草稿"""
        tasks = self._build_tasks(cases_text, industry, parsed_req_summary)

        crew = Crew(
            agents=[
                self.solution_analyst,
                self.industry_researcher,
                self.commercial_analyst,
                self.opportunity_scanner
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=8,
        )

        result = crew.kickoff()
        raw_output = str(result.raw) if hasattr(result, "raw") else str(result)

        # 用Writer Agent格式化为标准Markdown报告
        return self._format_to_report(raw_output, industry)

    def _format_to_report(self, analysis_text: str, industry: str) -> str:
        """将CrewAI输出格式化为PM专属标准报告"""
        date_str = datetime.now().strftime("%Y年%m月%d日")
        report = dedent(f"""
            # {industry}行业AI落地案例深度调研报告
            **生成日期**：{date_str} | **调研视角**：互联网大厂PM | **框架**：LangChain+CrewAI

            ---

            ## 执行摘要
            > *(由AutoGen审核后自动生成)*

            ---

            {analysis_text}

            ---

            ## 免责声明
            > 本报告基于公开信息检索与AI分析生成，数据仅供参考，请结合一手调研验证。
        """).strip()
        return report


# ═══════════════════════════════════════════════════════════════
# D5：AutoGen 质量审核层
# ═══════════════════════════════════════════════════════════════

# 报告质量评分规则（100分制）
QUALITY_RUBRIC = {
    "solution_depth": {
        "desc": "包含产品解决方案深度拆解（技术架构+优劣势）",
        "weight": 25,
        "check": lambda t: any(kw in t for kw in ["技术架构", "核心功能", "优势", "劣势", "解决方案"]),
    },
    "quantitative_data": {
        "desc": "包含≥3个量化数据（数字+单位）",
        "weight": 25,
        "check": lambda t: len(re.findall(r"\d+[\.\d]*\s*(MW|GWh|亿|万|%|个|项|元|年|月|家)", t)) >= 3,
    },
    "bigco_entry": {
        "desc": "包含大厂切入点专项分析",
        "weight": 20,
        "check": lambda t: any(kw in t for kw in ["切入点", "大厂", "云原生", "切入思路", "差异化优势"]),
    },
    "commercial_logic": {
        "desc": "包含商业闭环/收费模式/ROI分析",
        "weight": 15,
        "check": lambda t: any(kw in t for kw in ["ROI", "收费", "商业闭环", "付费", "合同"]),
    },
    "min_length": {
        "desc": "报告字数≥1000字",
        "weight": 15,
        "check": lambda t: len(t) >= 1000,
    },
}

PASS_THRESHOLD = 75


def score_report(text: str) -> tuple[int, list[str]]:
    total, fails = 0, []
    for key, rule in QUALITY_RUBRIC.items():
        if rule["check"](text):
            total += rule["weight"]
        else:
            fails.append(f"❌ {rule['desc']}（-{rule['weight']}分）")
    return total, fails


class AutoGenReviewer:
    """
    D5：规则引擎质量审核层（本地化方案，无API依赖）
    逻辑：纯规则评分 + 自动打分 + 反馈生成
    """
    MAX_ROUNDS = 1  # 简化为一轮评分

    def __init__(self):
        """本地化审核器，无需任何API配置"""
        pass

    def review_and_finalize(self, draft: str) -> str:
        """主审核方法：规则评分 + 自动反馈"""
        print(f"\n  🔍 [D5] 规则引擎质量审核启动")

        # 规则打分
        score, fails = score_report(draft)
        print(f"  📊 质量评分: {score}/100")

        if score >= PASS_THRESHOLD:
            print(f"  🎉 审核通过！")
            return self._stamp(draft, score, passed=True)
        else:
            for f in fails:
                print(f"    {f}")
            print(f"  ⚠️  审核未通过（{score}/100），已生成反馈")
            return self._stamp(draft, score, passed=False)

    def _stamp(self, report: str, score: int, passed: bool) -> str:
        """添加审核戳章"""
        status = "✅ 审核通过" if passed else "⚠️ 审核未通过"
        return report + dedent(f"""

            ---
            > **审核记录** | {status} | 得分: {score}/100
            > 评分维度: 解决方案深度(25) + 量化数据(25) + 大厂切入(20) + 商业逻辑(15) + 字数(15)
        """)


# ── 命令行测试 ──────────────────────────────────────────────────
if __name__ == "__main__":
    # 测试CrewAI
    crew = IndustryAnalysisCrew()
    sample_cases = """
    【案例1】横河电机AI化工优化：节能8.3%，降本1200万/年，ROI 18个月，合同额3000万
    【案例2】某虚拟电厂平台：聚合50MW，月均辅助服务收益300万，SaaS抽佣15%
    """
    draft = crew.run(
        cases_text=sample_cases,
        industry="化工",
        parsed_req_summary="行业=化工 | 需求=落地方向案例 | 优先级=标杆案例+节能数据"
    )

    # 测试AutoGen
    reviewer = AutoGenReviewer()
    final = reviewer.review_and_finalize(draft)
    print(f"\n✅ 最终报告长度: {len(final)} 字")