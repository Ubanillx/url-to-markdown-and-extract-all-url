from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any


class MarkdownExtractRequest(BaseModel):
    """Markdown提取请求模型"""
    url: HttpUrl
    include_external: bool = True  # 是否包含外部链接
    include_internal: bool = True  # 是否包含内部链接
    max_links: Optional[int] = None  # 最大链接数量限制
    include_images: bool = True  # 是否包含图片
    include_tables: bool = True  # 是否包含表格
    clean_html: bool = True  # 是否清理HTML标签


class MarkdownExtractResponse(BaseModel):
    """Markdown提取响应模型"""
    source_url: str
    extracted_urls: List[str]
    total_links_found: int
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    method: Optional[str] = None  # 使用的提取方法 (selenium)
    
    # Markdown相关字段
    markdown_content: Optional[str] = None  # 转换后的markdown内容
    title: Optional[str] = None  # 页面标题
    description: Optional[str] = None  # 页面描述
    headings: Optional[List[Dict[str, Any]]] = None  # 标题结构
    images: Optional[List[Dict[str, str]]] = None  # 图片信息
    tables: Optional[List[Dict[str, Any]]] = None  # 表格信息
    
    # 原始内容（可选）
    html_content: Optional[str] = None  # 原始HTML内容
    text_content: Optional[str] = None  # 提取的文本内容
    structured_content: Optional[dict] = None  # 结构化内容信息
