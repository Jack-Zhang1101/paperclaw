# Daily Paper Search Skill

## 功能描述
每日自动检索多来源论文，聚焦**人形机器人全身控制与感知控制**领域，与已评估数据库去重，精选 Top N 论文待评估，发送每日检索摘要。

## 研究领域关键词

### 全身控制（Whole-Body Control）
- humanoid robot whole-body control
- whole-body motion planning humanoid
- whole-body locomotion manipulation
- loco-manipulation humanoid
- contact-rich whole-body control
- model predictive control humanoid robot
- hierarchical whole-body controller

### 运动控制与步态（Locomotion）
- humanoid robot locomotion
- legged robot control reinforcement learning
- bipedal robot walking running
- humanoid robot agile locomotion
- zero-shot sim-to-real humanoid
- humanoid parkour climbing

### 感知控制（Perception-Action）
- visual-motor control humanoid
- proprioception humanoid robot
- sensorimotor learning robot
- vision-based humanoid control
- egocentric perception humanoid
- tactile sensing humanoid manipulation
- multimodal perception robot control

### 学习与规划（Learning & Planning）
- reinforcement learning humanoid robot
- imitation learning whole-body control
- motion retargeting humanoid
- teleoperation humanoid robot
- diffusion policy humanoid
- transformer robot policy humanoid

### 排除关键词（避免不相关领域）
- epidemic, epidemiology
- finance, economics
- NLP, language model（非机器人应用）
- autonomous driving（非人形机器人）

## 核心流程

```
┌─────────────────────────────────────────────────────────────┐
│  09:00 Asia/Shanghai 自动触发                               │
│       ↓                                                     │
│  1. 批量搜索多来源论文 (arXiv / Semantic Scholar)          │
│       ↓                                                     │
│  2. 搜索结果去重 (ID + 标准化标题)                          │
│       ↓                                                     │
│  3. 与 evaluated_papers.json 去重                           │
│       ↓                                                     │
│  4. 相关性评分排序                                          │
│       ↓                                                     │
│  5. 选择 Top 3 精选论文                                     │
│       ↓                                                     │
│  6. 下载 PDF + 创建元数据                                   │
│       ↓                                                     │
│  7. 生成待评估任务清单                                      │
│       ↓                                                     │
│  8. 同步 Obsidian 日报                                      │
│       ↓                                                     │
│  9. Agent 执行 paper-review 深度评估（summary + scores）    │
│       ↓                                                     │
│  10. 📧 发送深度评估邮件（send_daily_evaluation_email.py） │
└─────────────────────────────────────────────────────────────┘
```

## 使用方法

### 手动执行

```bash
# 完整流程（默认 Semantic Scholar）
python skills/daily-search/scripts/daily_paper_search.py

# 精选 5 篇论文（默认 3 篇）
python skills/daily-search/scripts/daily_paper_search.py --top 5

# 显式使用 Semantic Scholar 检索，并按 robotics venue 过滤
python skills/daily-search/scripts/daily_paper_search.py \
  --source semantic \
  --venues tro,icra,ral,iros,science_robotics,ijrr

# 显式切回 arXiv
python skills/daily-search/scripts/daily_paper_search.py --source arxiv

# 仅搜索，不下载 PDF
python skills/daily-search/scripts/daily_paper_search.py --skip-download

# 干跑模式（仅搜索，不下载不发送）
python skills/daily-search/scripts/daily_paper_search.py --dry-run
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--top N` | 精选论文数量（默认 3） |
| `--source {arxiv,semantic}` | 论文来源，默认 `semantic` |
| `--venues V1,V2` | `source=semantic` 时按 venue 过滤 |
| `--theme {humanoid,quadruped,mixed}` | 检索主题，默认 `mixed` |
| `--limit-per-query N` | 每个查询返回的最大论文数 |
| `--skip-download` | 跳过 PDF 下载 |
| `--dry-run` | 干跑模式，仅搜索不执行实际操作 |
| `--workspace PATH` | 指定工作空间路径 |

## 输出文件

执行后将生成以下文件：

| 文件 | 路径 | 说明 |
|------|------|------|
| 搜索日志 | `search_logs/YYYY-MM-DD_search_log.json` | 当日搜索统计和去重详情 |
| 待评估清单 | `pending_evaluation_YYYY-MM-DD.json` | Agent 待执行的评估任务 |
| 论文元数据 | `papers/{short_title}/metadata.json` | 每篇精选论文的基础信息，包含 `source` / `source_link` / `venue` / `doi` |
| 论文 PDF | `papers/{short_title}/*.pdf` | 下载的论文 PDF |
| Obsidian 日报 | `$OBSIDIAN_VAULT/PaperClaw/daily/YYYY-MM-DD.md` | 同步到 Obsidian |

