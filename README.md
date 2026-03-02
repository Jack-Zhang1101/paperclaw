# PaperClaw - Surrogate Modeling Expert
an OpenClaw Agent that can automatically search-review-critque arxiv papers relevant to specific topics (we use Scientific ML and 3D geometry surrogate modeling as a demo).
<div align="center">

**一个基于 OpenClaw 的三维几何代理模型领域论文自动检索、总结、评估和周报生成智能体**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Agent-blue)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[English](README_EN.md) | 简体中文

</div>

---

## 📋 项目简介

PaperAgent 是一个专门用于三维几何代理模型（3D Surrogate Modeling）领域的科研助手智能体。它能够：

- 🔍 **自动检索**：每天从 arXiv 检索最新相关论文
- 📝 **深度总结**：对论文进行专业级总结，回答10个核心问题
- 📊 **多维评估**：基于四维评分系统（工程应用、架构创新、理论贡献、可靠性）+ Date-Citation权衡机制
- 📈 **周报生成**：每周自动生成精选论文周报，通过如流消息推送

### 核心特点

✅ **专业领域聚焦**：专注于三维几何代理模型、神经算子学习、PDE求解
✅ **自动化工作流**：定时任务自动执行，无需手动干预
✅ **科学评分体系**：四维评分 + Date-Citation权衡，公平对比不同时期论文
✅ **完整数据管理**：结构化存储论文PDF、总结、评分、元数据
✅ **知识库集成**：自动创建知识库文档，方便团队协作

---

## 🎯 适用场景

### 科研人员
- 快速了解领域最新进展
- 自动化文献调研
- 跟踪重要论文的引用情况

### 工程师
- 评估新方法的工程应用价值
- 寻找适合工业场景的解决方案
- 了解最新技术趋势

### 团队协作
- 自动化周报生成
- 知识库文档管理
- 如流消息推送

---

## 🏗️ 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Platform                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Surrogate-Modeling Expert Agent             │  │
│  │                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│  │  │ arXiv Search │  │ Paper Review │  │Weekly Rpt │ │  │
│  │  │    Skill     │  │    Skill     │  │   Skill   │ │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Workspace: 3d_surrogate_proj              │
│                                                              │
│  papers/                        weekly_reports/              │
│  ├── DeepONet/                  └── 2026-03-02_weekly.md    │
│  │   ├── DeepONet.pdf                                          │
│  │   ├── summary.md                                            │
│  │   ├── scores.md                                             │
│  │   └── metadata.json                                         │
│  ├── FNO/                                                      │
│  └── ...                                                       │
│                                                              │
│  papers/evaluated_papers.json (论文索引)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services                                │
│                                                              │
│  arXiv API          Semantic Scholar      百度知识库          │
│  (论文检索)         (引用数据)          (文档管理)           │
│                                                              │
│  如流消息 (SO)                                                │
│  (周报推送)                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. Agent 定义层
- **AGENT.md**：Agent 角色定位、专业领域、核心任务
- **models.json**：模型配置（GLM-4.7-internal）
- **README.md**：Agent 使用说明

#### 2. 技能模块层
- **arxiv-search**：arXiv 论文检索
- **paper-review**：论文总结和评估
- **weekly-report**：周报生成和推送
- **semantic-scholar**：引用数据获取

