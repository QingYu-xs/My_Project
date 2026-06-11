"""配置管理模块
定义 API 提供商参数、分块策略、Flask 服务参数等全局配置。
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用全局配置类"""

    # API 提供商配置
    # 每个条目包含：embedding 模型名、LLM 模型名、API 请求地址
    API_KEYS = {
        "qwen": {
            "embedding_model": "text-embedding-v4",
            "llm_model": "qwen3.6-plus",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
        "zhipu": {
            "embedding_model": "Embedding-3",
            "llm_model": "GLM-4.7-Flash",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
        },
        "deepseek": {
            "embedding_model": "deepseek-text-embedding",
            "llm_model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
        },
    }

    API_TYPES = ["qwen", "Qwen", "zhipu", "deepseek", "DeepSeek"]
    DEFAULT_API_TYPE = "qwen"

    # 文档分块参数
    DOCUMENT_SIZE_CHUK = 500      # 每块最大字符数
    CHUNK_OVERLAP = 100           # 相邻块之间的重叠字符数

    # 支持的文件类型
    SUPPORT_FILES_TYPES = [".pdf", ".docx", ".md", ".txt"]

    # API Key
    @staticmethod
    def get_api_key():
        """从环境变量 / .env 文件读取 API Key"""
        return os.environ.get("Qwen_API_KEY")

    # Flask 服务配置
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    FLASK_DEBUG = True

    # 上传限制
    MAX_UPLOAD_SIZE_MB = 50
    MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
