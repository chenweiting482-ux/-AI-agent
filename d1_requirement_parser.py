"""
D1 — 需求解析模块（增强版）
LLM配置统一由 llm_config.py 管理，本文件不再硬写任何模型名。
支持细分行业、技术领域、公司范围、地域等多维度解析。
"""

import re
import time
from dataclasses import dataclass, field
from textwrap import dedent
from typing import Optional, List

from llm_config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ==================== 关键词矩阵（按细分领域组织）====================
KEYWORD_MATRIX = {
    "化工": {
        "sub_industries": ["石油化工", "精细化工", "煤化工", "化工新材料", "petrochemical", "fine chemicals"],
        "tech_domains": {
            "algorithm": ["Process Optimization", "Catalyst Optimization", "流程优化", "催化剂优化", "反应动力学建模"],
            "hardware": ["边缘计算设备", "传感器网络", "DCS系统", "PLC控制器"],
            "platform": ["工业互联网平台", "MES系统", "数字孪生", "工业PaaS"],
            "data": ["实时数据采集", "历史数据库", "时序数据分析", "异常检测"]
        },
        "commercial": ["ROI", "Energy Saving %", "Cost Reduction", "节能效果", "降本", "吨产品成本"],
        "priority": ["Benchmark", "Top Tier Enterprise", "标杆案例", "头部企业"],
    },
    "虚拟电厂": {
        "sub_industries": ["VPP", "Virtual Power Plant", "聚合资源", "需求侧响应", "分布式能源", "储能聚合"],
        "tech_domains": {
            "algorithm": ["负荷聚合", "AI调度", "预测算法", "load aggregation", "demand response"],
            "hardware": ["智能电表", "逆变器", "储能BMS", "边缘网关"],
            "platform": ["云平台", "SaaS平台", "能源管理系统", "交易平台"],
            "data": ["负荷预测", "电价预测", "气象数据", "用户行为分析"]
        },
        "commercial": ["电力市场化", "辅助服务收益", "MW聚合容量", "B2B SaaS", "平台收费"],
        "priority": ["电网接入", "政策合规", "大规模聚合", "可复制方案"],
    },
    "钢铁": {
        "sub_industries": ["炼铁", "炼钢", "轧制", "冶金", "blast furnace", "continuous casting"],
        "tech_domains": {
            "algorithm": ["高炉优化", "质量预测", "能耗管理", "Blast Furnace AI", "成分预测"],
            "hardware": ["高温传感器", "视觉检测", "机器人巡检", "红外测温"],
            "platform": ["智能制造平台", "质量追溯系统", "能源管理平台"],
            "data": ["工艺参数采集", "质量检测数据", "设备状态监测"]
        },
        "commercial": ["吨钢成本", "能耗kgce/t", "ROI", "降本增效", "良品率提升"],
        "priority": ["头部钢企", "规模化部署", "Benchmark", "宝武集团"],
    },
    "电力": {
        "sub_industries": ["新能源", "储能", "电网", "光伏", "风电", "火电", "核电"],
        "tech_domains": {
            "algorithm": ["预测性维护", "调度优化", "故障诊断", "predictive maintenance", "功率预测"],
            "hardware": ["智能终端", "保护装置", "储能系统", "充电桩"],
            "platform": ["电网调度系统", "运维管理平台", "电力交易平台"],
            "data": ["SCADA数据", "气象数据", "设备台账", "负荷曲线"]
        },
        "commercial": ["GWh", "MW", "度电成本", "LCOE", "电力现货", "峰谷价差"],
        "priority": ["国家电网", "头部电企", "政策项目", "五大发电集团"],
    },
    "汽车": {
        "sub_industries": ["整车制造", "零部件", "新能源汽车", "automotive", "动力电池", "智能驾驶"],
        "tech_domains": {
            "algorithm": ["预测性维护", "质量检测", "供应链优化", "路径规划", "缺陷检测"],
            "hardware": ["工业机器人", "AGV小车", "视觉相机", "激光雷达"],
            "platform": ["MES系统", "WMS仓储", "供应链协同平台", "车联网平台"],
            "data": ["生产节拍", "质量数据", "物流信息", "用户行为"]
        },
        "commercial": ["单车成本", "良品率", "交付周期", "OEE", "库存周转率"],
        "priority": ["主机厂", "Tier1供应商", "量产案例", "比亚迪", "特斯拉"],
    },
}

