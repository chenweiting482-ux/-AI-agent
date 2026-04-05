#!/bin/bash
# 工业 AI 调研 Agent 一键部署脚本
# 适用于 Ubuntu 20.04+ / CentOS 7+

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🏭 工业 AI 调研 Agent - 一键部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
else
    echo -e "${RED}❌ 无法检测操作系统${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 检测到操作系统: $OS${NC}"
echo ""

# 步骤 1: 更新系统
echo -e "${YELLOW}[1/7] 更新系统...${NC}"
if command -v apt &> /dev/null; then
    sudo apt update && sudo apt upgrade -y
elif command -v yum &> /dev/null; then
    sudo yum update -y
else
    echo -e "${RED}❌ 不支持的包管理器${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 系统更新完成${NC}"
echo ""

# 步骤 2: 安装 Python 3.10+
echo -e "${YELLOW}[2/7] 检查 Python 版本...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓ 已安装 Python $PYTHON_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  未检测到 Python3，开始安装...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3.10 python3.10-devel python3-pip
    fi
fi
echo ""

# 步骤 3: 安装 Git
echo -e "${YELLOW}[3/7] 检查 Git...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  未检测到 Git，开始安装...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt install -y git
    elif command -v yum &> /dev/null; then
        sudo yum install -y git
    fi
fi
echo -e "${GREEN}✓ Git 已就绪${NC}"
echo ""

# 步骤 4: 克隆项目
echo -e "${YELLOW}[4/7] 克隆项目代码...${NC}"
if [ ! -d "工业AI调研agent" ]; then
    git clone https://github.com/chenweiting482-ux/-AI-agent.git
    cd 工业AI调研agent
else
    cd 工业AI调研agent
    echo -e "${YELLOW}⚠️  项目目录已存在，跳过克隆${NC}"
fi
echo -e "${GREEN}✓ 代码已就绪${NC}"
echo ""

# 步骤 5: 创建虚拟环境
echo -e "${YELLOW}[5/7] 创建 Python 虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
echo ""

# 步骤 6: 安装依赖
echo -e "${YELLOW}[6/7] 安装 Python 依赖包...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 步骤 7: 配置环境变量
echo -e "${YELLOW}[7/7] 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未检测到 .env 文件，请手动创建${NC}"
    echo ""
    echo "请编辑 .env 文件，添加以下内容："
    echo "  DASHSCOPE_API_KEY=your_dashscope_api_key_here"
    echo "  TAVILY_API_KEY=your_tavily_api_key_here"
    echo ""
    read -p "按 Enter 键继续..."
fi
echo -e "${GREEN}✓ 环境变量配置完成${NC}"
echo ""

# 部署完成
echo "=========================================="
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo ""
echo "1️⃣  编辑 .env 文件，配置 API Key："
echo "   nano .env"
echo ""
echo "2️⃣  启动 FastAPI 服务（后台运行）："
echo "   nohup python app.py > api.log 2>&1 &"
echo ""
echo "3️⃣  或启动 Gradio Web 界面："
echo "   nohup python web_ui.py > web.log 2>&1 &"
echo ""
echo "4️⃣  查看服务日志："
echo "   tail -f api.log"
echo "   tail -f web.log"
echo ""
echo "5️⃣  访问服务："
echo "   API 文档: http://$(curl -s ifconfig.me):8000/docs"
echo "   Web 界面: http://$(curl -s ifconfig.me):7860"
echo ""
echo "📚 详细文档请参考: DEPLOYMENT.md"
echo ""
echo "=========================================="