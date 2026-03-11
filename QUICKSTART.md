# 快速入门指南

欢迎使用 PaperClaw - 人形机器人控制研究 Agent！本指南帮助你在 5 分钟内完成部署并开始使用。

---

## 📋 前置检查

- ✅ Python 3.8 或更高版本
- ✅ 安装了 OpenClaw 平台（`~/.npm-global/bin/openclaw`）
- ✅ Gmail 账号 + 应用专用密码（App Password）
- ✅ Obsidian vault 路径（用于日报/周报同步）

---

## 🚀 快速部署

### 步骤 1: 获取项目代码

```bash
git clone <repo_url>
cd PaperClaw
```

### 步骤 2: 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入以下内容：

```bash
# Gmail 邮件发送配置
EMAIL_SENDER=your_gmail@gmail.com
EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail 应用专用密码（16位）
EMAIL_RECIPIENT=user1@qq.com,user2@qq.com  # 支持逗号分隔多收件人

# Obsidian vault 路径
OBSIDIAN_VAULT=/home/yourname/Documents/Obsidian Vault

# 工作空间路径（可选，默认 ~/.paperclaw/workspace）
# PAPERCLAW_WORKSPACE=/path/to/workspace

# Semantic Scholar API Key（可选，提高速率限制）
# SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

**Gmail 应用专用密码获取方式**：
1. 访问 https://myaccount.google.com/security，开启两步验证
2. 搜索 "App passwords"，生成 16 位专用密码
3. 填入 `EMAIL_APP_PASSWORD`

### 步骤 3: 部署 Agent 到 OpenClaw

```bash
cd /data-ssd/zhang/paper_writing/PaperClaw

# 复制 Agent 配置
cp agent/AGENT.md ~/.openclaw/agents/surrogate-modeling-expert/
cp agent/models.json ~/.openclaw/agents/surrogate-modeling-expert/

