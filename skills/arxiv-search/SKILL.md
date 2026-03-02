# arXiv Paper Search Skill

## 功能描述
从 arXiv 检索学术论文，支持关键词搜索、批量下载和自动筛选。

## 使用方法

### 1. 基础搜索
```bash
# 使用 arXiv API 搜索论文
python3 << 'EOF'
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def search_arxiv(query, max_results=30):
    """搜索 arXiv 论文"""
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{urllib.parse.quote(query)}"
    url = base_url + search_query + f"&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    response = urllib.request.urlopen(url)
    xml_data = response.read().decode('utf-8')
    
    root = ET.fromstring(xml_data)
    papers = []
    
    # 定义 arXiv namespace
    ns = {'arxiv': 'http://arxiv.org/schemas/atom'}
    
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        paper = {
            'id': entry.find('{http://www.w3.org/2005/Atom}id').text,
            'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
            'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
            'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
            'updated': entry.find('{http://www.w3.org/2005/Atom}updated').text,
            'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                       for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
            'categories': [cat.get('term') 
                          for cat in entry.findall('{http://www.w3.org/2005/Atom}category')],
            'pdf_url': None
        }
        
        # 获取 PDF 链接
        for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
            if link.get('title') == 'pdf':
                paper['pdf_url'] = link.get('href')
                break
        
        papers.append(paper)
    
    return papers

# 示例搜索
papers = search_arxiv("neural operator PDE", max_results=5)
print(json.dumps(papers, indent=2, ensure_ascii=False))
EOF
```

### 2. 批量关键词搜索（含去重机制）
```bash
# 多关键词批量搜索，自动去重
python3 << 'EOF'
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import re
from datetime import datetime

# 核心关键词：聚焦3D几何代理模型和PDE求解
ADVANCED_QUERIES = [
    "ti:geometry AND (ti:neural OR ti:operator OR ti:pde)",
    "ti:mesh AND (ti:neural OR ti:deep OR ti:learning)",
    "(ti:cfd OR ti:fluid) AND (ti:surrogate OR ti:neural OR ti:deep)",
    "ti:3d AND (ti:pde OR ti:physics OR ti:solver)",
    "(ti:fno OR ti:deeponet OR ti:\"neural operator\") AND (ti:geometry OR ti:mesh OR ti:domain)",
    "(ti:pressure OR ti:stress OR ti:flow) AND (ti:neural OR ti:deep OR ti:surrogate)",
    "(ti:aerodynamic OR ti:structural) AND (ti:surrogate OR ti:neural)"
]

# 排除关键词：避免不相关领域
EXCLUDE_KEYWORDS = [
    "epidemic", "epidemiology", "disease modeling",
    "population dynamics", "social network",
    "finance", "economics",
    "NLP", "language model", "text"
]

def normalize_title(title):
    """标准化标题用于去重"""
    title = title.lower()
    # 保留版本标识符（++、-2、-3等），只移除其他标点
    version_markers = re.findall(r'[\+\-]+\d*', title)
    title = re.sub(r'[^\w\s\+\-]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def extract_arxiv_id(paper_id):
    """从 arXiv URL 提取 ID"""
    match = re.search(r'(\d{4}\.\d{4,5})', paper_id)
    if match:
        return match.group(1)
    return paper_id

def is_duplicate(paper, seen_ids, seen_titles, seen_normalized):
    """检查论文是否重复"""
    arxiv_id = extract_arxiv_id(paper['id'])
    normalized_title = normalize_title(paper['title'])
    
    if arxiv_id in seen_ids:
        return True, f"重复ID: {arxiv_id}"
    
    if paper['title'] in seen_titles:
        return True, f"重复标题: {paper['title'][:50]}..."
    
    if normalized_title in seen_normalized:
        return True, f"相似标题: {paper['title'][:50]}..."
    
    return False, None

def search_arxiv(query, max_results=30):
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{urllib.parse.quote(query)}"
    url = base_url + search_query + f"&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    try:
        response = urllib.request.urlopen(url, timeout=30)
        xml_data = response.read().decode('utf-8')
        root = ET.fromstring(xml_data)
        
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper = {
                'id': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()[:500],
                'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
                'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                           for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
            }
            
            for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                if link.get('title') == 'pdf':
                    paper['pdf_url'] = link.get('href')
                    break
            
            papers.append(paper)
        
        return papers
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        return []

def deduplicate_papers(papers):
    """去重并记录去重信息"""
    seen_ids = set()
    seen_titles = set()
    seen_normalized = set()
    
    unique_papers = []
    duplicates = []
    
    for paper in papers:
        is_dup, reason = is_duplicate(paper, seen_ids, seen_titles, seen_normalized)
        
        if is_dup:
            duplicates.append({
                'title': paper['title'],
                'id': paper['id'],
                'reason': reason
            })
        else:
            unique_papers.append(paper)
            seen_ids.add(extract_arxiv_id(paper['id']))
            seen_titles.add(paper['title'])
            seen_normalized.add(normalize_title(paper['title']))
    
    return unique_papers, duplicates

# 批量搜索
all_papers = []
for keyword in ADVANCED_QUERIES:
    print(f"Searching: {keyword}")
    papers = search_arxiv(keyword, max_results=30)
    all_papers.extend(papers)
    time.sleep(3)  # 避免请求过快

print(f"\nTotal papers collected: {len(all_papers)}")

# 去重
unique_papers, duplicates = deduplicate_papers(all_papers)

print(f"Unique papers after deduplication: {len(unique_papers)}")
print(f"Duplicates removed: {len(duplicates)}")

if duplicates:
    print("\n=== Duplicates Removed ===")
    for dup in duplicates[:10]:
        print(f"- {dup['reason']}")
        print(f"  Title: {dup['title'][:60]}...")

print(f"\n=== Sample Unique Papers ===")
print(json.dumps(unique_papers[:5], indent=2, ensure_ascii=False))
EOF
```

