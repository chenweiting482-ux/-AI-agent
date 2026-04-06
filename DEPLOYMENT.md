# 🚀 阿里云服务器部署指南

## 📋 前置准备

### 1. 服务器信息确认

- [ ] **公网 IP**：`your_server_ip`
- [ ] **SSH 端口**：`22`（默认）
- [ ] **登录方式**：SSH 密钥 / 密码
- [ ] **操作系统**：Ubuntu 20.04+ / CentOS 7+（推荐 Ubuntu）

### 2. 安全组配置（阿里云控制台）

在阿里云 ECS 控制台配置安全组规则：

| 端口 | 协议 | 用途 | 来源 |
|------|------|------|------|
| 22 | TCP | SSH 远程登录 | 0.0.0.0/0（或指定 IP） |
| 80 | TCP | HTTP 访问 | 0.0.0.0/0 |
| 443 | TCP | HTTPS 访问 | 0.0.0.0/0 |
| 8000 | TCP | FastAPI/Gradio 应用 | 0.0.0.0/0 |

---

## 🔧 步骤 1：连接到服务器

### Windows (PowerShell)

```powershell
ssh root@your_server_ip
```

### macOS/Linux

```bash
ssh -i /path/to/your/key.pem root@your_server_ip
```

---

## 📦 步骤 2：服务器环境配置

### 2.1 更新系统

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2.2 安装 Python 3.10+

```bash
# Ubuntu
sudo apt install python3.10 python3.10-venv python3.10-dev -y
sudo apt install python3-pip -y

# CentOS
sudo yum install python3.10 python3.10-devel -y
sudo yum install python3-pip -y

# 验证安装
python3 --version
pip3 --version
```

### 2.3 安装 Git

```bash
# Ubuntu
sudo apt install git -y

# CentOS
sudo yum install git -y

git --version
```

### 2.4 安装 Ollama（可选，用于本地 LLM）

```bash
# 下载并安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve &

# 拉取模型
ollama pull qwen2.5:1.5b

# 验证
ollama list
```

---

## 🚀 步骤 3：部署项目

### 3.1 克隆项目

```bash
cd ~
git clone https://github.com/chenweiting482-ux/-AI-agent.git
cd 工业AI调研agent
```

### 3.2 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

如果没有 `requirements.txt`，手动安装：

```bash
pip install langchain langchain-openai langchain-community langchain-text-splitters
pip install chromadb crewai python-dotenv
pip install fastapi uvicorn gradio  # Web 界面依赖
```

### 3.4 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
DASHSCOPE_API_KEY=your_dashscope_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
EOF

# 验证配置
cat .env
```

### 3.5 测试运行

```bash
# 运行测试（使用默认参数）
python main_entra.py "AI+化工落地方向案例"
```

---

## 🌐 步骤 4：部署 Web 界面（推荐）

### 4.1 创建 API 服务

创建 `app.py`：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main_entra import run_agent
import uvicorn

app = FastAPI(
    title="工业 AI 调研 Agent API",
    description="工业 AI 案例调研系统",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str
    skip_clarification: bool = False

@app.post("/api/research")
async def research(request: QueryRequest):
    try:
        report = run_agent(request.query, request.skip_clarification)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

### 4.2 创建 Gradio 界面（可选）

创建 `web_ui.py`：

```python
import gradio as gr
from main_entra import run_agent

def research_interface(query):
    if not query.strip():
        return "请输入调研需求"
    try:
        report = run_agent(query, skip_clarification=True)
        return report
    except Exception as e:
        return f"错误：{str(e)}"

