"""
基于Selenium的网页内容提取器
支持JavaScript渲染的网页内容提取
"""

import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import html2text

from app.schemas.url_extract import UrlExtractRequest, UrlExtractResponse

logger = logging.getLogger(__name__)


class SeleniumExtractorService:
    """基于Selenium的网页内容提取服务"""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # 不限制行宽
    
    def _setup_driver(self) -> webdriver.Chrome:
        """设置Chrome WebDriver"""
        chrome_options = Options()
        
        # 无头模式，适合Linux无GUI环境
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # 禁用图片加载以提高速度
        # 注意：不禁用JavaScript，因为需要支持动态渲染的网页
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 设置超时
        chrome_options.add_argument('--page-load-strategy=normal')
        
        try:
            # 自动下载和管理ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def _wait_for_page_load(self, timeout: int = 15) -> bool:
        """等待页面完全加载，包括动态内容"""
        try:
            # 等待页面基本加载完成
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 等待jQuery加载完成（如果存在）
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
                )
            except TimeoutException:
                pass
            
            # 等待网络请求完成
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("return window.performance.timing.loadEventEnd > 0")
                )
            except TimeoutException:
                pass
            
            # 额外等待动态内容渲染
            time.sleep(3)
            
            # 滚动页面以触发懒加载内容
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Error during scroll: {e}")
            
            return True
        except TimeoutException:
            logger.warning("Page load timeout, proceeding with current content")
            return False
    
    def _extract_links_from_page(self, base_url: str, base_domain: str, request: UrlExtractRequest) -> List[str]:
        """从页面中提取所有链接"""
        urls = []
        try:
            # 获取所有链接元素
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        # 处理相对URL
                        if href.startswith('/'):
                            absolute_url = urljoin(base_url, href)
                        else:
                            absolute_url = href
                        
                        parsed_url = urlparse(absolute_url)
                        if self._should_include_url(parsed_url, base_domain, request):
                            urls.append(absolute_url)
                except Exception as e:
                    logger.debug(f"Error extracting link: {e}")
                    continue
            
            # 去重
            urls = list(set(urls))
            return urls
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def _should_include_url(self, parsed_url, base_domain: str, request: UrlExtractRequest) -> bool:
        """判断是否应该包含该URL"""
        if not parsed_url.netloc:
            return False
        
        # 判断是内部链接还是外部链接
        is_internal = parsed_url.netloc == base_domain
        
        # 根据请求参数决定是否包含内部/外部链接
        if is_internal and not request.include_internal:
            return False
        if not is_internal and not request.include_external:
            return False
        
        # 排除不需要的文件类型
        excluded_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                             '.zip', '.rar', '.7z', '.jpg', '.jpeg', '.png', '.gif', 
                             '.css', '.js', '.ico', '.xml', '.json'}
        
        path = parsed_url.path.lower()
        if any(path.endswith(ext) for ext in excluded_extensions):
            return False
        
        return True
    
    def _extract_text_content(self) -> str:
        """提取页面的纯文本内容，包括动态渲染的内容和iframe内容"""
        try:
            # 等待内容加载
            time.sleep(2)
            
            # 首先检查是否有iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                logger.info(f"Found {len(iframes)} iframe(s), attempting to extract content from them")
                iframe_texts = []
                
                for i, iframe in enumerate(iframes):
                    try:
                        # 切换到iframe
                        self.driver.switch_to.frame(iframe)
                        
                        # 等待iframe内容加载
                        time.sleep(1)
                        
                        # 获取iframe内的文本内容
                        iframe_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if iframe_text.strip():
                            iframe_texts.append(iframe_text)
                            logger.info(f"Extracted {len(iframe_text)} characters from iframe {i+1}")
                        
                        # 切换回主页面
                        self.driver.switch_to.default_content()
                        
                    except Exception as e:
                        logger.debug(f"Failed to extract content from iframe {i+1}: {e}")
                        # 确保切换回主页面
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
                
                # 如果从iframe中提取到了内容，优先使用
                if iframe_texts:
                    combined_text = "\n\n".join(iframe_texts)
                    logger.info(f"Combined iframe content length: {len(combined_text)}")
                    return self._clean_text_content(combined_text)
            
            # 方法1：直接获取页面文本内容
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if len(page_text.strip()) > 100:
                    logger.info(f"Extracted text content directly, length: {len(page_text)}")
                    return self._clean_text_content(page_text)
            except Exception as e:
                logger.debug(f"Direct text extraction failed: {e}")
            
            # 方法2：使用BeautifulSoup解析
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 只移除脚本和样式标签，保留更多内容
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            
            # 尝试提取主要内容的容器
            main_content = None
            content_selectors = [
                'main', 'article', '.content', '.main-content', 
                '.post-content', '.entry-content', '.page-content',
                '#content', '#main', '.container', '.wrapper',
                'div[class*="list"]', 'div[class*="article"]',  # 针对列表页面
                '.list-container', '.article-list', '.news-list'
            ]
            
            for selector in content_selectors:
                try:
                    if selector.startswith('.'):
                        main_content = soup.select_one(selector)
                    elif selector.startswith('#'):
                        main_content = soup.find('div', id=selector[1:])
                    elif selector.startswith('div['):
                        main_content = soup.select_one(selector)
                    else:
                        main_content = soup.find(selector)
                    
                    if main_content and main_content.get_text(strip=True):
                        logger.info(f"Found main content using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # 如果找到主要内容容器，使用它
            if main_content and main_content.get_text(strip=True):
                text_content = main_content.get_text()
            else:
                # 尝试找到包含最多文本的div
                all_divs = soup.find_all('div')
                if all_divs:
                    # 找到文本内容最长的div
                    longest_div = max(all_divs, key=lambda x: len(x.get_text(strip=True)))
                    if len(longest_div.get_text(strip=True)) > 100:  # 至少100个字符
                        logger.info("Using longest div with text content")
                        text_content = longest_div.get_text()
                    else:
                        # 使用整个body
                        body = soup.find('body')
                        if body:
                            text_content = body.get_text()
                        else:
                            text_content = soup.get_text()
                else:
                    # 使用整个body
                    body = soup.find('body')
                    if body:
                        text_content = body.get_text()
                    else:
                        text_content = soup.get_text()
            
            # 清理文本内容
            result = self._clean_text_content(text_content)
            
            # 记录提取的内容长度
            logger.info(f"Extracted text content length: {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""
    
    def _clean_text_content(self, text: str) -> str:
        """清理文本内容，移除多余的空行和空白字符"""
        lines = text.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        return '\n'.join(cleaned_lines).strip()
    
    def extract_urls_and_text(self, request: UrlExtractRequest) -> UrlExtractResponse:
        """提取URL和文本内容"""
        start_time = time.time()
        
        try:
            # 设置WebDriver
            self.driver = self._setup_driver()
            
            # 访问页面
            url_str = str(request.url)
            logger.info(f"Loading page: {url_str}")
            self.driver.get(url_str)
            
            # 等待页面加载
            self._wait_for_page_load()
            
            # 解析基础URL信息
            parsed_url = urlparse(url_str)
            base_domain = parsed_url.netloc
            
            # 提取链接
            logger.info("Extracting links...")
            extracted_urls = self._extract_links_from_page(url_str, base_domain, request)
            
            # 提取文本内容
            logger.info("Extracting text content...")
            text_content = self._extract_text_content()
            
            processing_time = time.time() - start_time
            
            return UrlExtractResponse(
                success=True,
                source_url=str(request.url),
                extracted_urls=extracted_urls,
                total_links_found=len(extracted_urls),
                markdown_content=text_content,
                processing_time=processing_time,
                method="selenium"
            )
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            processing_time = time.time() - start_time
            
            return UrlExtractResponse(
                success=False,
                source_url=str(request.url),
                extracted_urls=[],
                total_links_found=0,
                markdown_content="",
                processing_time=processing_time,
                method="selenium",
                error_message=str(e)
            )
        
        finally:
            # 清理资源
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"Error closing driver: {e}")
                finally:
                    self.driver = None
    
    def __del__(self):
        """析构函数，确保资源清理"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
