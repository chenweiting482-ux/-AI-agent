"""
FastAPI 应用接口
提供 RESTful API 服务，支持远程调用工业 AI 调研 Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from main_entra import run_agent

app = FastAPI(
    title="工业 AI 调研 Agent API",
    description="基于 LangChain + CrewAI 的智能工业 AI 案例调研系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    """调研请求"""
    query: str
    skip_clarification: bool = False


class ResearchResponse(BaseModel):
    """调研响应"""
    status: str
    report: Optional[str] = None
    error: Optional[str] = None


@app.get("/", tags=["Root"])
async def root():
    """API 根路径"""
    return {
        "name": "工业 AI 调研 Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "industrial-ai-agent"
    }


@app.post("/api/research", response_model=ResearchResponse, tags=["Research"])
async def research(request: ResearchRequest):
    """
    执行工业 AI 调研
    
    Args:
        request: 包含调研需求的请求对象
        
    Returns:
        ResearchResponse: 调研报告
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="查询需求不能为空")
    
    try:
        report = run_agent(request.query, request.skip_clarification)
        return ResearchResponse(
            status="success",
            report=report
        )
    except Exception as e:
        return ResearchResponse(
            status="error",
            error=str(e)
        )


@app.post("/api/quick-research", response_model=ResearchResponse, tags=["Research"])
async def quick_research(request: ResearchRequest):
    """
    快速调研（跳过澄清步骤）
    
    Args:
        request: 包含调研需求的请求对象
        
    Returns:
        ResearchResponse: 调研报告
    """
    return await research(ResearchRequest(
        query=request.query,
        skip_clarification=True
    ))


if __name__ == "__main__":
    import uvicorn
    
    # 阿里云函数计算 FC 默认端口为 9000
    port = int(os.environ.get("PORT", 9000))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境关闭热重载
        log_level="info"
    )
