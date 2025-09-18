# URL Extract Service

一个基于FastAPI的工程化项目，用于提取网页中的URL链接。

## 项目结构

```
├── app/                    # 主应用目录
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   └── health.py      # 健康检查端点
│   ├── core/              # 核心配置
│   │   ├── __init__.py
│   │   └── config.py      # 应用配置
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic模式
│   ├── services/          # 业务逻辑服务
│   ├── utils/             # 工具函数
│   ├── __init__.py
│   └── main.py            # 主应用入口
├── tests/                 # 测试文件
├── docs/                  # 文档
├── requirements.txt       # 依赖包
└── README.md             # 项目说明
```

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动应用：
```bash
uvicorn app.main:app --reload
```

3. 访问健康检查端点：
```
GET http://localhost:8000/api/v1/health
```

## API文档

启动应用后，可以访问以下地址查看自动生成的API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
