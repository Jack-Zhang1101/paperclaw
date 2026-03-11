# PaperClaw - Surrogate Modeling Expert

An OpenClaw Agent that automatically searches, reviews, and critiques papers from arXiv and Semantic Scholar for humanoid and legged robot control research.

<div align="center">

**基于 OpenClaw 的论文自动检索、总结、评估智能体**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Agent-blue)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## ?? 核心功能

| 功能 | 说明 | 触发方式 |
|------|------|---------|
| 🔍 **每日检索** | 多来源检索（arXiv + Semantic Scholar），自动去重，精选 Top 3 | 每天 20:00 (Asia/Singapore) |
| 📝 **深度总结** | 回答 10 个核心问题，生成 summary.md | 检索后自动执行 |
| 📊 **四维评分** | 工程应用 + 架构创新 + 理论贡献 + 可靠性 | 总结后自动执行 |
| ?? **周报生成** | Top 3 精选论文报告，如流消息推送 | 每周日 10:00 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PaperClaw Agent                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │daily-search│ │arxiv-search│ │paper-review│ │weekly-rpt│ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  workspace/papers/                                          │
│  ├── {paper}/metadata.json  ← 结构化评分数据                │
│  ├── {paper}/summary.md     ← 深度总结                      │
│  ├── {paper}/scores.md      ← 评分报告                      │
│  └── evaluated_papers.json  ← 去重索引                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 每日检索（自动）

```bash
# 默认从 Semantic Scholar 检索，并按 robotics venue 过滤
python skills/daily-search/scripts/daily_paper_search.py --top 3

# 显式切回 arXiv 检索
python skills/daily-search/scripts/daily_paper_search.py \
  --source arxiv \
  --top 3

# 定时任务已配置：每天 20:00 (Asia/Singapore) 自动执行
```

### 2. 论文评估

```bash
# 获取引用数据
python skills/semantic-scholar/semantic_scholar_api.py paper-by-arxiv "2401.12345"

# 更新评估数据库（带文件锁 + 去重）
python skills/paper-review/scripts/update_registry.py \
  --id "2401.12345" --title "Paper Title" --short_title "ShortName" --score 8.5
```

### 3. 周报生成

```bash
python skills/weekly-report/scripts/generate_weekly_report_v2.py
```

---

## 📊 评分体系

### 四维评分 + Date-Citation 权衡

```
最终评分 = 四维基础评分 × 0.9 + 影响力评分 × 0.1

四维基础评分 = (工程应用 + 架构创新 + 理论贡献 + 可靠性) / 4
```

**Date-Citation 调整因子**：
- ≤3个月新论文：+0.2
- 3-24个月 + 引用≥50：+0.5
- >24个月 + 引用≥200：+0.5
- 引用密度≥10次/月：额外 +0.2

---

## 📁 项目结构

```
PaperClaw/
├── agent/
│   ├── AGENT.md          # Agent 角色定义
│   └── schedules.json    # 定时任务配置
├── skills/
│   ├── daily-search/     # 每日检索技能 (NEW)
│   ├── arxiv-search/     # arXiv 搜索脚本
│   ├── paper-review/     # 论文评估 + 安全写入
│   ├── semantic-scholar/ # Semantic Scholar 检索与引用数据 API
│   └── weekly-report/    # 周报生成脚本
└── examples/             # 示例数据
```

---

## 🔄 更新日志

### v1.2.0 (2026-03-10) - 论文来源增广

**🚀 新增功能**
- ✅ **多来源论文检索**：`daily_paper_search.py` 支持 `--source arxiv|semantic`
- ✅ **Venue 定向筛选**：Semantic Scholar 可按 `TRO / ICRA / RA-L / IROS / Science Robotics / IJRR` 过滤
- ✅ **来源元数据落盘**：`metadata.json` / `search_log` / `pending_evaluation` 记录 `source`、`source_link`、`venue`、`doi`

**📝 文档更新**
- ✅ 将“仅 arXiv”说明更新为“多来源检索”
- ✅ 补充 Semantic Scholar 检索用法与参数示例

### v1.1.0 (2026-03-04) - 架构优化与每日任务

**🚀 新增功能**
- ✅ **每日论文检索任务** (`daily-search` 技能)
  - 批量搜索 + 自动去重 + 相关性排序
  - PDF 下载 + 元数据创建
  - 如流消息每日摘要推送
  - 定时任务：每天 20:00 (Asia/Singapore)

**?? 架构优化**
- ✅ **消除脆弱的正则解析**：周报从 `metadata.json` 读取结构化评分，不再依赖 `scores.md` 正则匹配
- ✅ **解耦大模型与长代码块**：`search_arxiv.py` 脚本化，减少 ~200 行 heredoc Token 消耗
- ✅ **安全并发写入**：`update_registry.py` 支持文件锁 + 去重检查
- ✅ **强制思维链**：评分时必须使用 `<think>` 标签记录推理过程

**📝 文档更新**
- ✅ 新增 `skills/daily-search/SKILL.md`
- ✅ 更新 `agent/AGENT.md` 添加任务3说明
- ✅ 新增 `agent/schedules.json` 定时任务配置
- ✅ 精简 `arxiv-search/SKILL.md` 和 `paper-review/SKILL.md`

### v1.0.0 (2026-03-01) - 初始版本

- ✅ arXiv 论文自动检索
- ✅ 论文深度总结（10个问题）
- ✅ 四维评分系统 + Date-Citation 权衡
- ✅ 周报自动生成 + 知识库集成
- ✅ 如流消息推送

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star！**

---

*本文档由 Claude Opus 4.5 自动生成*

</div>