## 后续评估流程

每日检索完成后，Agent 需要执行以下步骤完成论文评估：

### 步骤 1: 查看待评估清单

```bash
cat workspace/pending_evaluation_YYYY-MM-DD.json
```

### 步骤 2: 对每篇论文执行深度评估

对于清单中的每篇论文，按照 `paper-review` 技能流程执行：

1. **获取 Semantic Scholar 数据**
```bash
python skills/semantic-scholar/semantic_scholar_api.py paper-by-arxiv "[arxiv_id]" --format json > papers/{short_title}/metadata.json
```

2. **阅读论文并撰写总结**
   - 生成 `papers/{short_title}/summary.md`

3. **进行四维评分**
   - 生成 `papers/{short_title}/scores.md`
   - 使用 `<think>` 标签记录推理过程

4. **更新已评估论文数据库**
```bash
python skills/paper-review/scripts/update_registry.py \
  --id "[arxiv_id]" \
  --title "[论文标题]" \
  --short_title "[short_title]" \
  --score "[最终评分]"
```

### 步骤 3: 确认评估完成

检查 `evaluated_papers.json` 确认论文已添加：
```bash
cat workspace/papers/evaluated_papers.json | python -m json.tool | tail -20
```

### 步骤 4: 发送深度评估邮件

所有论文评估完成后，发送包含完整摘要和四维评分的邮件：

```bash
python skills/daily-search/scripts/send_daily_evaluation_email.py \
  --workspace ~/.paperclaw/workspace
```

邮件内容包含：
- 每篇论文的完整总结（`summary.md`）
- 四维评分详情（`scores.md`）
- 论文来源链接（优先 arXiv，其次 DOI / PDF）

## 定时任务配置

### OpenClaw Cron 配置

在 Agent 配置中添加定时任务：

```json
{
  "name": "Daily Paper Search - Humanoid Robot Control",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "执行每日论文检索任务：优先从多来源（arXiv / Semantic Scholar）检索人形机器人全身控制与感知控制领域的最新论文，然后对精选的 Top 3 论文执行完整的 paper-review 流程（总结、评分、更新数据库）"
  },
  "sessionTarget": "isolated"
}
```

### 系统 Crontab 配置（备选）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务 (09:00 Asia/Shanghai = 01:00 UTC)
0 1 * * * cd /path/to/PaperClaw && python skills/daily-search/scripts/daily_paper_search.py --source semantic --venues tro,icra,ral,iros,science_robotics,ijrr >> /var/log/daily_paper_search.log 2>&1
```

## 去重机制说明

### 三层去重策略

1. **搜索结果内部去重** (`search_arxiv.py`)
   - arXiv ID 去重
   - 标准化标题去重（保留版本标识符如 ++、-2）
   - 排除不相关领域

2. **与已评估数据库去重** (`daily_paper_search.py`)
   - 读取 `evaluated_papers.json`
   - 比对 arXiv ID
   - 比对标题（不区分大小写）

3. **写入时去重** (`update_registry.py`)
   - 最后一道防线
   - 防止并发写入重复

## 注意事项

1. **API 限制**: arXiv API 与 Semantic Scholar API 都有限流，脚本已支持请求间隔
2. **网络依赖**: PDF 下载和邮件发送需要网络连接
3. **评估时间**: 深度评估每篇论文需要 Agent 投入时间，建议每日精选 3 篇
4. **存储空间**: PDF 文件会占用存储空间，定期清理旧论文

## 更新日志

### v2.1 (2026-03-10)
- ✅ 新增多来源检索（arXiv + Semantic Scholar）
- ✅ 新增 venue 定向筛选参数
- ✅ 搜索产物记录来源、链接、venue、doi

### v2.0 (2026-03-05)
- ✅ 研究领域切换为人形机器人全身控制与感知控制
- ✅ 新增 Obsidian 日报同步
- ✅ 新增邮件发送支持

### v1.0 (2026-03-04)
- ✅ 初始版本
- ✅ 批量搜索与去重
- ✅ PDF 下载
- ✅ 待评估任务清单生成
