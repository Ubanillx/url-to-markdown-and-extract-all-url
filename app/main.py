from fastapi import FastAPI
from app.api import health
from app.api import url_extract

app = FastAPI(
    title="URL to Markdown and Extract URL",
    description="一个用于将URL转换为Markdown并提取URL的服务 - 支持a标签和正则表达式两种方式提取链接",
    version="1.0.0"
)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(url_extract.router, prefix="/api/v1", tags=["url-extract"])
