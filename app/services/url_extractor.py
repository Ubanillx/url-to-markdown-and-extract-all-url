import re
import time
from typing import List, Set, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import html2text
from app.schemas.url_extract import UrlExtractRequest, UrlExtractResponse


class UrlExtractorService:
    """URL提取和Markdown转换服务"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # 不限制行宽
        
    def extract_urls_and_markdown(self, request: UrlExtractRequest) -> UrlExtractResponse:
        """提取URL并转换为Markdown"""
        start_time = time.time()
        
        try:
            # 获取网页内容
            response = self.session.get(str(request.url), timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取URLs
            extracted_urls = self._extract_urls(soup, request)
            
            # 转换为Markdown
            markdown_content = self._convert_to_markdown(soup, response.text)
            
            processing_time = time.time() - start_time
            
            return UrlExtractResponse(
                source_url=str(request.url),
                extracted_urls=extracted_urls,
                markdown_content=markdown_content,
                total_links_found=len(extracted_urls),
                processing_time=processing_time,
                success=True,
                method="requests"
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return UrlExtractResponse(
                source_url=str(request.url),
                extracted_urls=[],
                markdown_content="",
                total_links_found=0,
                processing_time=processing_time,
                success=False,
                error_message=str(e),
                method="requests"
            )
    
    def _extract_urls(self, soup: BeautifulSoup, request: UrlExtractRequest) -> List[str]:
        """提取网页中的所有URL"""
        base_url = str(request.url)
        base_domain = urlparse(base_url).netloc
        
        urls_set: Set[str] = set()
        
        # 方法1: 通过a标签提取
        a_tag_urls = self._extract_from_a_tags(soup, base_url, base_domain, request)
        urls_set.update(a_tag_urls)
        
        # 方法2: 通过正则表达式提取
        regex_urls = self._extract_from_regex(soup, base_url, base_domain, request)
        urls_set.update(regex_urls)
        
        # 转换为列表并去重
        urls_list = list(urls_set)
        
        # 应用最大链接数限制
        if request.max_links and len(urls_list) > request.max_links:
            urls_list = urls_list[:request.max_links]
            
        return urls_list
    
    def _extract_from_a_tags(self, soup: BeautifulSoup, base_url: str, base_domain: str, request: UrlExtractRequest) -> List[str]:
        """通过a标签提取URL"""
        urls = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if not href or href.startswith('#'):
                continue
                
            # 转换为绝对URL
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            
            # 过滤条件
            if self._should_include_url(parsed_url, base_domain, request):
                urls.append(absolute_url)
                
        return urls
    
    def _extract_from_regex(self, soup: BeautifulSoup, base_url: str, base_domain: str, request: UrlExtractRequest) -> List[str]:
        """通过正则表达式提取URL"""
        urls = []
        
        # 获取页面文本内容
        page_text = soup.get_text()
        
        # URL正则表达式模式
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # 标准HTTP/HTTPS URL
            r'www\.[^\s<>"{}|\\^`\[\]]+',     # www开头的URL
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                # 清理URL
                clean_url = match.rstrip('.,;!?)')
                
                # 如果是www开头的，添加https://
                if clean_url.startswith('www.'):
                    clean_url = 'https://' + clean_url
                
                try:
                    parsed_url = urlparse(clean_url)
                    if self._should_include_url(parsed_url, base_domain, request):
                        urls.append(clean_url)
                except:
                    continue
                    
        return urls
    
    def _should_include_url(self, parsed_url, base_domain: str, request: UrlExtractRequest) -> bool:
        """判断是否应该包含该URL"""
        # 检查协议
        if parsed_url.scheme not in ['http', 'https']:
            return False
            
        # 检查域名
        url_domain = parsed_url.netloc
        
        # 内部链接判断
        is_internal = url_domain == base_domain or url_domain.endswith('.' + base_domain)
        
        # 根据配置决定是否包含
        if is_internal and not request.include_internal:
            return False
        if not is_internal and not request.include_external:
            return False
            
        return True
    
    def _convert_to_markdown(self, soup: BeautifulSoup, html_content: str) -> str:
        """将HTML转换为Markdown"""
        # 清理HTML
        self._clean_html(soup)
        
        # 使用html2text转换
        markdown = self.h2t.handle(str(soup))
        
        # 清理多余的空白行
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        return markdown.strip()
    
    def _clean_html(self, soup: BeautifulSoup):
        """清理HTML内容"""
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # 移除注释
        from bs4 import Comment
        comments = soup.findAll(text=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