demo = gr.Interface(
    fn=research_interface,
    inputs=gr.Textbox(
        lines=3,
        placeholder="请输入调研需求，例如：AI+化工落地方向案例，产出报告",
        label="调研需求"
    ),
    outputs=gr.Markdown(label="调研报告"),
    title="🏭 工业 AI 调研 Agent",
    description="基于 LangChain + CrewAI 的智能工业 AI 案例调研系统",
    examples=[
        ["AI+化工的落地方向案例，产出报告，优先找有明确节能效果的标杆案例"],
        ["AI+虚拟电厂标杆案例及切入点分析，关注国内头部企业"],
        ["AI+钢铁高炉优化，算法方向，央企国企案例"],
    ]
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

### 4.3 启动服务

```bash
# 启动 FastAPI（后台运行）
nohup python app.py > api.log 2>&1 &

# 或启动 Gradio（后台运行）
nohup python web_ui.py > web.log 2>&1 &

# 查看日志
tail -f api.log
# 或
tail -f web.log
```

访问：
- **API 文档**：`http://your_server_ip:8000/docs`
- **Gradio 界面**：`http://your_server_ip:7860`

---

## 🔒 步骤 5：配置 Nginx（生产环境推荐）

### 5.1 安装 Nginx

```bash
# Ubuntu
sudo apt install nginx -y

# CentOS
sudo yum install nginx -y
```

### 5.2 配置反向代理

创建配置文件 `/etc/nginx/sites-available/industrial-ai-agent`：

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # 日志
    access_log /var/log/nginx/industrial-ai-agent-access.log;
    error_log /var/log/nginx/industrial-ai-agent-error.log;

    # API 服务
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gradio 界面
    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/industrial-ai-agent /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

### 5.3 配置 SSL（HTTPS）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 自动配置 SSL
sudo certbot --nginx -d your_domain.com
```

---

## 🔄 步骤 6：配置进程管理（PM2 / Supervisor）

### 6.1 使用 Supervisor（推荐）

```bash
# 安装 Supervisor
sudo apt install supervisor -y

# 创建配置文件
sudo tee /etc/supervisor/conf.d/industrial-ai-agent.conf << 'EOF'
[program:industrial-ai-api]
command=/root/工业AI调研agent/venv/bin/python /root/工业AI调研agent/app.py
directory=/root/工业AI调研agent
autostart=true
autorestart=true
stderr_logfile=/var/log/industrial-ai-api.err.log
stdout_logfile=/var/log/industrial-ai-api.out.log
user=root
environment=PATH="/root/工业AI调研agent/venv/bin"

[program:industrial-ai-web]
command=/root/工业AI调研agent/venv/bin/python /root/工业AI调研agent/web_ui.py
directory=/root/工业AI调研agent
autostart=true
autorestart=true
stderr_logfile=/var/log/industrial-ai-web.err.log
stdout_logfile=/var/log/industrial-ai-web.out.log
user=root
environment=PATH="/root/工业AI调研agent/venv/bin"
EOF

# 重启 Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# 查看状态
sudo supervisorctl status
```

---

## 📊 步骤 7：监控与维护

### 7.1 查看服务状态

```bash
# 查看进程
ps aux | grep python

# 查看端口占用
netstat -tunlp | grep python

# 查看日志
tail -f /var/log/industrial-ai-api.out.log
```

### 7.2 自动备份

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
PROJECT_DIR="/root/工业AI调研agent"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/industrial-ai-agent_$DATE.tar.gz $PROJECT_DIR

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加（每天凌晨 2 点备份）
0 2 * * * /root/工业AI调研agent/backup.sh
```

### 7.3 更新项目

```bash
cd /root/工业AI调研agent
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart all
```

---

## 🛡️ 安全加固建议

1. **修改 SSH 端口**：
   ```bash
   sudo nano /etc/ssh/sshd_config
   # 修改 Port 22 为 Port 2222
   sudo systemctl restart sshd
   ```

2. **配置防火墙**：
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 8000/tcp
   sudo ufw allow 7860/tcp
   ```

3. **定期更新系统**：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **禁用 root 登录**（使用普通用户 + sudo）

---

## 📞 故障排查

### 问题 1：服务无法启动

```bash
# 查看详细日志
journalctl -u supervisor -f
tail -f /var/log/industrial-ai-api.err.log
```

### 问题 2：端口被占用

```bash
# 查找占用端口的进程
sudo lsof -i :8000
sudo kill -9 <PID>
```

### 问题 3：API Key 配置错误

```bash
# 检查 .env 文件
cat .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('DASHSCOPE_API_KEY'))"
```

### 问题 4：内存不足

```bash
# 查看内存使用
free -h
htop

# 增加 Swap 空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🎉 完成！

部署完成后，你应该可以：

1. ✅ 通过 SSH 管理服务器
2. ✅ 访问 API 文档：`http://your_server_ip:8000/docs`
3. ✅ 使用 Web 界面：`http://your_server_ip:7860`
4. ✅ 查看服务日志和监控状态
5. ✅ 配置自动备份和更新

---

## 📚 附加资源

- [阿里云 ECS 文档](https://help.aliyun.com/product/25365.html)
- [FastAPI 部署文档](https://fastapi.tiangolo.com/deployment/)
- [Nginx 配置指南](https://nginx.org/en/docs/)
- [Supervisor 文档](http://supervisord.org/)

---

**🙋 如有问题，请查看日志文件或提交 Issue！**