# 公司范围映射
COMPANY_SCOPE_MAP = {
    "国内": ["中国", "国内", "本土", "China", "domestic"],
    "国外": ["国外", "海外", "国际", "international", "overseas", "欧美"],
    "头部企业": ["头部", "龙头", "标杆", "top tier", "leading", "benchmark"],
    "中小企业": ["中小", "SME", "small medium", "初创"],
    "央企国企": ["央企", "国企", "state-owned", "central enterprise"],
    "民营企业": ["民营", "private", "民企"],
}

# 地域范围映射
REGION_MAP = {
    "华东": ["华东", "上海", "江苏", "浙江", "山东", "east china"],
    "华北": ["华北", "北京", "天津", "河北", "north china"],
    "华南": ["华南", "广东", "深圳", "south china"],
    "西南": ["西南", "四川", "重庆", "southwest"],
    "全国": ["全国", "中国", "nationwide"],
    "全球": ["全球", "国际", "worldwide", "global"],
}

# 技术领域关键词
TECH_DOMAIN_KEYWORDS = {
    "算法/AI": ["算法", "AI", "机器学习", "深度学习", "大模型", "algorithm", "machine learning", "deep learning", "LLM"],
    "硬件/设备": ["硬件", "设备", "传感器", "机器人", "hardware", "sensor", "robot"],
    "软件/平台": ["平台", "软件", "SaaS", "系统", "platform", "software", "system"],
    "数据/集成": ["数据", "集成", "接口", "database", "integration", "API"],
}


@dataclass
class ParsedRequirement:
    """结构化需求对象（增强版）"""
    # 基础维度
    industry: str                          # 主行业（如"化工"）
    sub_industry: str = ""                 # 细分行业（如"石油化工"）
    demand_type: str = "案例汇总"          # 需求类型
    output_format: str = "标准化报告"      # 输出形式
    
    # 新增维度
    tech_domain: str = ""                  # 技术领域（算法/硬件/平台/数据）
    company_scope: str = ""                # 公司范围（国内/国外/头部/中小）
    region: str = ""                       # 地域范围（华东/华北/全国/全球）
    
    priorities: list[str] = field(default_factory=list)
    keyword_combo: list[str] = field(default_factory=list)
    
    is_ambiguous: bool = False
    clarification_prompt: Optional[str] = None
    raw_input: str = ""
    llm_backend_used: str = ""

    def to_search_query(self) -> str:
        """生成搜索查询字符串"""
        parts = []
        if self.sub_industry:
            parts.append(self.sub_industry)
        elif self.industry:
            parts.append(self.industry)
        
        if self.tech_domain:
            parts.append(self.tech_domain)
        
        if self.company_scope:
            parts.append(self.company_scope)
        
        if self.region:
            parts.append(self.region)
        
        # 添加优先级关键词
        for p in self.priorities[:2]:
            parts.append(p)
        
        return " ".join(parts[:8])

    def summary(self) -> str:
        """生成人类可读的摘要"""
        backend = f" [via {self.llm_backend_used}]" if self.llm_backend_used else ""
        parts = [f"行业={self.industry}"]
        
        if self.sub_industry:
            parts.append(f"细分={self.sub_industry}")
        if self.tech_domain:
            parts.append(f"技术域={self.tech_domain}")
        if self.company_scope:
            parts.append(f"公司={self.company_scope}")
        if self.region:
            parts.append(f"地域={self.region}")
        
        parts.extend([
            f"需求={self.demand_type}",
            f"输出={self.output_format}",
            f"优先级={'、'.join(self.priorities)}"
        ])
        
        return " | ".join(parts) + backend + f"\n关键词组合：{' + '.join(self.keyword_combo[:6])}"


