from fastapi import FastAPI
from app.api import health
from app.api import url_extract
from app.api import markdown_extract

app = FastAPI(
    title="URL Extract & Markdown Service",
    description="一个用于提取网页中URL链接和转换为Markdown格式的服务 - 支持静态和动态网页内容提取",
    version="1.0.0"
)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(url_extract.router, prefix="/api/v1", tags=["url-extract"])
app.include_router(markdown_extract.router, prefix="/api/v1", tags=["markdown-extract"])
