#!/usr/bin/env python3
"""
周报生成与邮件发送脚本 v3.0
功能：
1. 从 evaluated_papers.json 读取基础信息和最终评分
2. 从 papers/{short_title}/scores.md 读取四维评分详情
3. 从 papers/{short_title}/summary.md 读取完整总结
4. 从 papers/{short_title}/metadata.json 读取关键词等元信息
5. 按综合评分排序，筛选 Top 3 精选论文
6. 生成 Markdown 周报并保存到本地
7. 通过邮件发送周报

配置环境变量（~/.bashrc 或 .env）：
    EMAIL_SENDER=your_gmail@gmail.com
    EMAIL_APP_PASSWORD=your_app_password   # Gmail 应用专用密码
    EMAIL_RECIPIENT=your_email@example.com # 收件人邮箱

Gmail App Password 获取方式：
    1. 访问 https://myaccount.google.com/security
    2. 开启两步验证
    3. 搜索 "App passwords" 生成专用密码（16位）
"""
import os
import sys
import json
import smtplib
from datetime import datetime, timedelta
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


class WeeklyReportGenerator:
    """周报生成器 v3.0"""

    def __init__(self):
        self.workspace_dir = Path(
            os.environ.get(
                "PAPERCLAW_WORKSPACE",
                Path.home() / ".paperclaw" / "workspace"
            )
        )
        self.papers_file = self.workspace_dir / "papers" / "evaluated_papers.json"
        self.reports_dir = self.workspace_dir / "weekly_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Obsidian 配置
        obsidian_vault = os.environ.get("OBSIDIAN_VAULT", "")
        self.obsidian_weekly_dir = Path(obsidian_vault) / "PaperClaw" / "weekly" if obsidian_vault else None

        # 邮件配置（从环境变量读取，支持逗号分隔多收件人）
        self.email_sender = os.environ.get("EMAIL_SENDER", "")
        self.email_password = os.environ.get("EMAIL_APP_PASSWORD", "")
        recipients_str = os.environ.get("EMAIL_RECIPIENT", "")
        self.email_recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

    def load_evaluated_papers(self):
        """加载已评估论文"""
        if not self.papers_file.exists():
            print(f"❌ 论文数据文件不存在: {self.papers_file}")
            return []

        with open(self.papers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        papers = data.get('papers', data.get('evaluated_papers', []))
        print(f"✅ 加载 {len(papers)} 篇论文")
        return papers

    def filter_week_papers(self, papers, days=7):
        """筛选最近N天的论文"""
        week_start = datetime.now() - timedelta(days=days)
        week_papers = []
        for paper in papers:
            try:
                eval_date_str = paper.get('evaluated_date', '')
                if not eval_date_str:
                    continue
                eval_date = datetime.fromisoformat(eval_date_str)
                if eval_date >= week_start:
                    week_papers.append(paper)
            except (ValueError, TypeError) as e:
                print(f"⚠️  日期解析失败: {paper.get('short_title', 'Unknown')} - {e}")
        return week_papers

    def sort_and_select_top(self, papers, top_n=3):
        """按综合评分排序并选择Top N"""
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('scores', {}).get('final_score', 0),
            reverse=True
        )
        return sorted_papers[:top_n]

    def read_summary_file(self, short_title):
        """读取论文的完整 summary.md 内容"""
        summary_file = self.workspace_dir / "papers" / short_title / "summary.md"
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"⚠️  读取 summary.md 失败 {short_title}: {e}")
        return None

    def read_scores_file(self, short_title):
        """读取论文的 scores.md 内容（四维评分详情）"""
        scores_file = self.workspace_dir / "papers" / short_title / "scores.md"
        if scores_file.exists():
            try:
                with open(scores_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"⚠️  读取 scores.md 失败 {short_title}: {e}")
        return None

    def read_metadata_file(self, short_title):
        """读取论文的 metadata.json 内容"""
        metadata_file = self.workspace_dir / "papers" / short_title / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  读取 metadata.json 失败 {short_title}: {e}")
        return None

    def generate_report_markdown(self, papers, all_week_papers, report_date):
        """生成Markdown格式的周报"""
        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        paper_list = []
        for i, paper in enumerate(papers, 1):
            short_title = paper.get('short_title', '')
            scores_content = self.read_scores_file(short_title)
            metadata = self.read_metadata_file(short_title)
            keywords = metadata.get('keywords', []) if metadata else paper.get('keywords', [])
            final_score = paper.get('scores', {}).get('final_score', 0)

            paper_entry = f"""### {i}. {paper.get('title', 'Unknown')}

**综合评分**: {final_score:.2f}/10

**四维评分详情**:
{scores_content if scores_content else '*评分详情暂缺*'}

**关键词**: {', '.join(keywords)}

**arXiv链接**: https://arxiv.org/abs/{paper.get('arxiv_id', '')}

---"""
            paper_list.append(paper_entry)

        table_rows = []
        for paper in all_week_papers[:5]:
            short_title = paper.get('short_title', '')
            title = paper.get('title', 'Unknown')
            if len(title) > 30:
                title = title[:30] + "..."
            final_score = paper.get('scores', {}).get('final_score', 0)

            metadata = self.read_metadata_file(short_title)
            if metadata and 'scores' in metadata:
                s = metadata['scores']
                eng = str(s.get('engineering_value', 'N/A'))
                arch = str(s.get('architecture_innovation', 'N/A'))
                theo = str(s.get('theoretical_contribution', 'N/A'))
                rel = str(s.get('result_reliability', 'N/A'))
                imp = str(s.get('impact', 'N/A'))
            else:
                eng = arch = theo = rel = imp = "N/A"

            table_rows.append(
                f"| {title} | {eng} | {arch} | {theo} | {rel} | {imp} | {final_score:.2f} |"
            )

        report = f"""# 🤖 人形机器人全身控制与感知控制研究周报

**报告周期**: {week_start} - {report_date}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**报告人**: Surrogate-Modeling Expert Agent

---

## 📌 本周概览

- **评估论文总数**: {len(all_week_papers)}
- **精选推荐论文**: Top {len(papers)}

---

## 🌟 本周精选论文 Top 3

{chr(10).join(paper_list)}

## 📊 四维评分分布（Top 5）

| 论文 | 控制性能 | 架构创新 | 理论贡献 | 可靠性 | 影响力 | 综合评分 |
|------|---------|---------|---------|--------|--------|---------|
{chr(10).join(table_rows)}

---

## 💡 研究建议

### 值得跟进的方向
1. 全身控制与操作（Loco-manipulation）的统一框架
2. 基于视觉感知的闭环运动控制
3. Sim-to-Real 迁移与领域自适应技术

### 工具与资源
- 推荐关注 arXiv cs.RO 和 cs.LG 分类
- 开源代码库持续跟踪（IsaacGym / MuJoCo / Unitree）

---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*Surrogate-Modeling Expert Agent*"""

        return report

    def send_email(self, subject, body, report_path=None):
        """通过 Gmail SMTP 发送邮件"""
        if not all([self.email_sender, self.email_password, self.email_recipients]):
            print("⚠️  邮件配置不完整，请设置环境变量:")
            print("   EMAIL_SENDER, EMAIL_APP_PASSWORD, EMAIL_RECIPIENT")
            print("\n📄 周报内容已保存到本地，跳过邮件发送")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = ', '.join(self.email_recipients)

            # 纯文本正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, self.email_recipients, msg.as_string())

            print(f"✅ 邮件发送成功: {', '.join(self.email_recipients)}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("❌ Gmail 认证失败，请检查 EMAIL_APP_PASSWORD 是否为应用专用密码")
            print("   获取方式: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

    def generate_and_send(self):
        """生成周报并发送"""
        print("=" * 60)
        print("📊 开始生成周报 v3.0...")
        print("=" * 60)

        # 1. 加载论文数据
        print("\n📖 加载已评估论文...")
        papers = self.load_evaluated_papers()
        if not papers:
            print("❌ 没有找到已评估的论文")
            return

        # 2. 筛选本周论文
        print("\n📅 筛选本周论文...")
        week_papers = self.filter_week_papers(papers, days=7)
        print(f"✅ 本周评估 {len(week_papers)} 篇论文")

        if not week_papers:
            print("⚠️  本周没有评估新论文，使用全部历史数据")
            week_papers = papers

        # 3. 排序并选择Top 3精选论文
        print("\n🏆 筛选 Top 3 精选论文...")
        top_papers = self.sort_and_select_top(week_papers, top_n=3)
        for i, paper in enumerate(top_papers, 1):
            score = paper.get('scores', {}).get('final_score', 0)
            print(f"   {i}. {paper.get('title', 'Unknown')[:50]}... - {score:.2f}分")

        # 4. 生成周报Markdown
        print("\n📝 生成周报内容...")
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_content = self.generate_report_markdown(top_papers, week_papers, report_date)

        # 保存本地副本
        report_path = self.reports_dir / f"{report_date}_weekly_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"✅ 周报已保存: {report_path}")

        # 保存到 Obsidian
        if self.obsidian_weekly_dir:
            self.obsidian_weekly_dir.mkdir(parents=True, exist_ok=True)
            obsidian_path = self.obsidian_weekly_dir / f"{report_date}_weekly_report.md"
            with open(obsidian_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ 周报已同步到 Obsidian: {obsidian_path}")
        else:
            print("⚠️  未配置 OBSIDIAN_VAULT，跳过 Obsidian 同步")

        # 5. 发送邮件
        print("\n📧 发送邮件...")
        subject = f"🤖 人形机器人控制研究周报 - {report_date}"
        self.send_email(subject, report_content, report_path)

        print("\n" + "=" * 60)
        print("✅ 周报生成完成！")
        print("=" * 60)

        return report_path


def main():
    generator = WeeklyReportGenerator()
    generator.generate_and_send()


if __name__ == "__main__":
    main()
