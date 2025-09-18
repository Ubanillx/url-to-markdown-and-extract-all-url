"""
文本内容提取服务
从HTML中提取有效的文字信息，过滤掉无用的标签和内容
"""

import re
import logging
from typing import Optional, List
from bs4 import BeautifulSoup, Comment
from bs4.element import NavigableString

logger = logging.getLogger(__name__)


class TextExtractorService:
    """文本内容提取服务"""
    
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
    
    def extract_text_content(self, html_content: str) -> str:
        """
        从HTML内容中提取有效的文字信息
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            提取的文本内容
        """
        if not html_content:
            return ""
        
        try:
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除不需要的标签
            self._remove_unwanted_tags(soup)
            
            # 移除不需要的元素
            self._remove_unwanted_elements(soup)
            
            # 提取文本内容
            text_content = self._extract_clean_text(soup)
            
            # 清理文本
            cleaned_text = self._clean_text(text_content)
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
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
        
        # 移除注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """提取清洁的文本内容"""
        # 优先提取主要内容区域
        main_content = self._extract_main_content(soup)
        if main_content:
            return main_content
        
        # 如果没有找到主要内容区域，提取body内容
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        # 最后提取整个文档
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
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
                    text = main_element.get_text(separator=' ', strip=True)
                    if len(text) > 100:  # 确保有足够的内容
                        return text
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除多余的换行符
        text = re.sub(r'\n+', '\n', text)
        
        # 移除行首行尾的空白
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        # 重新组合文本
        cleaned_text = '\n'.join(cleaned_lines)
        
        # 移除过短的行（可能是导航或装饰性文本）
        final_lines = []
        for line in cleaned_lines:
            if len(line) > 10:  # 只保留长度大于10的行
                final_lines.append(line)
        
        return '\n'.join(final_lines)
    
    def extract_structured_content(self, html_content: str) -> dict:
        """
        提取结构化的内容信息
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            包含标题、正文、链接等信息的字典
        """
        if not html_content:
            return {
                'title': '',
                'content': '',
                'headings': [],
                'links': [],
                'images': []
            }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取正文内容
            content = self.extract_text_content(html_content)
            
            # 提取标题结构
            headings = self._extract_headings(soup)
            
            # 提取链接
            links = self._extract_links(soup)
            
            # 提取图片
            images = self._extract_images(soup)
            
            return {
                'title': title,
                'content': content,
                'headings': headings,
                'links': links,
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Error extracting structured content: {e}")
            return {
                'title': '',
                'content': '',
                'headings': [],
                'links': [],
                'images': []
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
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[dict]:
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
    
    def _extract_links(self, soup: BeautifulSoup) -> List[dict]:
        """提取链接信息"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            if href and text:
                links.append({
                    'url': href,
                    'text': text
                })
        return links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[dict]:
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