### 3. 下载论文 PDF
```bash
# 下载单篇论文
python3 << 'EOF'
import urllib.request
import os
import re

def download_paper(pdf_url, title, save_dir):
    """下载论文 PDF"""
    # 清理标题作为文件名
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = re.sub(r'[-\s]+', '_', safe_title)[:100]
    
    os.makedirs(save_dir, exist_ok=True)
    pdf_path = os.path.join(save_dir, f"{safe_title}.pdf")
    
    try:
        urllib.request.urlretrieve(pdf_url, pdf_path)
        print(f"Downloaded: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Error downloading {title}: {e}")
        return None
EOF
```

### 4. 智能筛选论文
```bash
# 基于标题和摘要筛选高质量论文
python3 << 'EOF'
import json
import re

def score_paper_relevance(paper, keywords):
    """评估论文相关性分数"""
    title = paper['title'].lower()
    summary = paper['summary'].lower()
    
    score = 0
    
    # 核心关键词（高权重）
    geometry_keywords = ['3d geometry', '3d mesh', 'unstructured mesh', 'geometry-aware']
    for kw in geometry_keywords:
        if kw in title: score += 15
        if kw in summary: score += 5
    
    operator_keywords = ['neural operator', 'deep operator', 'operator learning']
    for kw in operator_keywords:
        if kw in title: score += 12
        if kw in summary: score += 4
    
    pde_keywords = ['pde solver', 'neural pde', 'pde surrogate', 'physics-informed']
    for kw in pde_keywords:
        if kw in title: score += 10
        if kw in summary: score += 3
    
    # 应用场景关键词（中高权重）
    application_keywords = ['cfd', 'fluid dynamics', 'aerodynamics', 'pressure field']
    for kw in application_keywords:
        if kw in title: score += 8
        if kw in summary: score += 3
    
    # 技术关键词（中权重）
    tech_keywords = ['transformer', 'graph neural network', 'gnn', 'pointnet']
    for kw in tech_keywords:
        if kw in title: score += 5
        if kw in summary: score += 2
    
    # 负面关键词（扣分）
    exclude_keywords = ['epidemic', 'epidemiology', 'disease', 'population dynamics',
                        'social network', 'finance', 'economics', 'nlp', 'language model']
    for kw in exclude_keywords:
        if kw in title: score -= 20
        if kw in summary: score -= 5
    
    # 加分项
    if any(word in summary for word in ['experiment', 'benchmark', 'dataset', 'validation']):
        score += 5
    
    if any(word in summary for word in ['code', 'github', 'implementation', 'open source']):
        score += 3
    
    return max(score, 0)  # 确保分数非负

def select_top_papers(papers, top_n=3):
    """选择最相关的论文"""
    scored = [(paper, score_paper_relevance(paper, [])) for paper in papers]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [paper for paper, score in scored[:top_n]]
EOF
```

## 注意事项
1. arXiv API 有请求频率限制，批量搜索时需要添加延迟（建议 3 秒）
2. 论文标题可能包含特殊字符，需要清理后才能作为文件名
3. 某些论文可能没有 PDF 链接，需要检查 `pdf_url` 是否存在
4. 建议保存搜索日志，方便追踪和去重
