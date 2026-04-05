# 📋 工业 AI 调研 Agent 云部署完整记录

## 🎯 项目概述

**项目名称**: 工业 AI 调研 Agent  
**技术架构**: 基于 LangChain 的多智能体系统，包含 D1→D2→D3→D4→D5 五阶段工作流  
**部署方式**: 阿里云 ECS 服务器 + Gradio Web 界面 + FastAPI  
**创建时间**: 2026-04-05  
**最后更新**: 2026-04-05

---

##  服务器信息

| 项目 | 值 |
|------|-----|
| **服务器 IP** | 172.19.43.169（内网）|
| **SSH 端口** | 22 |
| **操作系统** | Ubuntu |
| **Python 版本** | 3.12 |
| **项目路径** | `/root/-AI-agent` |
| **Web 服务端口** | 7860 |
| **API 服务端口** | 8000 |

---

## 🐍 环境配置

### 虚拟环境信息

- **位置**: `/root/-AI-agent/venv`
- **Python 版本**: 3.12
- **pip 版本**: 26.0.1
- **激活命令**: `source venv/bin/activate`

### 核心依赖库

```bash
langchain==1.2.15
langchain-classic==1.0.3
langchain-community==0.4.1
langchain-core==1.2.26
langchain-openai==1.1.12
langchain-text-splitters==1.1.1
langchain-ollama
```

### API Key 配置

- **DASHSCOPE_API_KEY**: `sk-10a0d08a2ece457899aa5574b4f38bea`
- **配置文件**: `/root/-AI-agent/.env`
- **格式**: UTF-8 编码，`KEY=VALUE` 格式
- **注意**: `.env` 文件不提交到 Git，需要手动配置

---

## 📁 项目文件结构

```
/root/-AI-agent/
├── main_entra.py                # 主入口
├── d1_requirement_parser.py     # D1: 需求解析
├── d2_search_tool.py            # D2: 搜索工具
├── d3_rag_library.py            # D3: RAG 库
├── d4_d5_analysis_review.py     # D4/D5: 分析审核
├── llm_config.py                # LLM 配置
├── web_ui.py                    # Gradio Web 界面
├── app.py                       # FastAPI 接口
├── requirements.txt             # 依赖列表
├── .env                         # API Key 配置（不提交到 Git）
├── venv/                        # Python 虚拟环境
├── README.md                    # 项目说明
├── DEPLOYMENT.md                # 部署指南
├── QUICK_START.md               # 快速上手
├── deploy.sh                    # 一键部署脚本
├── supervisor.conf              # Supervisor 配置
└── nginx.conf                   # Nginx 配置
```

---

## ‍💻 Git 版本控制

### 仓库信息

- **仓库地址**: https://github.com/chenweiting482-ux/-AI-agent
- **默认分支**: `main`
- **用户名**: chenweiting482-ux
- **邮箱**: chenweiting482@gmail.com

### Git 配置命令

```bash
git config user.name "chenweiting482-ux"
git config user.email "chenweiting482@gmail.com"
```

### 常用 Git 命令

```bash
# 查看状态
git status

# 添加文件
git add .

# 提交更改
git commit -m "提交信息"

# 推送到远程
git push origin main

# 拉取最新代码
git pull origin main
```

---

## ✅ 已完成的操作

### 1. 本地开发（Windows）

- [x] 创建项目并编写代码
- [x] 初始化 Git 仓库
- [x] 配置 `.gitignore`（排除 venv/、__pycache__/、.env 等）
- [x] 创建所有核心模块
- [x] 创建 Web UI（Gradio）和 API（FastAPI）
- [x] 推送到 GitHub

### 2. 服务器端操作（阿里云）

- [x] SSH 连接到服务器
- [x] 克隆项目: `git clone https://github.com/chenweiting482-ux/-AI-agent.git`
- [x] 修复 dpkg 问题: `sudo dpkg --configure -a`
- [x] 安装 python3.12-venv: `apt install python3.12-venv -y`
- [x] 创建 Python 虚拟环境: `python3 -m venv venv`
- [x] 激活虚拟环境: `source venv/bin/activate`
- [x] 升级 pip: `pip install --upgrade pip`
- [x] 安装核心依赖: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- [x] 安装 langchain-ollama: `pip install langchain-ollama -i https://pypi.tuna.tsinghua.edu.cn/simple`
- [x] 配置 API Key: `nano .env` → 写入 `DASHSCOPE_API_KEY=sk-10a0d08a2ece457899aa5574b4f38bea`

### 3. 待完成的操作

- [ ] 启动 Web 服务并测试
- [ ] 配置阿里云安全组（开放 7860 端口）
- [ ] 在浏览器中访问 Web 界面
- [ ] 测试完整的 AI Agent 工作流

---

## 🌐 Web UI 访问

### 启动命令

```bash
# 确保在正确的目录
cd /root/-AI-agent

# 激活虚拟环境
source venv/bin/activate

# 启动 Web 服务（后台运行）
nohup python web_ui.py > web.log 2>&1 &

# 等待 15 秒
sleep 15

# 查看日志
tail -f web.log
```

