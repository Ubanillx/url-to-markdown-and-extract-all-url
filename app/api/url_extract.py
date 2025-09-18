from fastapi import APIRouter, HTTPException
from app.schemas.url_extract import UrlExtractRequest, UrlExtractResponse
from app.services.url_extractor import UrlExtractorService
from app.services.selenium_extractor import SeleniumExtractorService

router = APIRouter()
url_extractor = UrlExtractorService()
selenium_extractor = SeleniumExtractorService()


@router.post("/extract/static", response_model=UrlExtractResponse)
async def extract_static_webpage(request: UrlExtractRequest):
    """
    静态网页爬取端点 - 使用requests和BeautifulSoup提取静态网页内容
    
    适用于：
    - 传统HTML网页
    - 服务器端渲染的网页
    - 不需要JavaScript渲染的网页
    
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    
    返回包含以下信息的JSON:
    - extracted_urls: 提取到的URL数组
    - total_links_found: 找到的链接总数
    - processing_time: 处理时间(秒)
    - success: 是否成功
    - error_message: 错误信息(如果有)
    - method: 使用的提取方法 (requests)
    - html_content: 原始HTML内容
    """
    try:
        result = url_extractor.extract_urls(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理静态网页请求时发生错误: {str(e)}")


@router.post("/extract/dynamic", response_model=UrlExtractResponse)
async def extract_dynamic_webpage(request: UrlExtractRequest):
    """
    SPA动态网页抓取端点 - 使用Selenium提取需要JavaScript渲染的网页内容
    
    适用于：
    - 单页应用(SPA)
    - 需要JavaScript渲染的网页
    - 动态加载内容的网页
    - React、Vue、Angular等框架构建的网页
    
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    
    返回包含以下信息的JSON:
    - extracted_urls: 提取到的URL数组
    - total_links_found: 找到的链接总数
    - processing_time: 处理时间(秒)
    - success: 是否成功
    - error_message: 错误信息(如果有)
    - method: 使用的提取方法 (selenium)
    - html_content: 原始HTML内容（包括JavaScript渲染后的内容）
    """
    try:
        result = selenium_extractor.extract_urls(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理动态网页请求时发生错误: {str(e)}")


@router.get("/extract/static")
async def extract_static_webpage_get(
    url: str,
    include_external: bool = True,
    include_internal: bool = True,
    max_links: int = None
):
    """
    通过GET请求提取静态网页中的所有URL链接
    
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    """
    try:
        request = UrlExtractRequest(
            url=url,
            include_external=include_external,
            include_internal=include_internal,
            max_links=max_links
        )
        
        result = url_extractor.extract_urls(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理静态网页请求时发生错误: {str(e)}")


@router.get("/extract/dynamic")
async def extract_dynamic_webpage_get(
    url: str,
    include_external: bool = True,
    include_internal: bool = True,
    max_links: int = None
):
    """
    通过GET请求提取动态网页中的所有URL链接
    
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    """
    try:
        request = UrlExtractRequest(
            url=url,
            include_external=include_external,
            include_internal=include_internal,
            max_links=max_links
        )
        
        result = selenium_extractor.extract_urls(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理动态网页请求时发生错误: {str(e)}")
