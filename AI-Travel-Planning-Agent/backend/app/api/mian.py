"""FastAPI主应用"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="智能旅行助手",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS  跨域资源共享
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origin_list(),  # 指定哪些前端域名可以访问后端API,提高安全性
    allow_credentials=True,  # 当设置为True时， 允许浏览器发送认证信息（如cookies）
    allow_methods=["*"],  # 请求方法 不限制
    allow_headsers=["*"]  # 请求头  不限制
)

# 注册路由
app.include_router(trip.router)


