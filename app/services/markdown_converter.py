"""
Markdown转换服务
将HTML内容转换为Markdown格式
"""

import re
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class MarkdownConverterService:
    """Markdown转换服务"""
    
    def __init__(self):
        # 需要移除的标签
        self.remove_tags = [
            'script', 'style', 'nav', 'header', 'footer', 'aside', 
            'noscript', 'iframe', 'embed', 'object', 'applet',
            'form', 'input', 'button', 'select', 'textarea',
            'meta', 'link', 'title', 'head'
        ]
        
        # 需要移除的CSS类名模式
        self.remove_class_patterns = [
            r'.*nav.*', r'.*menu.*', r'.*sidebar.*', r'.*footer.*',
            r'.*header.*', r'.*ad.*', r'.*banner.*', r'.*popup.*',
            r'.*modal.*', r'.*cookie.*', r'.*social.*', r'.*share.*',
            r'.*comment.*', r'.*related.*', r'.*recommend.*'
        ]
        
        # 需要移除的ID模式
        self.remove_id_patterns = [
            r'.*nav.*', r'.*menu.*', r'.*sidebar.*', r'.*footer.*',
            r'.*header.*', r'.*ad.*', r'.*banner.*', r'.*popup.*',
            r'.*modal.*', r'.*cookie.*', r'.*social.*', r'.*share.*',
            r'.*comment.*', r'.*related.*', r'.*recommend.*'
        ]
    
    def html_to_markdown(self, html_content: str, base_url: str = "", 
                        include_images: bool = True, include_tables: bool = True,
                        clean_html: bool = True) -> str:
        """
        将HTML内容转换为Markdown格式
        
        Args:
            html_content: 原始HTML内容
            base_url: 基础URL，用于处理相对链接
            include_images: 是否包含图片
            include_tables: 是否包含表格
            clean_html: 是否清理HTML标签
            
        Returns:
            转换后的Markdown内容
        """
        if not html_content:
            return ""
        
        try:
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if clean_html:
                # 移除不需要的标签和元素
                self._remove_unwanted_tags(soup)
                self._remove_unwanted_elements(soup)
            
            # 提取主要内容区域
            main_content = self._extract_main_content(soup)
            if not main_content:
                main_content = soup.find('body') or soup
            
            # 转换为Markdown
            markdown_content = self._convert_to_markdown(main_content, base_url, include_images, include_tables)
            
            # 清理Markdown内容
            cleaned_markdown = self._clean_markdown(markdown_content)
            
            return cleaned_markdown
            
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {e}")
            return ""
    
    def _remove_unwanted_tags(self, soup: BeautifulSoup) -> None:
        """移除不需要的HTML标签"""
        for tag_name in self.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """移除不需要的元素（基于class和id）"""
        # 移除基于class的元素
        for pattern in self.remove_class_patterns:
            elements = soup.find_all(class_=re.compile(pattern, re.IGNORECASE))
            for element in elements:
                element.decompose()
        
        # 移除基于id的元素
        for pattern in self.remove_id_patterns:
            elements = soup.find_all(id=re.compile(pattern, re.IGNORECASE))
            for element in elements:
                element.decompose()
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """提取主要内容区域"""
        # 常见的主要内容选择器
        main_selectors = [
            'main', 'article', '.content', '.main-content', '.post-content',
            '.entry-content', '.article-content', '.page-content',
            '#content', '#main', '#article', '#post', '#entry'
        ]
        
        for selector in main_selectors:
            try:
                if selector.startswith('.'):
                    # class选择器
                    elements = soup.find_all(class_=selector[1:])
                elif selector.startswith('#'):
                    # id选择器
                    elements = soup.find_all(id=selector[1:])
                else:
                    # 标签选择器
                    elements = soup.find_all(selector)
                
                if elements:
                    # 选择最大的元素（通常是主要内容）
                    main_element = max(elements, key=lambda x: len(x.get_text()))
                    if len(main_element.get_text()) > 100:  # 确保有足够的内容
                        return main_element
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        return None
    
    def _convert_to_markdown(self, element: Tag, base_url: str = "", 
                           include_images: bool = True, include_tables: bool = True) -> str:
        """递归转换HTML元素为Markdown"""
        if not element:
            return ""
        
        markdown_parts = []
        
        for child in element.children:
            if isinstance(child, str):
                # 处理文本节点
                text = child.strip()
                if text:
                    markdown_parts.append(text)
            elif hasattr(child, 'name'):
                # 处理HTML标签
                tag_name = child.name
                tag_markdown = self._convert_tag_to_markdown(child, base_url, include_images, include_tables)
                if tag_markdown:
                    markdown_parts.append(tag_markdown)
        
        return '\n'.join(markdown_parts)
    
    def _convert_tag_to_markdown(self, tag: Tag, base_url: str = "", 
                               include_images: bool = True, include_tables: bool = True) -> str:
        """将HTML标签转换为Markdown"""
        tag_name = tag.name
        text = tag.get_text().strip()
        
        if not text and tag_name not in ['img', 'br', 'hr']:
            return ""
        
        # 标题
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            return f"{'#' * level} {text}\n"
        
        # 段落
        elif tag_name == 'p':
            return f"{text}\n"
        
        # 链接
        elif tag_name == 'a':
            href = tag.get('href', '')
            if href:
                # 处理相对URL
                if base_url and not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                    href = urljoin(base_url, href)
                return f"[{text}]({href})"
            return text
        
        # 图片
        elif tag_name == 'img' and include_images:
            src = tag.get('src', '')
            alt = tag.get('alt', '')
            if src:
                # 处理相对URL
                if base_url and not src.startswith(('http://', 'https://', 'data:')):
                    src = urljoin(base_url, src)
                return f"![{alt}]({src})"
            return ""
        
        # 列表
        elif tag_name in ['ul', 'ol']:
            items = []
            for li in tag.find_all('li', recursive=False):
                item_text = li.get_text().strip()
                if item_text:
                    if tag_name == 'ul':
                        items.append(f"- {item_text}")
                    else:
                        items.append(f"1. {item_text}")
            return '\n'.join(items) + '\n'
        
        # 列表项
        elif tag_name == 'li':
            return text
        
        # 表格
        elif tag_name == 'table' and include_tables:
            return self._convert_table_to_markdown(tag)
        
        # 代码
        elif tag_name in ['code', 'pre']:
            if tag_name == 'pre':
                return f"```\n{text}\n```\n"
            else:
                return f"`{text}`"
        
        # 强调
        elif tag_name in ['strong', 'b']:
            return f"**{text}**"
        
        elif tag_name in ['em', 'i']:
            return f"*{text}*"
        
        # 引用
        elif tag_name == 'blockquote':
            lines = text.split('\n')
            quoted_lines = [f"> {line}" for line in lines if line.strip()]
            return '\n'.join(quoted_lines) + '\n'
        
        # 水平线
        elif tag_name == 'hr':
            return "---\n"
        
        # 换行
        elif tag_name == 'br':
            return "\n"
        
        # 其他标签，递归处理子元素
        else:
            return self._convert_to_markdown(tag, base_url, include_images, include_tables)
    
    def _convert_table_to_markdown(self, table: Tag) -> str:
        """将HTML表格转换为Markdown表格"""
        try:
            rows = []
            
            # 处理表头
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    if headers:
                        rows.append('| ' + ' | '.join(headers) + ' |')
                        rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
            
            # 处理表体
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                if thead and tr in thead.find_all('tr'):
                    continue  # 跳过已经在表头处理过的行
                
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append('| ' + ' | '.join(cells) + ' |')
            
            return '\n'.join(rows) + '\n'
            
        except Exception as e:
            logger.debug(f"Error converting table to markdown: {e}")
            return table.get_text().strip() + '\n'
    
    def _clean_markdown(self, markdown: str) -> str:
        """清理Markdown内容"""
        if not markdown:
            return ""
        
        # 移除多余的空白行
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.rstrip()
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        # 移除开头和结尾的空行
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def extract_metadata(self, html_content: str) -> Dict[str, Any]:
        """提取页面元数据"""
        if not html_content:
            return {
                'title': '',
                'description': '',
                'headings': [],
                'images': [],
                'tables': []
            }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取描述
            description = self._extract_description(soup)
            
            # 提取标题结构
            headings = self._extract_headings(soup)
            
            # 提取图片信息
            images = self._extract_images(soup)
            
            # 提取表格信息
            tables = self._extract_tables(soup)
            
            return {
                'title': title,
                'description': description,
                'headings': headings,
                'images': images,
                'tables': tables
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                'title': '',
                'description': '',
                'headings': [],
                'images': [],
                'tables': []
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        # 尝试从title标签获取
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 尝试从h1标签获取
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取页面描述"""
        # 尝试从meta description获取
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # 尝试从第一个段落获取
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            if len(text) > 20:  # 确保有足够的内容
                return text[:200] + '...' if len(text) > 200 else text
        
        return ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取标题结构"""
        headings = []
        for i in range(1, 7):  # h1到h6
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': i,
                        'text': text
                    })
        return headings
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """提取图片信息"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                images.append({
                    'src': src,
                    'alt': alt
                })
        return images
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取表格信息"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    'rows': len(rows),
                    'columns': len(rows[0]) if rows else 0,
                    'data': rows
                })
        
        return tables