#### 3. 数据存储层
- **papers/**：论文目录（PDF、summary、scores、metadata）
- **evaluated_papers.json**：论文索引（去重、排序）
- **weekly_reports/**：周报文件
- **search_logs/**：检索日志

#### 4. 外部服务层
- arXiv API：论文检索
- Semantic Scholar API：引用数据
- 百度知识库 API：文档管理
- 如流消息 API：消息推送

---

## 📦 项目结构

```
PaperAgent_Open/
├── README.md                    # 项目说明文档（本文件）
├── QUICKSTART.md                # 快速入门指南
├── INSTALLATION.md              # 详细安装指南
├── CONFIGURATION.md             # 配置说明
├── ARCHITECTURE.md              # 架构设计文档
├── API_REFERENCE.md             # API 参考
├── TROUBLESHOOTING.md           # 故障排查
├── CONTRIBUTING.md              # 贡献指南
├── LICENSE                      # MIT 许可证
│
├── agent/                       # Agent 核心文件
│   ├── AGENT.md                 # Agent 定义（角色、任务、专业领域）
│   ├── README.md                # Agent 使用说明
│   ├── models.json              # 模型配置
│   └── sessions/                # 会话数据（运行时生成）
│
├── skills/                      # 技能模块
│   ├── arxiv-search/
│   │   └── SKILL.md             # arXiv 检索技能说明
│   │
│   ├── paper-review/
│   │   └── SKILL.md             # 论文评估技能说明
│   │
│   ├── weekly-report/
│   │   ├── SKILL.md             # 周报生成技能说明
│   │   └── scripts/
│   │       └── generate_weekly_report_v2.py  # 周报生成脚本
│   │
│   └── semantic-scholar/
│       ├── SKILL.md             # Semantic Scholar API 说明
│       └── semantic_scholar_api.py  # API 客户端
│
├── workspace/                   # 工作区（运行时生成）
│   └── 3d_surrogate_proj/       # 项目工作目录
│       ├── papers/              # 论文存储
│       │   ├── DeepONet/
│       │   │   ├── DeepONet.pdf
│       │   │   ├── summary.md
│       │   │   ├── scores.md
│       │   │   └── metadata.json
│       │   ├── FNO/
│       │   └── ...
│       │   └── evaluated_papers.json  # 论文索引
│       │
│       ├── weekly_reports/      # 周报存储
│       ├── scripts/            # 辅助脚本
│       └── search_logs/        # 检索日志
│
├── docs/                        # 详细文档
│   ├── evaluation_system.md     # 评分系统详解
│   ├── data_structure.md        # 数据结构说明
│   ├── workflow.md              # 工作流程详解
│   └── examples/               # 示例文档
│
└── examples/                    # 示例数据
    ├── sample_paper/            # 示例论文目录
    │   ├── summary.md
    │   ├── scores.md
    │   └── metadata.json
    └── sample_weekly_report.md  # 示例周报
```

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- OpenClaw 平台（已安装）
- 百度内部账号（用于知识库和如流消息）

### 5分钟快速部署

```bash
# 1. 克隆或下载项目
cd /path/to/your/workspace
git clone https://github.com/yourusername/PaperAgent_Open.git
cd PaperAgent_Open

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys

# 4. 部署 Agent
# 在 OpenClaw 中创建新 Agent，使用 agent/ 目录下的文件

# 5. 配置定时任务
# 使用 OpenClaw 的 cron 功能配置每日检索和周报生成

# 6. 测试运行
# 手动触发一次论文检索任务
```

详细步骤请参考 [QUICKSTART.md](QUICKSTART.md)

---

## 📚 核心功能

### 1. 论文自动检索

**触发方式**：
- 定时触发：每天 21:00 自动执行
- 手动触发：通过对话指令触发

**检索策略**：
- 使用 8 个核心关键词检索 arXiv
- 每个关键词检索 30 篇论文
- 智能去重（arXiv ID、标题匹配）
- 基于相关性评分筛选 Top 3 精选论文

**核心关键词**：
```
geometry-aware neural operator
neural operator 3D mesh
operator learning arbitrary geometry
transformer PDE solver 3D
physics-informed neural network 3D geometry
surrogate model 3D geometry
deep learning surrogate CFD
neural operator fluid dynamics
```

### 2. 论文深度总结

每篇论文的 `summary.md` 必须回答以下 10 个核心问题：

1. 论文试图解决什么问题？
2. 这是一个新问题吗？以前的研究工作有没有解决相同或类似的问题？
3. 这篇文章要验证一个什么科学假设？
4. 有哪些相关研究？如何归类？谁是这一课题在领域内值得关注的研究员？
5. 论文中提到的解决方案之关键是什么？
6. 论文中的实验是如何设计的？
7. 用于定量评估的数据集是什么？代码有没有开源？
8. 论文中的实验及结果有没有很好地支持需要验证的科学假设？
9. 这篇论文到底有什么贡献？
10. 下一步怎么做？有什么工作可以继续深入？

### 3. 多维评估系统

#### 四维评分体系

| 维度 | 权重 | 说明 |
|------|------|------|
| 工程应用价值 | - | 解决实际工程问题的能力、工业级验证、部署可行性 |
| 网络架构创新 | - | 架构设计新颖性、模块机制创新、对比优势 |
| 理论贡献 | - | 数学框架、定理证明、理论连接、理论深度 |
| 结果可靠性 | - | 实验严谨性、开源支持、可复现性 |

#### Date-Citation 权衡机制

**设计目标**：公平对比不同发表时间论文的影响力

**调整规则**：

| 论文年龄 | 引用情况 | 调整因子 |
|---------|---------|---------|
| ≤ 3个月 | - | +0.2（最新论文奖励） |
| 3-24个月 | 引用数 ≥ 50 | +0.5 |
| 3-24个月 | 引用数 20-49 | +0.3 |
| 3-24个月 | 引用数 10-19 | +0.2 |
| 3-24个月 | 引用数 < 10 | +0.1 |
| > 24个月 | 引用数 ≥ 200 | +0.5 |
| > 24个月 | 引用数 100-199 | +0.4 |
| > 24个月 | 引用数 50-99 | +0.3 |
| > 24个月 | 引用数 20-49 | +0.2 |
| > 24个月 | 引用数 < 20 | +0.0 |

**引用密度奖励**（适用于所有年龄段）：
- 引用密度 ≥ 10次/月：额外 +0.2
- 引用密度 5-10次/月：额外 +0.1

**最终评分公式**：
```
四维基础评分 = (工程应用 + 架构创新 + 理论贡献 + 可靠性) / 4
最终综合评分 = 四维基础评分 × 0.9 + 影响力评分 × 0.1
```

### 4. 周报自动生成

**生成流程**：
1. 从 `evaluated_papers.json` 读取本周评估的论文
2. 从 `papers/{short_title}/scores.md` 读取四维评分详情
3. 从 `papers/{short_title}/summary.md` 读取完整总结
4. 从 `papers/{short_title}/metadata.json` 读取关键词等元信息
5. 按综合评分排序，筛选 Top 3 精选论文
6. 为每篇精选论文创建独立知识库文档
7. 生成 Markdown 周报
8. 创建周报知识库文档
9. 发送如流消息（包含周报链接和精选论文链接）

**周报内容**：
- 本周概览（评估论文总数、精选推荐）
- Top 3 精选论文（完整评分、推荐理由）
- 完整评分列表（所有本周评估的论文）
- 附录：精选论文知识库文档链接

---

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# 百度智能云 API Key
BAIDU_API_KEY=your_baidu_api_key_here

# 百度地图 API Key（可选）
BAIDU_MAP_AK=your_baidu_map_ak_here

# Comate Auth Token（知识库和如流消息）
COMATE_AUTH_TOKEN=your_comate_token_here

# SerpAPI Key（Google Scholar，可选）
SERPAPI_KEY=your_serpapi_key_here
```

### 知识库配置

编辑 `skills/weekly-report/scripts/generate_weekly_report_v2.py`：

```python
# 知识库配置
self.ku_repo_id = "your_repository_guid"  # 你的知识库ID
self.ku_parent_doc_id = "your_parent_doc_guid"  # 父文档ID
```

### 如流消息配置

编辑 `skills/weekly-report/scripts/generate_weekly_report_v2.py`：

```python
# 如流消息接收人
self.recipients = ["username1", "username2"]  # 替换为你的用户名
```

### 定时任务配置

使用 OpenClaw 的 cron 功能配置：

**每日论文检索**（每天 21:00）：
```json
{
  "name": "Daily Paper Search - Surrogate Modeling",
  "schedule": {
    "kind": "cron",
    "expr": "0 21 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "执行每日论文检索任务：检索三维几何代理模型领域的最新论文"
  },
  "sessionTarget": "isolated"
}
```

**每周报告生成**（每周日 10:00）：
```json
{
  "name": "Weekly Report - Surrogate Modeling",
  "schedule": {
    "kind": "cron",
    "expr": "0 10 * * 0",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "生成三维几何代理模型研究周报，创建知识库文档并发送给指定用户"
  },
  "sessionTarget": "isolated"
}
```

---

## 📖 使用示例

### 手动触发论文检索

在 OpenClaw 对话中输入：

```
帮我检索 geometry-aware neural operator 相关的最新论文
```

或者指定关键词：

```
帮我搜索 transformer for PDE 的最新研究
```

### 查看论文总结

```bash
# 查看论文目录
ls workspace/3d_surrogate_proj/papers/

# 查看某篇论文的总结
cat workspace/3d_surrogate_proj/papers/DeepONet/summary.md

# 查看某篇论文的评分
cat workspace/3d_surrogate_proj/papers/DeepONet/scores.md
```

### 查看周报

```bash
# 查看周报目录
ls workspace/3d_surrogate_proj/weekly_reports/

# 查看最新周报
cat workspace/3d_surrogate_proj/weekly_reports/*.md
```

### 管理定时任务

```bash
# 查看所有定时任务
openclaw cron list

# 临时禁用任务
openclaw cron update <job-id> --patch '{"enabled": false}'

# 立即执行任务
openclaw cron run <job-id>
```

---

## 📊 数据结构

### 论文目录结构

```
papers/
├── DeepONet/                    # 论文目录（使用 short_title）
│   ├── DeepONet.pdf            # 论文原文
│   ├── summary.md              # 论文总结（10个问题）
│   ├── scores.md               # 论文评分（四维评分）
│   └── metadata.json           # 元数据（作者、关键词、引用数等）
├── FNO/
│   ├── FNO.pdf
│   ├── summary.md
│   ├── scores.md
│   └── metadata.json
└── evaluated_papers.json       # 论文索引（去重、排序）
```

### metadata.json 格式

```json
{
  "arxiv_id": "1910.03193",
  "title": "Learning Nonlinear Operators via DeepONet Based on the Universal Approximation Theorem of Operators",
  "short_title": "DeepONet",
  "authors": ["Lu Lu", "Pengzhan Jin", "George Em Karniadakis"],
  "venue": "Nature Machine Intelligence",
  "publication_date": "2019-10-08",
  "citations": 3144,
  "evaluated_date": "2026-03-01",
  "scores": {
    "engineering_value": 9.0,
    "architecture_innovation": 10.0,
    "theoretical_contribution": 9.0,
    "result_reliability": 9.0,
    "impact": 10.0,
    "final_score": 9.33
  },
  "keywords": [
    "operator learning",
    "DeepONet",
    "neural operators",
    "universal approximation theorem"
  ]
}
```

### evaluated_papers.json 格式

```json
{
  "description": "已评估论文列表（精炼版 - 仅包含基础信息和最终评分）",
  "papers": [
    {
      "arxiv_id": "1910.03193",
      "title": "Learning Nonlinear Operators via DeepONet Based on the Universal Approximation Theorem of Operators",
      "short_title": "DeepONet",
      "final_score": 9.33,
      "evaluated_date": "2026-03-01"
    }
  ],
  "last_updated": "2026-03-01T11:47:43.560831"
}
```

---

## 🤝 贡献指南

欢迎贡献代码、文档或提出建议！

### 贡献方式

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献类型

- 🐛 Bug 修复
- ✨ 新功能
- 📝 文档改进
- 🎨 代码优化
- ⚡ 性能提升
- ✅ 测试用例

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- OpenClaw 平台 - 强大的 AI Agent 框架
- arXiv - 开放的学术论文预印本平台
- Semantic Scholar - 丰富的学术引用数据
- 百度知识库 - 便捷的文档管理平台

---

## 📧 联系方式

- **项目主页**: https://github.com/yourusername/PaperAgent_Open
- **问题反馈**: https://github.com/yourusername/PaperAgent_Open/issues
- **讨论区**: https://github.com/yourusername/PaperAgent_Open/discussions

---

## 🗺️ 路线图

### v1.0 (当前版本)
- ✅ arXiv 论文自动检索
- ✅ 论文深度总结（10个问题）
- ✅ 四维评分系统
- ✅ Date-Citation 权衡机制
- ✅ 周报自动生成
- ✅ 知识库文档创建
- ✅ 如流消息推送

### v1.1 (计划中)
- 🔄 支持多个论文数据库（arXiv, PubMed, IEEE Xplore）
- 🔄 多语言支持（英文、中文）
- 🔄 可视化评分雷达图
- 🔄 论文相似度分析
- 🔄 引用网络可视化

### v2.0 (未来)
- 🔮 多模态论文理解（图表、公式）
- 🔮 自动化文献综述生成
- 🔮 论文推荐系统
- 🔮 协作式论文标注

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！**

Made with ❤️ by [Your Name]

</div>
