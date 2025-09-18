from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class UrlExtractRequest(BaseModel):
    """URL提取请求模型"""
    url: HttpUrl
    include_external: bool = True  # 是否包含外部链接
    include_internal: bool = True  # 是否包含内部链接
    max_links: Optional[int] = None  # 最大链接数量限制


class UrlExtractResponse(BaseModel):
    """URL提取响应模型"""
    source_url: str
    extracted_urls: List[str]
    total_links_found: int
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    method: Optional[str] = None  # 使用的提取方法 (requests/selenium)
    html_content: Optional[str] = None  # 原始HTML内容
    text_content: Optional[str] = None  # 提取的文本内容
    structured_content: Optional[dict] = None  # 结构化内容信息