class RequirementParser:

    PARSE_PROMPT = dedent("""
        你是工业AI调研助手。从用户输入中提取关键信息，**严格按以下格式输出**：

        行业: XX
        细分行业: XX（若无则写"无"）
        需求类型: XX（落地方向/案例汇总/切入点分析/竞品对比）
        优先级: XX+XX
        关键词: "XX"+"XX"+"XX"

        **若输入太模糊**（少于10字或无明确行业），输出：
        AMBIGUOUS

        ---
        示例：
        输入：AI+石油化工催化剂优化，国外头部企业案例，华东地区
        输出：
        行业: 化工
        细分行业: 石油化工
        需求类型: 案例汇总
        优先级: 标杆案例+商业价值数据
        关键词: "石油化工"+"催化剂优化"+"国外企业"+"华东地区"+"ROI"

        ---
        输入：{{user_input}}
    """)

    def _extract_json(self, raw: str, original: str) -> ParsedRequirement:
        """从LLM输出中提取键值对，并结合规则引擎补充其他维度"""
        
        # 检查是否模糊
        if raw.strip().upper() == "AMBIGUOUS":
            return self._ambiguous(original)
        
        # 提取基础字段
        fields = {}
        for line in raw.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if key in ["行业", "细分行业", "需求类型", "优先级", "关键词"]:
                    fields[key] = value
        
        if not fields or "行业" not in fields:
            return self._fallback(original)
        
        # 解析优先级
        priorities_raw = fields.get("优先级", "标杆案例+商业价值数据")
        priorities = [p.strip() for p in priorities_raw.split("+") if p.strip()]
        
        # 解析关键词
        kw_raw = fields.get("关键词", "")
        keywords = [k.strip().strip('"').strip("'") for k in kw_raw.split("+") if k.strip()]
        
        # 创建基础对象
        req = ParsedRequirement(
            industry=fields.get("行业", "工业"),
            sub_industry=fields.get("细分行业", "") if fields.get("细分行业", "") != "无" else "",
            demand_type=fields.get("需求类型", "案例汇总"),
            output_format="标准化报告",
            priorities=priorities if priorities else ["标杆案例", "商业价值数据"],
            keyword_combo=keywords,
            raw_input=original,
        )
        
        # **规则引擎补充其他维度**
        user_input_lower = original.lower()
        
        # 识别技术领域
        for domain, kw_list in TECH_DOMAIN_KEYWORDS.items():
            if any(kw in user_input_lower for kw in kw_list):
                req.tech_domain = domain
                break
        
        # 识别公司范围
        for scope, kw_list in COMPANY_SCOPE_MAP.items():
            if any(kw in user_input_lower for kw in kw_list):
                req.company_scope = scope
                break
        
        # 识别地域
        for region, kw_list in REGION_MAP.items():
            if any(kw in user_input_lower for kw in kw_list):
                req.region = region
                break
        
        return req

    def parse(self, user_input: str) -> ParsedRequirement:
        print(f"\n  🔍 解析：{user_input[:80]}")
        stripped = user_input.strip()
        for prefix in ["AI+", "ai+", "AI +", "ai +"]:
            stripped = stripped.replace(prefix, "")
        if len(stripped.strip()) < 6:
            return self._ambiguous(user_input)

        raw = self._call_with_retry(user_input) if self.chain else None
        if raw is None:
            return self._fallback(user_input)

        parsed = self._extract_json(raw, user_input)
        parsed.llm_backend_used = self.backend_name
        parsed.keyword_combo = self._enrich_keywords(parsed)
        return parsed

    def _call_with_retry(self, user_input: str, max_retries: int = 2) -> Optional[str]:
        for attempt in range(max_retries + 1):
            try:
                result = self.chain.invoke({"user_input": user_input})
                print(f"  📋 LLM原始输出:\n{result[:300]}...")
                return result
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    m = re.search(r"retry[^\d]*(\d+)", err, re.IGNORECASE)
                    wait = min(int(m.group(1)) + 2, 60) if m else 30
                    if attempt < max_retries:
                        print(f"  ⏳ 配额超限，{wait}s后重试 ({attempt+1}/{max_retries})...")
                        time.sleep(wait)
                        continue
                    return None
                elif "connection" in err.lower() or "refused" in err.lower():
                    print("  ❌ 连接断开，请运行：ollama serve")
                    return None
                else:
                    print(f"  ❌ 调用失败：{err[:150]}")
                    return None
        return None

    def _ambiguous(self, user_input: str) -> ParsedRequirement:
        return ParsedRequirement(
            industry="未明确", demand_type="未明确",
            output_format="标准化报告",
            priorities=["标杆案例", "商业价值数据"],
            keyword_combo=[], is_ambiguous=True,
            clarification_prompt="请明确需求细节：\n1. 需求类型\n2. 核心侧重点\n3. 目标行业/细分领域",
            raw_input=user_input, llm_backend_used="rules",
        )

    def _fallback(self, user_input: str) -> ParsedRequirement:
        """规则回退策略"""
        # 识别主行业
        industry = next((k for k in KEYWORD_MATRIX if k in user_input), "工业")
        matrix = KEYWORD_MATRIX.get(industry, {})
        
        # 识别细分行业
        sub_industry = ""
        if matrix:
            for sub in matrix["sub_industries"]:
                if sub in user_input:
                    sub_industry = sub
                    break
        
        # 识别技术领域
        tech_domain = ""
        for domain, keywords in TECH_DOMAIN_KEYWORDS.items():
            if any(kw in user_input for kw in keywords):
                tech_domain = domain
                break
        
        # 识别公司范围
        company_scope = ""
        for scope, keywords in COMPANY_SCOPE_MAP.items():
            if any(kw in user_input for kw in keywords):
                company_scope = scope
                break
        
        # 识别地域
        region = ""
        for reg, keywords in REGION_MAP.items():
            if any(kw in user_input for kw in keywords):
                region = reg
                break
        
        # 构建关键词
        kws = [industry]
        if sub_industry:
            kws.append(sub_industry)
        if tech_domain:
            kws.append(tech_domain)
        if company_scope:
            kws.append(company_scope)
        if region:
            kws.append(region)
        kws.extend(matrix.get("commercial", [])[:2])
        kws.extend(matrix.get("priority", [])[:1])
        
        # 判断需求类型
        demand = ("切入点分析" if any(w in user_input for w in ["切入点", "机会"])
                  else "竞品对比" if any(w in user_input for w in ["竞品", "对比", "vs"])
                  else "落地方向" if any(w in user_input for w in ["落地", "方向"])
                  else "案例汇总")
        
        return ParsedRequirement(
            industry=industry,
            sub_industry=sub_industry,
            demand_type=demand,
            output_format="标准化报告",
            tech_domain=tech_domain,
            company_scope=company_scope,
            region=region,
            priorities=["标杆案例", "商业价值数据"],
            keyword_combo=kws[:10],
            raw_input=user_input,
            llm_backend_used="rules_fallback",
        )

if __name__ == "__main__":
    print("=" * 80)
    print("D1 需求解析（增强版） | 规则引擎测试")
    print("=" * 80)
    parser = RequirementParser()
    
    # 禁用 LLM，只测试规则引擎
    parser.chain = None
    
    tests = [
        "AI+化工的落地方向案例，产出报告，优先找有明确节能效果的标杆案例",
        "AI+虚拟电厂标杆案例及切入点分析，关注国内头部企业",
        "AI+石油化工催化剂优化，国外头部企业案例，华东地区",
        "AI+钢铁高炉优化，算法方向，央企国企案例",
        "AI+化工案例",  # 模糊测试
    ]
    
    for t in tests:
        print("\n" + "─" * 80)
        r = parser.parse(t)
        if r.is_ambiguous:
            print(f"⚠️  模糊需求：\n{r.clarification_prompt}")
        else:
            print(f"✅ {r.summary()}")
            print(f"   搜索查询: {r.to_search_query()}")
