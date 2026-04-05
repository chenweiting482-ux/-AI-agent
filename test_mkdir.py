"""测试目录创建逻辑"""
from pathlib import Path

test_industries = ['石油/化工', '电力\\能源', '制造业']
output_dir = Path('./output_reports')
output_dir.mkdir(exist_ok=True)

for ind in test_industries:
    safe_industry = ind.replace("/", "_").replace("\\", "_").replace(":", "_").strip()
    industry_dir = output_dir / safe_industry
    industry_dir.mkdir(exist_ok=True)
    print(f"✅ {ind} -> {industry_dir}")

print("\n所有测试通过！")