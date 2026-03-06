#!/usr/bin/env python3
"""
每日深度评估邮件发送脚本
在 paper-review 完成后调用，发送包含完整摘要和四维评分的评估报告。

使用方法:
  python send_daily_evaluation_email.py --workspace ~/.paperclaw/workspace
  python send_daily_evaluation_email.py --workspace ~/.paperclaw/workspace --date 2026-03-05
  python send_daily_evaluation_email.py --workspace ~/.paperclaw/workspace --dry-run
"""
import os
import sys
import json
import smtplib
import argparse
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


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


class DailyEvaluationMailer:
    """每日深度评估邮件发送器"""

    def __init__(self, workspace_path=None):
        if workspace_path:
            self.workspace_dir = Path(workspace_path)
        else:
            self.workspace_dir = Path.home() / ".paperclaw" / "workspace"

        self.papers_dir = self.workspace_dir / "papers"

        self.email_sender = os.environ.get("EMAIL_SENDER", "")
        self.email_password = os.environ.get("EMAIL_APP_PASSWORD", "")
        recipients_str = os.environ.get("EMAIL_RECIPIENT", "")
        self.email_recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

        obsidian_vault = os.environ.get("OBSIDIAN_VAULT", "")
        self.obsidian_daily_dir = Path(obsidian_vault) / "PaperClaw" / "daily" if obsidian_vault else None

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
        """读取文件内容，不存在返回 None"""
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                pass
        return None

    def read_metadata(self, paper_dir):
        """读取 metadata.json"""
        meta_path = Path(paper_dir) / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def build_evaluation_content(self, papers_data, date_str, truncate_summary=False):
        """构建评估报告内容（Markdown 格式）。truncate_summary=True 用于邮件发送时截断。"""
        evaluated = [p for p in papers_data if p["summary"] or p["scores"]]
        pending = [p for p in papers_data if not p["summary"] and not p["scores"]]

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

        if pending:
            sections.append(f"\n⚠️ **以下 {len(pending)} 篇未完成评估**:")
            for p in pending:
                sections.append(f"- {p.get('title', 'Unknown')} ({p.get('arxiv_id', '')})")

        sections.append("\n\n*PaperClaw · Humanoid Robot Control Research*")
        return "\n".join(sections)

    def build_email_body(self, papers_data, date_str):
        """构建邮件正文（摘要截断，避免过长）"""
        return self.build_evaluation_content(papers_data, date_str, truncate_summary=True)

    def save_to_obsidian(self, papers_data, date_str):
        """将深度评估报告追加到 Obsidian 日报文件"""
        if not self.obsidian_daily_dir:
            print("⚠️  未配置 OBSIDIAN_VAULT，跳过 Obsidian 同步")
            return None

        self.obsidian_daily_dir.mkdir(parents=True, exist_ok=True)
        obsidian_path = self.obsidian_daily_dir / f"{date_str}.md"

        # 完整内容（不截断 summary）
        content = self.build_evaluation_content(papers_data, date_str, truncate_summary=False)

        # 若日报文件已存在（由 daily_paper_search.py 创建），追加评估内容
        if obsidian_path.exists():
            with open(obsidian_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n## 📊 深度评估结果\n\n")
                f.write(content)
        else:
            with open(obsidian_path, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"✅ 深度评估已同步到 Obsidian: {obsidian_path}")
        return obsidian_path

    def send(self, date_str, dry_run=False):
        """主流程：读取今日评估结果并发送邮件"""
        print("=" * 60)
        print(f"📧 每日深度评估邮件 - {date_str}")
        print("=" * 60)

        # 1. 读取今日待评估论文
        tasks = self.load_today_papers(date_str)
        if not tasks:
            print("❌ 无今日论文数据，退出")
            return False

        print(f"✅ 今日论文 {len(tasks)} 篇")

        # 2. 读取每篇论文的评估结果
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

        # 3. 同步到 Obsidian（完整内容）
        print("\n📓 同步到 Obsidian...")
        self.save_to_obsidian(papers_data, date_str)

        # 4. 构建邮件内容（摘要截断）
        body = self.build_email_body(papers_data, date_str)
        subject = f"[PaperClaw] 每日深度评估报告 - {date_str}"

        if dry_run:
            print("\n📧 [DRY-RUN] 邮件主题:", subject)
            print("\n📧 [DRY-RUN] 邮件正文预览:")
            print(body[:800] + "...")
            return True

        # 5. 发送邮件
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


def main():
    parser = argparse.ArgumentParser(description="发送每日深度评估邮件（在 paper-review 完成后调用）")
    parser.add_argument("--workspace", type=str, help="工作空间路径")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="报告日期，格式 YYYY-MM-DD（默认今天）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不发送邮件")
    args = parser.parse_args()

    mailer = DailyEvaluationMailer(workspace_path=args.workspace)
    mailer.send(date_str=args.date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
