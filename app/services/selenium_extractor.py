"""
基于Selenium的网页内容提取器
支持JavaScript渲染的网页内容提取
"""

import time
import logging
import socket
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
from bs4 import BeautifulSoup

from app.schemas.url_extract import UrlExtractRequest, UrlExtractResponse
from app.services.text_extractor import TextExtractorService

logger = logging.getLogger(__name__)


class SeleniumExtractorService:
    """基于Selenium的URL提取服务"""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.text_extractor = TextExtractorService()
    
    def _check_network_connectivity(self) -> bool:
        """检查网络连接状态"""
        try:
            # 尝试连接到一个可靠的DNS服务器
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            try:
                # 备用DNS服务器
                socket.create_connection(("1.1.1.1", 53), timeout=5)
                return True
            except OSError:
                return False
    
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
        
        # 禁用Selenium Manager自动下载功能
        chrome_options.set_capability("se:enableManager", False)
        
        # 定义可能的chromedriver路径
        possible_driver_paths = [
            "/usr/local/bin/chromedriver",  # 用户安装的路径
            "/usr/bin/chromedriver",        # 系统路径
            "chromedriver",                 # PATH中的chromedriver
        ]
        
        driver_path = None
        for path in possible_driver_paths:
            if os.path.exists(path) or path == "chromedriver":
                try:
                    # 测试路径是否可用
                    if path == "chromedriver":
                        # 检查PATH中是否有chromedriver
                        import shutil
                        if shutil.which("chromedriver"):
                            driver_path = "chromedriver"
                            break
                    else:
                        # 检查文件是否可执行
                        if os.access(path, os.X_OK):
                            driver_path = path
                            break
                except Exception:
                    continue
        
        if not driver_path:
            raise Exception("未找到可用的chromedriver。请确保chromedriver已安装并在以下路径之一：/usr/local/bin/chromedriver, /usr/bin/chromedriver, 或系统PATH中")
        
        try:
            logger.info(f"Setting up Chrome driver using: {driver_path}")
            
            # 明确指定使用本地chromedriver，跳过Selenium Manager
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            logger.info("Chrome driver setup successful")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise Exception(f"无法设置Chrome WebDriver。请确保：1) 已安装Chrome浏览器 2) chromedriver已正确安装并可执行。错误详情: {e}")
    
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
    
    
    def extract_urls(self, request: UrlExtractRequest) -> UrlExtractResponse:
        """提取URL"""
        start_time = time.time()
        
        # 检查网络连接
        if not self._check_network_connectivity():
            logger.error("No network connectivity detected")
            return UrlExtractResponse(
                success=False,
                source_url=str(request.url),
                extracted_urls=[],
                total_links_found=0,
                processing_time=time.time() - start_time,
                error_message="网络连接不可用，请检查网络设置",
                method="selenium"
            )
        
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
            
            # 获取完整的HTML内容（包括JavaScript渲染后的内容）
            html_content = self.driver.page_source
            
            # 提取文本内容
            text_content = self.text_extractor.extract_text_content(html_content)
            
            # 提取结构化内容
            structured_content = self.text_extractor.extract_structured_content(html_content)
            
            processing_time = time.time() - start_time
            
            return UrlExtractResponse(
                success=True,
                source_url=str(request.url),
                extracted_urls=extracted_urls,
                total_links_found=len(extracted_urls),
                processing_time=processing_time,
                method="selenium",
                html_content=html_content,
                text_content=text_content,
                structured_content=structured_content
            )
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            processing_time = time.time() - start_time
            
            return UrlExtractResponse(
                success=False,
                source_url=str(request.url),
                extracted_urls=[],
                total_links_found=0,
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