### 访问地址

在你的**本地电脑浏览器**中访问：
```
http://172.19.43.169:7860
```

### 阿里云安全组配置

需要在阿里云控制台开放以下端口：

| 端口 | 协议 | 用途 |
|------|------|------|
| 22 | TCP | SSH 连接 |
| 7860 | TCP | Gradio Web 界面 |
| 8000 | TCP | FastAPI 接口 |

**配置路径**: 阿里云控制台 → ECS → 实例 → 安全组 → 配置规则 → 手动添加

---

## 🔧 常用管理命令

### 查看服务状态

```bash
# 查看 Python 进程
ps aux | grep python

# 查看端口占用
netstat -tunlp | grep 7860

# 查看 Web 服务日志
tail -f /root/-AI-agent/web.log
```

### 停止服务

```bash
# 停止 Web 服务
pkill -f "python web_ui.py"

# 或者手动杀进程
ps aux | grep web_ui.py
kill <PID>
```

### 重启服务

```bash
cd /root/-AI-agent
source venv/bin/activate
pkill -f "python web_ui.py"
sleep 2
nohup python web_ui.py > web.log 2>&1 &
sleep 15
tail -f web.log
```

### 更新代码

```bash
cd /root/-AI-agent
source venv/bin/activate
git pull origin main
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pkill -f "python web_ui.py"
nohup python web_ui.py > web.log 2>&1 &
```

---

## 🚨 故障排查

### 问题 1: ModuleNotFoundError

```bash
# 缺少某个模块时
pip install 模块名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2: pip install 很慢

```bash
# 使用国内镜像源
pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: 端口被占用

```bash
# 查看占用端口的进程
sudo lsof -i :7860

# 杀掉进程
sudo kill -9 <PID>
```

### 问题 4: dpkg 中断

```bash
sudo dpkg --configure -a
```

### 问题 5: 虚拟环境创建失败

```bash
# 安装 venv 包
apt install python3.12-venv -y

# 删除旧的 venv
rm -rf venv

# 重新创建
python3 -m venv venv
```

### 问题 6: 无法访问 Web 界面

1. 检查服务是否启动: `ps aux | grep web_ui`
2. 检查端口是否开放: `netstat -tunlp | grep 7860`
3. 检查阿里云安全组是否配置了 7860 端口
4. 查看日志: `tail -f web.log`

---

## 📚 参考文档

- **项目 README**: https://github.com/chenweiting482-ux/-AI-agent/blob/main/README.md
- **部署指南**: https://github.com/chenweiting482-ux/-AI-agent/blob/main/DEPLOYMENT.md
- **快速上手**: https://github.com/chenweiting482-ux/-AI-agent/blob/main/QUICK_START.md

---

## 🎯 下一步建议

### 测试 Web 界面

1. 访问 `http://172.19.43.169:7860`
2. 输入测试需求，如："AI+化工案例"
3. 观察 D1→D5 各阶段执行情况
4. 查看生成的调研报告

### 性能优化

1. **添加 Swap 空间**（如果内存不足）:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. **使用 Supervisor 管理进程**（实现自动重启）:
```bash
apt install supervisor -y
cp supervisor.conf /etc/supervisor/conf.d/web_ui.conf
supervisorctl reread
supervisorctl update
supervisorctl start web_ui
```

3. **配置 Nginx 反向代理**（生产环境推荐）:
```bash
apt install nginx -y
cp nginx.conf /etc/nginx/sites-available/web_ui
ln -s /etc/nginx/sites-available/web_ui /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 💡 重要提醒

1. **API Key 安全**: `.env` 文件包含敏感信息，不要分享或公开
2. **服务器备份**: 定期备份重要数据和配置文件
3. **监控日志**: 定期查看 `web.log` 和系统日志
4. **安全组配置**: 不要开放不必要的端口
5. **虚拟环境**: 始终在虚拟环境中运行 Python 代码
6. **代码更新**: 每次更新代码后，记得重启服务

---

## 📅 部署时间线

| 日期 | 操作 | 状态 |
|------|------|------|
| 2026-04-05 | 项目初始化和开发 | ✅ 完成 |
| 2026-04-05 | 推送到 GitHub | ✅ 完成 |
| 2026-04-05 | 克隆到阿里云服务器 | ✅ 完成 |
| 2026-04-05 | 安装 Python 环境和依赖 | ✅ 完成 |
| 2026-04-05 | 配置 API Key | ✅ 完成 |
| 2026-04-05 | 启动 Web 服务 | ⏳ 待完成 |
| 2026-04-05 | 测试完整功能 | ⏳ 待完成 |

---

**这份文档记录了从 0 到 1 的完整部署过程，以后每次部署或维护都可以参考！** 🎉

---

## 📞 联系方式

- **GitHub**: https://github.com/chenweiting482-ux
- **项目仓库**: https://github.com/chenweiting482-ux/-AI-agent
