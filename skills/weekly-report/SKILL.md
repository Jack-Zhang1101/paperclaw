# Weekly Report Generation Skill

## 功能描述
基于本周评估的论文，生成**人形机器人全身控制与感知控制**领域每周精选报告，通过邮件发送给指定用户，并同步到 Obsidian 知识库。

## 核心流程

### 步骤1: 读取已评估论文数据

从 `evaluated_papers.json` 读取本周评估的论文：

```bash
# 读取已评估论文列表
cat workspace/papers/evaluated_papers.json
```

### 步骤2: 筛选本周论文并排序

```python
import json
from datetime import datetime, timedelta

# 读取已评估论文
with open('workspace/papers/evaluated_papers.json', 'r') as f:
    data = json.load(f)

# 筛选本周论文（最近7天）
week_start = datetime.now() - timedelta(days=7)
week_papers = [
    paper for paper in data['papers']
    if datetime.fromisoformat(paper['evaluated_date']) >= week_start
]

# 按综合评分排序（降序）
week_papers.sort(key=lambda x: x['final_score'], reverse=True)

# 取 Top 3 精选论文
top_papers = week_papers[:3]
```

### 步骤3: 生成 Markdown 周报

基于四维评分系统生成周报：

```markdown
# 🤖 人形机器人全身控制与感知控制研究周报

**报告周期**: YYYY-MM-DD - YYYY-MM-DD
**生成时间**: YYYY-MM-DD HH:MM:SS

## 本周概览
- 评估论文总数: N
- 精选推荐论文: Top 3

## 本周精选论文 Top 3
...

## 四维评分分布（Top 5）
| 论文 | 控制性能 | 架构创新 | 理论贡献 | 可靠性 | 影响力 | 综合评分 |
```

### 步骤4: 保存与发送

1. 保存至本地 `weekly_reports/YYYY-MM-DD_weekly_report.md`
2. 同步到 Obsidian `$OBSIDIAN_VAULT/PaperClaw/weekly/`
3. 通过 Gmail SMTP 发送到配置的收件人邮箱

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart('alternative')
msg['Subject'] = f"🤖 人形机器人控制研究周报 - {report_date}"
msg['From'] = os.environ['EMAIL_SENDER']
msg['To'] = os.environ['EMAIL_RECIPIENT']
msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(os.environ['EMAIL_SENDER'], os.environ['EMAIL_APP_PASSWORD'])
    server.sendmail(msg['From'], msg['To'], msg.as_string())
```

**Gmail App Password 获取方式**：
1. 访问 https://myaccount.google.com/security，开启两步验证
2. 搜索 "App passwords"，生成 16 位专用密码
3. 设置环境变量：`EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx`

## 完整自动化脚本

脚本位置: `skills/weekly-report/scripts/generate_weekly_report_v2.py`

### 主要功能

1. **加载论文数据**: 从 `evaluated_papers.json` 读取
2. **筛选本周论文**: 最近7天评估的论文
3. **排序选择**: 按综合评分排序，取 Top 3 精选论文
4. **生成周报**: Markdown格式，保存到 `weekly_reports/` 目录
5. **同步 Obsidian**: 保存至 `$OBSIDIAN_VAULT/PaperClaw/weekly/`
6. **发送邮件**: 通过 Gmail SMTP 发送周报到指定邮箱

## 使用方法

### 手动生成周报
```bash
# 执行周报生成脚本
python skills/weekly-report/scripts/generate_weekly_report_v2.py
```

### 在 Agent 中调用
```
生成人形机器人全身控制与感知控制研究周报
```

## 配置说明

### 邮件配置（.env 文件）

```bash
EMAIL_SENDER=your_gmail@gmail.com
EMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"  # Gmail 应用专用密码
EMAIL_RECIPIENT=recipient1@example.com,recipient2@example.com  # 支持多收件人
OBSIDIAN_VAULT=/path/to/your/obsidian/vault
```

### Cron 定时任务

每周五早上 10 点自动生成并发送周报：

```json
{
  "name": "Weekly Report - Humanoid Robot Control",
  "schedule": {
    "kind": "cron",
    "expr": "0 10 * * 5",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "生成人形机器人全身控制与感知控制研究周报，并发送邮件给指定用户"
  },
  "sessionTarget": "isolated"
}
```

## 注意事项

1. **数据源**：周报必须从 `evaluated_papers.json` 读取，确保数据一致性
2. **评分系统**：使用四维评分系统（控制性能、架构创新、理论贡献、可靠性）
3. **评分公式**：`最终综合评分 = 四维基础评分 × 0.9 + 影响力评分 × 0.1`
4. **邮件发送**：通过 Gmail SMTP 将完整周报发送到指定邮箱（支持多收件人）
5. **Obsidian 同步**：自动保存至 Obsidian vault，需配置 `OBSIDIAN_VAULT` 环境变量

## 更新日志

### v3.0 (2026-03-05)
- ✅ 研究领域切换为人形机器人全身控制与感知控制
- ✅ 新增 Obsidian 周报同步
- ✅ 支持多收件人邮件发送
- ✅ 自动加载 .env 配置文件

### v2.0 (2026-03-01)
- ✅ 添加知识库文档创建功能
- ✅ 优化消息格式，避免过长

### v1.0
- ✅ 初始版本：周报生成与邮件发送
