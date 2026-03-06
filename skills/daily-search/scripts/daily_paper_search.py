#!/usr/bin/env python3
"""
每日论文检索与筛选脚本
功能：
1. 批量搜索 arXiv 论文
2. 与 evaluated_papers.json 去重
3. 相关性排序，选 Top N 待评估
4. 下载 PDF
5. 生成待评估清单
6. 发送每日检索摘要如流消息

使用方法:
  python daily_paper_search.py                    # 完整流程
  python daily_paper_search.py --skip-download    # 跳过PDF下载
  python daily_paper_search.py --dry-run          # 仅搜索，不下载不发送
"""
import os
import sys
import json
import argparse
import urllib.request
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# 自动加载 .env 文件（从项目根目录向上查找）
def _load_dotenv():
    search = Path(__file__).resolve()
    for _ in range(6):
        env_file = search / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            break
        search = search.parent

_load_dotenv()

# 添加技能路径
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILLS_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SKILLS_DIR / 'arxiv-search' / 'scripts'))
sys.path.insert(0, '/home/gem/.openclaw/skills/so-send-message/scripts')

from search_arxiv import batch_search, deduplicate_papers, score_paper_relevance


class DailyPaperSearcher:
    """每日论文检索器"""
    
    def __init__(self, workspace_path=None):
        if workspace_path:
            self.workspace_dir = Path(workspace_path)
        else:
            self.workspace_dir = Path("/home/gem/.openclaw/workspace/3d_surrogate_proj")

        self.papers_dir = self.workspace_dir / "papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        self.evaluated_file = self.papers_dir / "evaluated_papers.json"
        self.search_logs_dir = self.workspace_dir / "search_logs"
        self.search_logs_dir.mkdir(parents=True, exist_ok=True)

        # Obsidian 配置
        obsidian_vault = os.environ.get("OBSIDIAN_VAULT", "")
        self.obsidian_daily_dir = Path(obsidian_vault) / "PaperClaw" / "daily" if obsidian_vault else None

        # 如流消息接收人
        self.recipients = ["guhaohao"]
        # 邮件配置（与 weekly-report 保持一致，支持逗号分隔多收件人）
        self.email_sender = os.environ.get("EMAIL_SENDER", "")
        self.email_password = os.environ.get("EMAIL_APP_PASSWORD", "")
        recipients_str = os.environ.get("EMAIL_RECIPIENT", "")
        self.email_recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
        
    def load_evaluated_papers(self):
        """加载已评估论文列表（用于去重）"""
        if not self.evaluated_file.exists():
            return set(), set()
        
        try:
            with open(self.evaluated_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            papers_list = data.get('papers', data.get('evaluated_papers', []))
            evaluated_ids = {p.get('arxiv_id', '') for p in papers_list}
            evaluated_titles = {p.get('title', '').lower().strip() for p in papers_list}
            
            print(f"✅ 已加载 {len(evaluated_ids)} 篇已评估论文用于去重")
            return evaluated_ids, evaluated_titles
        except Exception as e:
            print(f"⚠️  读取已评估论文失败: {e}")
            return set(), set()
    
    def filter_against_evaluated(self, papers, evaluated_ids, evaluated_titles):
        """过滤掉已评估的论文"""
        new_papers = []
        skipped = []
        
        for paper in papers:
            arxiv_id = paper.get('arxiv_id', '')
            title = paper.get('title', '').lower().strip()
            
            if arxiv_id in evaluated_ids:
                skipped.append({'paper': paper, 'reason': f'ID已评估: {arxiv_id}'})
                continue
            
            if title in evaluated_titles:
                skipped.append({'paper': paper, 'reason': '标题已评估'})
                continue
            
            new_papers.append(paper)
        
        return new_papers, skipped
    
    def download_pdf(self, paper, save_dir):
        """下载论文 PDF"""
        pdf_url = paper.get('pdf_url')
        if not pdf_url:
            print(f"   ⚠️  无 PDF 链接: {paper['title'][:50]}...")
            return None
        
        # 生成安全文件名
        safe_title = re.sub(r'[^\w\s-]', '', paper['title'])
        safe_title = re.sub(r'[-\s]+', '_', safe_title)[:80]
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        pdf_path = save_path / f"{safe_title}.pdf"
        
        try:
            print(f"   ?? 下载中: {paper['title'][:50]}...")
            urllib.request.urlretrieve(pdf_url, pdf_path)
            print(f"   ✅ 已保存: {pdf_path.name}")
            return str(pdf_path)
        except Exception as e:
            print(f"   ❌ 下载失败: {e}")
            return None
    
    def create_paper_metadata(self, paper, pdf_path=None):
        """创建论文元数据文件"""
        short_title = self.generate_short_title(paper['title'])
        paper_dir = self.papers_dir / short_title
        paper_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "arxiv_id": paper.get('arxiv_id', ''),
            "title": paper.get('title', ''),
            "short_title": short_title,
            "authors": paper.get('authors', []),
            "summary": paper.get('summary', ''),
            "published": paper.get('published', ''),
            "pdf_url": paper.get('pdf_url', ''),
            "pdf_path": pdf_path,
            "relevance_score": paper.get('relevance_score', 0),
            "search_date": datetime.now().isoformat(),
            "status": "pending_evaluation"
        }
        
        metadata_path = paper_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return short_title, str(paper_dir)
    
    def generate_short_title(self, title):
        """生成简短标题（用于文件夹名）"""
        # 提取关键词
        words = re.findall(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)|[a-z]+', title)
        
        # 优先使用大写开头的词（通常是方法名）
        key_words = [w for w in words if w[0].isupper()][:3]
        
        if len(key_words) < 2:
            key_words = words[:4]
        
        short_title = '-'.join(key_words)
        
        # 确保唯一性
        if (self.papers_dir / short_title).exists():
            short_title = f"{short_title}-{datetime.now().strftime('%m%d')}"
        
        return short_title[:50]
    
    def save_search_log(self, search_results, selected_papers, skipped_evaluated):
        """保存搜索日志"""
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_path = self.search_logs_dir / f"{log_date}_search_log.json"
        
        log_data = {
            "search_date": datetime.now().isoformat(),
            "total_searched": len(search_results),
            "after_dedup": len(search_results),  # 搜索脚本已去重
            "skipped_evaluated": len(skipped_evaluated),
            "selected_count": len(selected_papers),
            "selected_papers": [
                {
                    "arxiv_id": p.get('arxiv_id'),
                    "title": p.get('title'),
                    "relevance_score": p.get('relevance_score', 0)
                }
                for p in selected_papers
            ],
            "skipped_details": [
                {
                    "arxiv_id": s['paper'].get('arxiv_id'),
                    "title": s['paper'].get('title')[:60],
                    "reason": s['reason']
                }
                for s in skipped_evaluated[:20]
            ]
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"📝 搜索日志已保存: {log_path}")
        return log_path
    
    # ─── 深度评估邮件相关方法 ────────────────────────────────────────

    def load_today_papers(self, date_str):
        """从 pending_evaluation_YYYY-MM-DD.json 读取今日待评估论文列表"""
        task_file = self.workspace_dir / f"pending_evaluation_{date_str}.json"
        if not task_file.exists():
            print(f"❌ 未找到待评估清单: {task_file}")
            return []
        with open(task_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tasks", [])

    def read_file(self, path):
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                pass
        return None

    def read_metadata(self, paper_dir):
        meta_path = Path(paper_dir) / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def build_evaluation_content(self, papers_data, date_str, truncate_summary=False):
        """构建评估报告内容（Markdown 格式）"""
        evaluated = [p for p in papers_data if p["summary"] or p["scores"]]
        sections = []
        sections.append(f"# 🤖 每日深度评估报告 - {date_str}")
        sections.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"**今日评估**: {len(evaluated)} / {len(papers_data)} 篇\n")
        sections.append("---")

        for i, paper in enumerate(papers_data, 1):
            title = paper.get("title", "Unknown")
            arxiv_id = paper.get("arxiv_id", "")
            summary = paper.get("summary")
            scores = paper.get("scores")
            meta = paper.get("metadata", {})
            final_score = meta.get("scores", {}).get("final_score", "N/A") if meta else "N/A"

            section = [f"\n## {i}. {title}"]
            section.append(f"\n**arXiv**: https://arxiv.org/abs/{arxiv_id}")
            if final_score != "N/A":
                section.append(f"**综合评分**: {final_score}/10")

            if scores:
                section.append(f"\n### 四维评分\n\n{scores.strip()}")
            else:
                section.append("\n*⚠️ 评分详情未生成（paper-review 未完成）*")

            if summary:
                summary_text = summary.strip()
                if truncate_summary and len(summary_text) > 1500:
                    summary_text = summary_text[:1500] + "\n\n*[摘要已截断，完整内容见 Obsidian]*"
                section.append(f"\n### 论文总结\n\n{summary_text}")
            else:
                section.append("\n*⚠️ 论文总结未生成（paper-review 未完成）*")

            section.append("\n---")
            sections.append("\n".join(section))

        sections.append("\n\n*PaperClaw · Humanoid Robot Control Research*")
        return "\n".join(sections)

    def save_evaluation_to_obsidian(self, papers_data, date_str):
        """将深度评估报告追加到 Obsidian 日报文件"""
        if not self.obsidian_daily_dir:
            print("⚠️  未配置 OBSIDIAN_VAULT，跳过 Obsidian 同步")
            return None

        self.obsidian_daily_dir.mkdir(parents=True, exist_ok=True)
        obsidian_path = self.obsidian_daily_dir / f"{date_str}.md"
        content = self.build_evaluation_content(papers_data, date_str, truncate_summary=False)

        if obsidian_path.exists():
            with open(obsidian_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n## 📊 深度评估结果\n\n")
                f.write(content)
        else:
            with open(obsidian_path, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"✅ 深度评估已同步到 Obsidian: {obsidian_path}")
        return obsidian_path

    def send_evaluation_email(self, date_str=None, dry_run=False):
        """读取今日 paper-review 结果，同步 Obsidian 并发送深度评估邮件"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        print("=" * 60)
        print(f"📧 每日深度评估邮件 - {date_str}")
        print("=" * 60)

        tasks = self.load_today_papers(date_str)
        if not tasks:
            print("❌ 无今日论文数据，退出")
            return False

        print(f"✅ 今日论文 {len(tasks)} 篇")
        papers_data = []
        for task in tasks:
            short_title = task.get("short_title", "")
            paper_dir = self.papers_dir / short_title
            summary = self.read_file(paper_dir / "summary.md")
            scores = self.read_file(paper_dir / "scores.md")
            metadata = self.read_metadata(paper_dir)
            papers_data.append({
                "title": task.get("title", "Unknown"),
                "arxiv_id": task.get("arxiv_id", ""),
                "short_title": short_title,
                "summary": summary,
                "scores": scores,
                "metadata": metadata,
            })
            status = "✅" if (summary and scores) else "⚠️ 未完成"
            print(f"  {status} {task.get('title', '')[:55]}...")

        print("\n📓 同步到 Obsidian...")
        self.save_evaluation_to_obsidian(papers_data, date_str)

        body = self.build_evaluation_content(papers_data, date_str, truncate_summary=True)
        subject = f"[PaperClaw] 每日深度评估报告 - {date_str}"

        if dry_run:
            print("\n📧 [DRY-RUN] 邮件主题:", subject)
            print("\n📧 [DRY-RUN] 邮件正文预览:")
            print(body[:800] + "...")
            return True

        if not all([self.email_sender, self.email_password, self.email_recipients]):
            print("⚠️  邮件配置不完整，请检查 .env 中的 EMAIL_SENDER / EMAIL_APP_PASSWORD / EMAIL_RECIPIENT")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_sender
            msg["To"] = ", ".join(self.email_recipients)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, self.email_recipients, msg.as_string())

            print(f"\n✅ 深度评估邮件发送成功: {', '.join(self.email_recipients)}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("❌ Gmail 认证失败，请检查 EMAIL_APP_PASSWORD（需要应用专用密码）")
            return False
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

    # ─── 每日检索 Obsidian 同步 ─────────────────────────────────────

    def save_to_obsidian(self, search_stats, selected_papers):
        """保存每日检索报告到 Obsidian"""
        if not self.obsidian_daily_dir:
            print("⚠️  未配置 OBSIDIAN_VAULT，跳过 Obsidian 同步")
            return None

        self.obsidian_daily_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        obsidian_path = self.obsidian_daily_dir / f"{date_str}.md"

        paper_lines = []
        for i, paper in enumerate(selected_papers, 1):
            relevance = paper.get('relevance_score', 0)
            arxiv_id = paper.get('arxiv_id', 'N/A')
            paper_lines.append(
                f"### {i}. {paper['title']}\n\n"
                f"- **arXiv**: https://arxiv.org/abs/{arxiv_id}\n"
                f"- **相关性评分**: {relevance}\n"
                f"- **摘要**: {paper.get('summary', '')[:300]}...\n"
            )

        content = f"""# 每日论文检索报告 - {date_str}

## 检索统计

- 批量搜索论文数: {search_stats['total_searched']}
- 去重后论文数: {search_stats['after_dedup']}
- 已评估跳过: {search_stats['skipped_evaluated']}
- 今日精选: {search_stats['selected_count']} 篇

## 今日精选论文 (Top {len(selected_papers)})

{chr(10).join(paper_lines)}
---

*Surrogate-Modeling Expert Agent*
*检索时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(obsidian_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 日报已同步到 Obsidian: {obsidian_path}")
        return obsidian_path

    def generate_evaluation_task(self, selected_papers):
        """生成待评估任务清单（供 Agent 执行）"""
        task_date = datetime.now().strftime("%Y-%m-%d")
        task_path = self.workspace_dir / f"pending_evaluation_{task_date}.json"
        
        tasks = []
        for i, paper in enumerate(selected_papers, 1):
            short_title = self.generate_short_title(paper['title'])
            tasks.append({
                "priority": i,
                "arxiv_id": paper.get('arxiv_id'),
                "title": paper.get('title'),
                "short_title": short_title,
                "paper_dir": str(self.papers_dir / short_title),
                "relevance_score": paper.get('relevance_score', 0),
                "status": "pending"
            })
        
        with open(task_path, 'w', encoding='utf-8') as f:
            json.dump({"date": task_date, "tasks": tasks}, f, ensure_ascii=False, indent=2)
        
        print(f"?? 待评估任务清单已生成: {task_path}")
        return task_path, tasks
    
    def build_daily_summary_message(self, search_stats, selected_papers):
        """构建每日检索摘要消息体"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""📚 **每日论文检索报告** - {date_str}

🔍 **检索统计**:
- 批量搜索论文数: {search_stats['total_searched']}
- 去重后论文数: {search_stats['after_dedup']}
- 已评估跳过: {search_stats['skipped_evaluated']}
- 今日精选: {search_stats['selected_count']} 篇

🏆 **今日精选论文** (Top {len(selected_papers)}):
"""
        
        for i, paper in enumerate(selected_papers, 1):
            relevance = paper.get('relevance_score', 0)
            message += f"\n{i}. **{paper['title'][:60]}...**\n"
            message += f"   arXiv: {paper.get('arxiv_id', 'N/A')} | 相关性: {relevance}分\n"
        
        message += f"""
📎 **后续操作**:
以上论文已加入待评估队列，将进行深度总结和四维评分。

---
*Surrogate-Modeling Expert Agent*
*检索时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""

    def send_daily_summary(self, search_stats, selected_papers, dry_run=False):
        """发送每日检索摘要如流消息"""
        message = self.build_daily_summary_message(search_stats, selected_papers)

        if dry_run:
            print("\n📨 [DRY-RUN] 如流消息内容:")
            print("-" * 50)
            print(message)
            print("-" * 50)
            return True
        
        try:
            from send_message import GroupMessageSender
            sender = GroupMessageSender()
            
            for user in self.recipients:
                result = sender.send_app_message(
                    to_users=user,
                    msg_type="text",
                    content=message
                )
                
                if result.get('code') == 'ok':
                    print(f"✅ 如流消息发送成功: {user}")
                else:
                    print(f"⚠️  如流消息发送失败 {user}: {result}")
            
            return True
        except ImportError:
            print("⚠️  如流消息模块未安装，跳过发送")
            print("\n📨 消息内容预览:")
            print(message[:500] + "...")
            return False
        except Exception as e:
            print(f"❌ 发送如流消息异常: {e}")
            return False

    def send_daily_email(self, search_stats, selected_papers, dry_run=False):
        """通过 Gmail SMTP 发送每日报告邮件"""
        subject = f"[PaperClaw] 每日论文检索报告 - {datetime.now().strftime('%Y-%m-%d')}"
        body = self.build_daily_summary_message(search_stats, selected_papers)

        if dry_run:
            print("\n📧 [DRY-RUN] 邮件主题:")
            print(subject)
            print("\n📧 [DRY-RUN] 邮件正文预览:")
            print(body[:500] + "...")
            return True

        if not all([self.email_sender, self.email_password, self.email_recipients]):
            print("⚠️  邮件配置不完整，跳过邮件发送")
            print("   需要环境变量: EMAIL_SENDER, EMAIL_APP_PASSWORD, EMAIL_RECIPIENT")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_sender
            msg["To"] = ', '.join(self.email_recipients)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, self.email_recipients, msg.as_string())

            print(f"✅ 每日报告邮件发送成功: {', '.join(self.email_recipients)}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("❌ 邮件认证失败，请检查 EMAIL_APP_PASSWORD（Gmail 应用专用密码）")
            return False
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def run(self, top_n=3, skip_download=False, dry_run=False):
        """执行每日检索流程"""
        print("=" * 60)
        print(f"📚 每日论文检索任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 加载已评估论文（用于去重）
        print("\n?? 步骤 1/6: 加载已评估论文...")
        evaluated_ids, evaluated_titles = self.load_evaluated_papers()
        
        # 2. 批量搜索
        print("\n🔍 步骤 2/6: 批量搜索 arXiv...")
        all_papers = batch_search(max_results_per_query=30, delay=3)
        
        # 3. 搜索脚本内部去重
        print("\n🔄 步骤 3/6: 搜索结果去重...")
        unique_papers, search_dups, excluded = deduplicate_papers(all_papers)
        print(f"   搜索去重后: {len(unique_papers)} 篇")
        
        # 4. 与已评估数据库去重
        print("\n🔄 步骤 4/6: 与已评估数据库去重...")
        new_papers, skipped_evaluated = self.filter_against_evaluated(
            unique_papers, evaluated_ids, evaluated_titles
        )
        print(f"   跳过已评估: {len(skipped_evaluated)} 篇")
        print(f"   新论文数量: {len(new_papers)} 篇")
        
        if not new_papers:
            print("\n⚠️  今日无新论文，所有搜索结果均已评估")
            return
        
        # 5. 相关性排序，选 Top N
        print(f"\n🏆 步骤 5/6: 相关性排序，选择 Top {top_n}...")
        for paper in new_papers:
            paper['relevance_score'] = score_paper_relevance(paper)
        
        new_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        selected_papers = new_papers[:top_n]
        
        for i, paper in enumerate(selected_papers, 1):
            print(f"   {i}. [{paper['relevance_score']}分] {paper['title'][:55]}...")
        
        # 6. 下载 PDF 并创建元数据
        if not skip_download and not dry_run:
            print(f"\n📥 步骤 6/6: 下载 PDF 并创建元数据...")
            for paper in selected_papers:
                short_title = self.generate_short_title(paper['title'])
                paper_dir = self.papers_dir / short_title
                
                pdf_path = self.download_pdf(paper, paper_dir)
                self.create_paper_metadata(paper, pdf_path)
        else:
            print(f"\n⏭️  步骤 6/6: 跳过 PDF 下载 (skip_download={skip_download}, dry_run={dry_run})")
        
        # 保存搜索日志
        search_stats = {
            'total_searched': len(all_papers),
            'after_dedup': len(unique_papers),
            'skipped_evaluated': len(skipped_evaluated),
            'selected_count': len(selected_papers)
        }
        self.save_search_log(unique_papers, selected_papers, skipped_evaluated)
        
        # 生成待评估任务清单
        task_path, tasks = self.generate_evaluation_task(selected_papers)
        
        # 保存到 Obsidian
        print("\n📓 同步到 Obsidian...")
        self.save_to_obsidian(search_stats, selected_papers)

        # 邮件在 paper-review 完成后由 send_daily_evaluation_email.py 统一发送
        print("\n📋 检索完成，待评估清单已生成。")
        print("   💡 请执行 paper-review 后运行 send_daily_evaluation_email.py 发送深度评估邮件")
        
        print("\n" + "=" * 60)
        print("✅ 每日论文检索任务完成！")
        print("=" * 60)
        print(f"\n📋 后续步骤:")
        print(f"   1. 查看待评估清单: {task_path}")
        print(f"   2. 对每篇论文执行 paper-review 技能进行评估")
        print(f"   3. 评估完成后使用 update_registry.py 更新数据库")
        
        return selected_papers


def main():
    parser = argparse.ArgumentParser(description='每日论文检索与筛选')
    parser.add_argument('--top', type=int, default=3, help='精选论文数量（默认3）')
    parser.add_argument('--skip-download', action='store_true', help='跳过PDF下载')
    parser.add_argument('--dry-run', action='store_true', help='仅搜索，不下载不发送')
    parser.add_argument('--workspace', type=str, help='工作空间路径')
    parser.add_argument('--send-evaluation', action='store_true',
                        help='发送深度评估邮件（在 paper-review 完成后调用）')
    parser.add_argument('--date', type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help='报告日期，格式 YYYY-MM-DD（默认今天）')

    args = parser.parse_args()

    searcher = DailyPaperSearcher(workspace_path=args.workspace)

    if args.send_evaluation:
        searcher.send_evaluation_email(date_str=args.date, dry_run=args.dry_run)
    else:
        searcher.run(
            top_n=args.top,
            skip_download=args.skip_download,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()
