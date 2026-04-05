"""
LLM配置统一管理模块
D1 使用本地 Ollama 千问模型
"""

import os
from typing import Optional
from langchain_ollama import ChatOllama


def get_llm(temperature: float = 0.7, num_predict: int = 1024):
    """
    获取LLM实例 - D1 专用
    使用本地部署的 Ollama 千问模型
    
    Args:
        temperature: 温度参数，控制输出随机性 (0.0-2.0)
        num_predict: 最大输出token数
        
    Returns:
        LangChain ChatOllama实例
    """
    try:
        return ChatOllama(
            model="qwen:7b",  # 本地部署的千问 7B 模型
            base_url="http://localhost:11434",  # Ollama 默认地址
            temperature=temperature,
            num_predict=num_predict,
            timeout=60,
        )
    except Exception as e:
        print(f"⚠️  Ollama 连接失败: {e}")
        print("   请确保运行了: ollama pull qwen:7b && ollama serve")
        return None

