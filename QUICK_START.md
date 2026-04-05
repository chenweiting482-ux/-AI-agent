# 🚀 快速上云指南

## ✅ 已完成准备工作

我已经为你准备好了所有部署所需的文件，并已推送到 GitHub：

```
✅ README.md - 项目说明文档
✅ DEPLOYMENT.md - 详细部署指南
✅ app.py - FastAPI 应用接口
✅ web_ui.py - Gradio Web 界面
✅ requirements.txt - Python 依赖列表
✅ deploy.sh - 一键部署脚本
✅ supervisor.conf - 进程管理配置
✅ nginx.conf - Nginx 反向代理配置
```

---

## 📝 接下来你需要做的事情

### 第一步：SSH 连接到阿里云服务器

在你的本地电脑上打开 PowerShell（Windows）或终端（macOS/Linux）：

```bash
# 使用密码登录
ssh root@你的服务器IP

# 或使用密钥登录
ssh -i /path/to/your/key.pem root@你的服务器IP
```

> 💡 **提示**：服务器 IP 可以在阿里云 ECS 控制台查看

---

### 第二步：一键部署（推荐）

连接服务器后，执行以下命令：

```bash
# 1. 下载一键部署脚本
curl -O https://raw.githubusercontent.com/chenweiting482-ux/-AI-agent/main/deploy.sh

# 2. 添加执行权限
chmod +x deploy.sh

# 3. 运行部署脚本
./deploy.sh
```

部署脚本会自动完成：
- ✅ 系统更新
- ✅ Python 3.10+ 安装
- ✅ Git 安装
- ✅ 项目代码克隆
- ✅ 虚拟环境创建
- ✅ 依赖包安装

---

### 第三步：配置 API Key

部署完成后，编辑 `.env` 文件：

```bash
nano .env
```

添加以下内容（替换为你的真实 API Key）：

```
DASHSCOPE_API_KEY=sk-你的阿里云DashScope密钥
TAVILY_API_KEY=你的Tavily密钥（可选）
```

保存退出：`Ctrl + X` → `Y` → `Enter`

> 📌 **获取 API Key**：
> - DashScope: https://dashscope.console.aliyun.com/
> - Tavily（可选）: https://tavily.com/

---

### 第四步：启动服务

#### 方式 1：简单启动（测试用）

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Web 界面（前台运行）
python web_ui.py
```

然后在浏览器访问：`http://你的服务器IP:7860`

按 `Ctrl + C` 可停止服务

---

#### 方式 2：后台运行（生产推荐）

```bash
# 启动 API 服务（后台）
nohup python app.py > api.log 2>&1 &

# 启动 Web 界面（后台）
nohup python web_ui.py > web.log 2>&1 &

# 查看日志
tail -f api.log
tail -f web.log
```

访问：
- **Web 界面**: `http://你的服务器IP:7860`
- **API 文档**: `http://你的服务器IP:8000/docs`

---

### 第五步：配置 Nginx（可选，生产环境推荐）

如果你想通过域名访问并配置 HTTPS：

```bash
# 1. 安装 Nginx
sudo apt install nginx -y

# 2. 下载配置文件
curl -O https://raw.githubusercontent.com/chenweiting482-ux/-AI-agent/main/nginx.conf

# 3. 编辑配置（修改域名/IP）
nano nginx.conf

# 4. 启用配置
sudo cp nginx.conf /etc/nginx/sites-available/industrial-ai-agent
sudo ln -s /etc/nginx/sites-available/industrial-ai-agent /etc/nginx/sites-enabled/

# 5. 测试并重启
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 常用运维命令

### 查看服务状态

```bash
# 查看进程
ps aux | grep python

# 查看端口
netstat -tunlp | grep python

# 查看日志
tail -f api.log
tail -f web.log
```

### 停止服务

```bash
# 停止所有 Python 进程
pkill -f "python (app|web_ui).py"

# 或根据 PID 停止
kill <PID>
```

### 更新代码

```bash
cd ~/工业AI调研agent
source venv/bin/activate
git pull origin main
pip install -r requirements.txt

# 重启服务
pkill -f "python (app|web_ui).py"
nohup python app.py > api.log 2>&1 &
nohup python web_ui.py > web.log 2>&1 &
```

---

## ️ 阿里云安全组配置

**重要**：记得在阿里云控制台开放端口！

1. 登录 [阿里云 ECS 控制台](https://ecs.console.aliyun.com/)
2. 找到你的实例 → 安全组 → 配置规则
3. 添加入方向规则：

| 端口范围 | 协议 | 授权对象 | 说明 |
|---------|------|---------|------|
| 22 | TCP | 0.0.0.0/0 | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 7860 | TCP | 0.0.0.0/0 | Gradio Web |
| 8000 | TCP | 0.0.0.0/0 | FastAPI |

---

## 📊 服务访问

部署完成后，你可以通过以下方式访问：

### 1. Web 界面（推荐）
```
http://你的服务器IP:7860
```
- ✅ 友好的图形界面
- ✅ 支持交互式输入
- ✅ 内置示例需求
- ✅ 可直接复制报告内容

### 2. API 接口
```
http://你的服务器IP:8000/docs
```
- ✅ Swagger API 文档
- ✅ 在线测试接口
- ✅ 支持程序化调用

### 3. 命令行
```bash
cd ~/工业AI调研agent
source venv/bin/activate
python main_entra.py "AI+化工落地方向案例"
```

---

## 🆘 常见问题

### Q1: 部署脚本执行失败？

**A**: 检查网络连接和权限：
```bash
# 确保是 root 用户
whoami

# 测试网络
ping -c 3 github.com

# 手动执行各步骤（参考 DEPLOYMENT.md）
```

### Q2: 服务启动后无法访问？

**A**: 检查防火墙和安全组：
```bash
# 查看防火墙状态
sudo ufw status

# 开放端口
sudo ufw allow 7860/tcp
sudo ufw allow 8000/tcp
```

### Q3: API Key 配置错误？

**A**: 验证配置：
```bash
cat .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key exists:', bool(os.getenv('DASHSCOPE_API_KEY')))"
```

### Q4: 内存不足？

**A**: 添加 Swap 空间：
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📚 更多资源

- 📖 **详细部署指南**: [DEPLOYMENT.md](DEPLOYMENT.md)
- 📖 **项目文档**: [README.md](README.md)
- 🔗 **GitHub 仓库**: https://github.com/chenweiting482-ux/-AI-agent

---

## 🎉 完成！

按照以上步骤，你的工业 AI 调研 Agent 就已经成功部署到阿里云服务器了！

**下一步建议**：
1. 测试 Web 界面是否正常工作
2. 运行一个完整的调研流程
3. 配置域名和 HTTPS（可选）
4. 设置自动备份（参考 DEPLOYMENT.md）

**祝你使用愉快！** 🚀