# 复制技能模块
cp -r skills/* ~/.openclaw/agents/surrogate-modeling-expert/skills/
```

### 步骤 4: 配置 OpenClaw 定时任务

启动 Gateway 后添加两个定时任务：

```bash
# 启动 Gateway（建议在 tmux 中长期运行）
~/.npm-global/bin/openclaw gateway
```

#### 每日论文检索（每天 09:00 Asia/Shanghai）

```bash
~/.npm-global/bin/openclaw cron add << 'EOF'
{
  "agentId": "surrogate-modeling-expert",
  "name": "Daily Paper Search - Humanoid Whole-Body Control",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "执行每日论文检索任务：默认从 Semantic Scholar 检索人形机器人全身控制与感知控制领域的最新论文，并过滤 tro, icra, ral, iros, science_robotics, ijrr；必要时再切回 arXiv。然后对精选的 Top 3 论文执行完整的 paper-review 流程（阅读论文、撰写 summary.md、四维评分 scores.md、更新 evaluated_papers.json），最后运行以下命令发送深度评估邮件：\n\npython3 /data-ssd/zhang/paper_writing/PaperClaw/skills/daily-search/scripts/daily_paper_search.py --workspace ~/.paperclaw/workspace --send-evaluation",
    "timeoutSeconds": 1800
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "none" },
  "enabled": true
}
EOF
```

#### 每周报告生成（每周五 10:00 Asia/Shanghai）

```bash
~/.npm-global/bin/openclaw cron add << 'EOF'
{
  "agentId": "surrogate-modeling-expert",
  "name": "Weekly Report - Humanoid Whole-Body Control",
  "schedule": {
    "kind": "cron",
    "expr": "0 10 * * 5",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "生成人形机器人全身运动控制研究周报并发送邮件，运行以下命令：\n\npython3 /data-ssd/zhang/paper_writing/PaperClaw/skills/weekly-report/scripts/generate_weekly_report_v2.py\n\n该脚本会自动完成：读取本周评估论文、筛选 Top 3、生成 Markdown 周报、保存到本地和 Obsidian、发送邮件到收件人列表。",
    "timeoutSeconds": 1800
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "none" },
  "enabled": true
}
EOF
```

#### 验证定时任务

```bash
~/.npm-global/bin/openclaw cron list
```

### 步骤 5: 配置系统 crontab（邮件兜底）

系统 crontab 在 09:15 独立发送邮件，确保即使 Agent 未完成 paper-review，邮件也 100% 送达：

```bash
crontab -e
```

添加：

```
15 1 * * * /usr/bin/python3 /data-ssd/zhang/paper_writing/PaperClaw/skills/daily-search/scripts/daily_paper_search.py --workspace /home/shibo/.paperclaw/workspace --send-evaluation >> /tmp/paperclaw-email.log 2>&1
```

> 注意：系统 crontab 使用 UTC 时间，09:15 Asia/Shanghai = 01:15 UTC。

---

## 📖 每日流程说明

```
09:00  OpenClaw cron 触发 Agent
         ↓
       daily_paper_search.py          # 多来源检索（arXiv / Semantic Scholar）→ 筛选 Top 3 → 下载 PDF → 生成 Obsidian 日报
         ↓
       Agent paper-review × 3         # 阅读 PDF → summary.md + scores.md → 更新 evaluated_papers.json
         ↓
       daily_paper_search.py          # --send-evaluation：发送深度评估邮件 + 追加 Obsidian 日报
                                        --send-evaluation

09:15  系统 crontab 兜底（确保邮件 100% 发出，即使 Agent 未跑完）
         ↓
       daily_paper_search.py --send-evaluation
```

**每周五 10:00**：OpenClaw cron 触发 `generate_weekly_report_v2.py`，生成周报并发送邮件。

**邮件收件人**：在 `.env` 中配置 `EMAIL_RECIPIENT`（支持逗号分隔多个收件人）

**Obsidian 同步路径**：在 `.env` 中配置 `OBSIDIAN_VAULT`
- 日报：`daily/YYYY-MM-DD.md`
- 周报：`weekly/YYYY-MM-DD_weekly_report.md`

---

## 🖥️ 手动测试

### 打开 OpenClaw 对话界面

```bash
# 终端 1：启动 Gateway
~/.npm-global/bin/openclaw gateway

# 终端 2：打开 TUI（切换到 surrogate-modeling-expert）
~/.npm-global/bin/openclaw tui
```

### 手动触发每日全流程（在 TUI 中发送）

```
执行每日论文检索任务：检索人形机器人全身控制与感知控制领域的最新论文，然后对精选的 Top 3 论文执行完整的 paper-review 流程（阅读论文、撰写 summary.md、四维评分 scores.md、更新 evaluated_papers.json），最后运行以下命令发送深度评估邮件：

python3 /data-ssd/zhang/paper_writing/PaperClaw/skills/daily-search/scripts/daily_paper_search.py --workspace ~/.paperclaw/workspace --send-evaluation
```

### 手动测试多来源检索

```bash
# 默认 Semantic Scholar
python3 /data-ssd/zhang/paper_writing/PaperClaw/skills/daily-search/scripts/daily_paper_search.py \
  --workspace ~/.paperclaw/workspace \
  --top 3

# 显式切回 arXiv
python3 /data-ssd/zhang/paper_writing/PaperClaw/skills/daily-search/scripts/daily_paper_search.py \
  --workspace ~/.paperclaw/workspace \
  --source arxiv \
  --top 3
```

### 手动触发周报（在 TUI 中发送，或直接运行脚本）

```bash
python3 /data-ssd/zhang/paper_writing/PaperClaw/skills/weekly-report/scripts/generate_weekly_report_v2.py
```

### 立即触发 cron job（测试用）

```bash
# 查看 job ID
~/.npm-global/bin/openclaw cron list

# 立即运行
~/.npm-global/bin/openclaw cron run <job-id>
```

---

## 🔍 查看结果

```bash
# 查看今日待评估清单
cat ~/.paperclaw/workspace/pending_evaluation_$(date +%Y-%m-%d).json

# 查看论文目录
ls ~/.paperclaw/workspace/papers/

# 查看某篇论文总结
cat ~/.paperclaw/workspace/papers/<short_title>/summary.md

# 查看检索日志
cat ~/.paperclaw/workspace/search_logs/$(date +%Y-%m-%d)_search_log.json

# 查看最新周报
ls ~/.paperclaw/workspace/weekly_reports/

# 查看邮件发送日志（系统 crontab 兜底）
cat /tmp/paperclaw-email.log
```

---

## ⚙️ 管理定时任务

```bash
# 查看所有任务
~/.npm-global/bin/openclaw cron list

# 立即触发任务（测试用）
~/.npm-global/bin/openclaw cron run <job-id>

# 修改任务消息
~/.npm-global/bin/openclaw cron edit <job-id> --message "新消息内容"

# 禁用任务
~/.npm-global/bin/openclaw cron disable <job-id>

# 删除任务
~/.npm-global/bin/openclaw cron rm <job-id>
```

---

## 🔍 故障排查

### Gateway 未运行

```
Error: gateway closed (1006 abnormal closure)
```

**解决**：在 tmux 中启动并保持运行：

```bash
tmux new -s openclaw
~/.npm-global/bin/openclaw gateway
# Ctrl+B, D 退出 tmux 但保持后台运行
```

### 邮件发送失败

- 检查 `.env` 中 `EMAIL_APP_PASSWORD` 是否为 16 位应用专用密码（非 Gmail 登录密码）
- 确认 Gmail 已开启两步验证
- 手动测试连通性：

```bash
python3 -c "
import smtplib
with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as s:
    s.ehlo(); s.starttls(); print('SMTP OK')
"
```

### arXiv 搜索无结果

```bash
# 测试网络连通性
curl -s "http://export.arxiv.org/api/query?search_query=ti:humanoid&max_results=1" | head -20
```

### PATH 配置（避免每次写完整路径）

```bash
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

之后可直接使用 `openclaw` 命令。
