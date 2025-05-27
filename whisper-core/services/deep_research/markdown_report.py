from datetime import datetime
from typing import List, Dict, Any

class MarkdownReport:
    """处理研究报告的 Markdown 文档生成"""
    def __init__(self, question: str):
        self.content = []
        self.search_results = []  # 存储所有搜索结果
        self.content.append(f"# 深度研究报告\n\n")
        self.content.append(f"## 研究问题\n{question}\n\n")
        self.content.append("## 研究过程\n\n")

    def add_planning_done(self):
        """添加规划完成标记"""
        self.content.append("\n### 规划阶段完成\n")

    def add_search_keywords(self, keywords: List[str]):
        """添加搜索关键词"""
        self.content.append(f"\n### 搜索关键词\n{', '.join(keywords)}\n")

    def add_search_result(self, result: Dict[str, Any]):
        """添加单个搜索结果到存储"""
        self.search_results.append(result)

    def add_search_results(self, results: List[Dict[str, Any]]):
        """添加搜索结果到文档"""
        self.content.append(f"\n### 搜索结果\n")
        for idx, result in enumerate(results, 1):
            self.content.append(f"\n#### 结果 {idx}\n")
            self.content.append(f"**查询词**: {result['query']}\n")
            self.content.append(f"**摘要**: {result['summary_content']}\n")
            self.content.append("**参考来源**:\n")
            for ref in result['search_references']:
                self.content.append(f"- [{ref['title']}]({ref['url']})")
                self.content.append(f"  - 来源: {ref['site']}")
                self.content.append(f"  - 内容: {ref['content'][:200]}...\n")

    def add_content(self, content: str):
        """添加普通内容"""
        self.content.append(content)

    def add_research_done(self):
        """添加研究完成标记"""
        self.content.append("\n### 研究完成\n")
        # 在研究完成时添加所有搜索结果
        if self.search_results:
            self.add_search_results(self.search_results)

    def save(self) -> str:
        """保存文档并返回文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_report_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("".join(self.content))
        return filename 