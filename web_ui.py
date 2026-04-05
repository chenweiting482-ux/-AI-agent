"""
Gradio Web 界面
提供友好的 Web UI，支持交互式调研需求输入和报告展示
"""

import gradio as gr
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from main_entra import run_agent


def research_interface(query, skip_clarification=False):
    """
    调研接口函数
    
    Args:
        query: 用户输入的调研需求
        skip_clarification: 是否跳过澄清步骤
        
    Returns:
        str: 调研报告内容
    """
    if not query or not query.strip():
        return "⚠️ 请输入调研需求"
    
    try:
        print(f"\n🔍 开始处理需求: {query}")
        report = run_agent(query, skip_clarification=skip_clarification)
        print("✅ 报告生成完成")
        return report
    except Exception as e:
        error_msg = f"❌ 发生错误：\n```\n{str(e)}\n```\n\n请检查：\n1. 环境变量配置（.env 文件）\n2. API Key 是否有效\n3. 网络连接是否正常"
        print(f"❌ 错误: {e}")
        return error_msg


def create_demo():
    """创建 Gradio 演示界面"""
    
    # 创建示例列表
    examples = [
        ["AI+化工的落地方向案例，产出报告，优先找有明确节能效果的标杆案例"],
        ["AI+虚拟电厂标杆案例及切入点分析，关注国内头部企业"],
        ["AI+石油化工催化剂优化，国外头部企业案例，华东地区"],
        ["AI+钢铁高炉优化，算法方向，央企国企案例"],
    ]
    
    # 创建界面
    with gr.Blocks(
        title="🏭 工业 AI 调研 Agent",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="green"
        )
    ) as demo:
        
        gr.Markdown(
            """
            # 🏭 工业 AI 调研 Agent
            
            > **基于 LangChain + CrewAI 的智能工业 AI 案例调研系统**
            
            ## 功能特点
            - ✅ 智能需求解析（支持多行业、多维度）
            - 🔍 精准案例检索（三重过滤机制）
            - 📚 RAG 知识库（元数据提取 + 混合检索）
            - 🤖 多智能体协作分析（4 角色流水线）
            - 📊 PM 视角标准化报告输出
            
            ## 使用指南
            1. 在下方输入框中填写调研需求
            2. 点击"开始调研"按钮
            3. 等待系统生成报告（通常需要 2-5 分钟）
            4. 查看并下载调研报告
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    lines=4,
                    placeholder="请输入调研需求，例如：\nAI+化工落地方向案例，产出报告，优先找有明确节能效果的标杆案例",
                    label="📝 调研需求",
                    info="支持多行业、多维度需求描述"
                )
                
                skip_clarification = gr.Checkbox(
                    label="️ 跳过澄清步骤（自动化模式）",
                    value=False,
                    info="勾选后将跳过需求确认环节，直接使用默认参数"
                )
                
                submit_btn = gr.Button(
                    "🚀 开始调研",
                    variant="primary",
                    size="lg"
                )
                
                clear_btn = gr.Button(
                    "🗑️ 清空",
                    variant="secondary"
                )
            
            with gr.Column(scale=3):
                output_report = gr.Markdown(
                    label="📄 调研报告",
                    show_copy_button=True
                )
        
        # 添加示例
        gr.Examples(
            examples=examples,
            inputs=query_input,
            label="💡 示例需求"
        )
        
        # 添加说明
        gr.Markdown(
            """
            ## 📖 需求描述建议
            
            **好的需求描述应包含**：
            1. **目标行业**：如"化工"、"虚拟电厂"、"钢铁"
            2. **需求类型**：如"落地方向"、"案例汇总"、"切入点分析"
            3. **优先级**：如"标杆案例"、"节能效果"、"ROI 数据"
            4. **其他维度**（可选）：如"国内/国外"、"头部企业"、"华东地区"
            
            **示例**：
            - ✅ "AI+化工落地方向案例，产出报告，优先找有明确节能效果的标杆案例"
            - ✅ "AI+虚拟电厂标杆案例及切入点分析，关注国内头部企业"
            - ❌ "AI 案例"（过于模糊）
            
            ## ⚙️ 技术架构
            - **D1** 需求解析：LLM + 规则引擎混合解析
            - **D2** 精准检索：Tavily API + 三重过滤（时效性/商业价值/相关性）
            - **D3** RAG 知识库：9 字段元数据提取 + ChromaDB 混合检索
            - **D4** CrewAI 分析：4 角色协作（解决方案/行业/商业/切入点）
            - **D5** 质量审核：100 分制规则评分（合格线 75 分）
            """
        )
        
        # 绑定事件
        submit_btn.click(
            fn=research_interface,
            inputs=[query_input, skip_clarification],
            outputs=output_report
        )
        
        clear_btn.click(
            fn=lambda: ("", gr.update(value=False)),
            inputs=None,
            outputs=[query_input, skip_clarification]
        )
    
    return demo


if __name__ == "__main__":
    # 创建演示
    demo = create_demo()
    
    # 启动服务
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # 设置为 True 可生成临时公网链接
        inbrowser=False,
        quiet=False
    )