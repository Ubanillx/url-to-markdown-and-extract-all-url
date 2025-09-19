from fastapi import APIRouter, HTTPException
from app.schemas.markdown_extract import MarkdownExtractRequest, MarkdownExtractResponse
from app.services.selenium_extractor import SeleniumExtractorService
from app.services.markdown_converter import MarkdownConverterService
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
selenium_extractor = SeleniumExtractorService()
markdown_converter = MarkdownConverterService()


@router.post("/extract/markdown", response_model=MarkdownExtractResponse)
async def extract_markdown_from_webpage(request: MarkdownExtractRequest):
    """
    网页Markdown提取端点 - 使用Selenium提取动态网页内容并转换为Markdown格式
    
    适用于：
    - 单页应用(SPA)
    - 需要JavaScript渲染的网页
    - 动态加载内容的网页
    - React、Vue、Angular等框架构建的网页
    
    参数：
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    - **include_images**: 是否包含图片 (默认: True)
    - **include_tables**: 是否包含表格 (默认: True)
    - **clean_html**: 是否清理HTML标签 (默认: True)
    
    返回包含以下信息的JSON:
    - extracted_urls: 提取到的URL数组
    - total_links_found: 找到的链接总数
    - processing_time: 处理时间(秒)
    - success: 是否成功
    - error_message: 错误信息(如果有)
    - method: 使用的提取方法 (selenium)
    - markdown_content: 转换后的markdown内容
    - title: 页面标题
    - description: 页面描述
    - headings: 标题结构
    - images: 图片信息
    - tables: 表格信息
    - html_content: 原始HTML内容（可选）
    - text_content: 提取的文本内容（可选）
    - structured_content: 结构化内容信息（可选）
    """
    start_time = time.time()
    
    try:
        # 使用Selenium提取网页内容
        from app.schemas.url_extract import UrlExtractRequest
        url_request = UrlExtractRequest(
            url=request.url,
            include_external=request.include_external,
            include_internal=request.include_internal,
            max_links=request.max_links
        )
        
        result = selenium_extractor.extract_urls(url_request)
        
        if not result.success:
            return MarkdownExtractResponse(
                success=False,
                source_url=str(request.url),
                extracted_urls=[],
                total_links_found=0,
                processing_time=time.time() - start_time,
                error_message=result.error_message,
                method="selenium"
            )
        
        # 转换HTML为Markdown
        markdown_content = markdown_converter.html_to_markdown(
            html_content=result.html_content,
            base_url=str(request.url),
            include_images=request.include_images,
            include_tables=request.include_tables,
            clean_html=request.clean_html
        )
        
        # 提取元数据
        metadata = markdown_converter.extract_metadata(result.html_content)
        
        processing_time = time.time() - start_time
        
        return MarkdownExtractResponse(
            success=True,
            source_url=str(request.url),
            extracted_urls=result.extracted_urls,
            total_links_found=result.total_links_found,
            processing_time=processing_time,
            method="selenium",
            markdown_content=markdown_content,
            title=metadata['title'],
            description=metadata['description'],
            headings=metadata['headings'],
            images=metadata['images'],
            tables=metadata['tables'],
            html_content=result.html_content,
            text_content=result.text_content,
            structured_content=result.structured_content
        )
        
    except Exception as e:
        logger.error(f"Error during markdown extraction: {e}")
        processing_time = time.time() - start_time
        
        return MarkdownExtractResponse(
            success=False,
            source_url=str(request.url),
            extracted_urls=[],
            total_links_found=0,
            processing_time=processing_time,
            method="selenium",
            error_message=str(e)
        )


@router.get("/extract/markdown")
async def extract_markdown_from_webpage_get(
    url: str,
    include_external: bool = True,
    include_internal: bool = True,
    max_links: int = None,
    include_images: bool = True,
    include_tables: bool = True,
    clean_html: bool = True
):
    """
    通过GET请求提取网页内容并转换为Markdown格式
    
    参数：
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    - **include_images**: 是否包含图片 (默认: True)
    - **include_tables**: 是否包含表格 (默认: True)
    - **clean_html**: 是否清理HTML标签 (默认: True)
    """
    try:
        request = MarkdownExtractRequest(
            url=url,
            include_external=include_external,
            include_internal=include_internal,
            max_links=max_links,
            include_images=include_images,
            include_tables=include_tables,
            clean_html=clean_html
        )
        
        return await extract_markdown_from_webpage(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理Markdown提取请求时发生错误: {str(e)}")


@router.post("/extract/markdown/clean", response_model=MarkdownExtractResponse)
async def extract_clean_markdown_from_webpage(request: MarkdownExtractRequest):
    """
    网页Markdown提取端点（仅返回Markdown内容）- 使用Selenium提取动态网页内容并转换为Markdown格式
    
    这个端点专门用于获取干净的Markdown内容，不返回原始HTML等冗余信息。
    
    参数：
    - **url**: 要处理的网页URL
    - **include_external**: 是否包含外部链接 (默认: True)
    - **include_internal**: 是否包含内部链接 (默认: True)
    - **max_links**: 最大链接数量限制 (可选)
    - **include_images**: 是否包含图片 (默认: True)
    - **include_tables**: 是否包含表格 (默认: True)
    - **clean_html**: 是否清理HTML标签 (默认: True)
    
    返回包含以下信息的JSON:
    - extracted_urls: 提取到的URL数组
    - total_links_found: 找到的链接总数
    - processing_time: 处理时间(秒)
    - success: 是否成功
    - error_message: 错误信息(如果有)
    - method: 使用的提取方法 (selenium)
    - markdown_content: 转换后的markdown内容
    - title: 页面标题
    - description: 页面描述
    - headings: 标题结构
    - images: 图片信息
    - tables: 表格信息
    """
    start_time = time.time()
    
    try:
        # 使用Selenium提取网页内容
        from app.schemas.url_extract import UrlExtractRequest
        url_request = UrlExtractRequest(
            url=request.url,
            include_external=request.include_external,
            include_internal=request.include_internal,
            max_links=request.max_links
        )
        
        result = selenium_extractor.extract_urls(url_request)
        
        if not result.success:
            return MarkdownExtractResponse(
                success=False,
                source_url=str(request.url),
                extracted_urls=[],
                total_links_found=0,
                processing_time=time.time() - start_time,
                error_message=result.error_message,
                method="selenium"
            )
        
        # 转换HTML为Markdown
        markdown_content = markdown_converter.html_to_markdown(
            html_content=result.html_content,
            base_url=str(request.url),
            include_images=request.include_images,
            include_tables=request.include_tables,
            clean_html=request.clean_html
        )
        
        # 提取元数据
        metadata = markdown_converter.extract_metadata(result.html_content)
        
        processing_time = time.time() - start_time
        
        return MarkdownExtractResponse(
            success=True,
            source_url=str(request.url),
            extracted_urls=result.extracted_urls,
            total_links_found=result.total_links_found,
            processing_time=processing_time,
            method="selenium",
            markdown_content=markdown_content,
            title=metadata['title'],
            description=metadata['description'],
            headings=metadata['headings'],
            images=metadata['images'],
            tables=metadata['tables']
            # 注意：不返回html_content, text_content, structured_content以节省带宽
        )
        
    except Exception as e:
        logger.error(f"Error during clean markdown extraction: {e}")
        processing_time = time.time() - start_time
        
        return MarkdownExtractResponse(
            success=False,
            source_url=str(request.url),
            extracted_urls=[],
            total_links_found=0,
            processing_time=processing_time,
            method="selenium",
            error_message=str(e)
        )
