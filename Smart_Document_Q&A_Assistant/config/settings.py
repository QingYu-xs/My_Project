"""
配置管理模块
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """ 应用配置类 """
    API_KEYS = {
        'qwen': {
            'embedding_model': 'text-embedding-v4',
            'llm_model': 'qwen3.6-plus',
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        },
        'zhipu': {
            'embedding_model': 'Embedding-3',
            'llm_model': 'GLM-4.7-Flash',
            'base_url': 'https://open.bigmodel.cn/api/paas/v4'
        },
        "deepseek": {
            "embedding_model": "deepseek-text-embedding",
            "llm_model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1"
        }
    }

    API_TYPES = ['qwen', 'Qwen', 'zhipu', 'deepseek', 'DeepSeek']

    # 文档快大小
    DOCUMENT_SIZE_CHUK = 500
    # 分块重叠数
    CHUNK_OVERLAP = 100

    # 服务器地址
    GRADIO_SERVER = "127.0.0.1"
    # 端口
    GRADIO_PORT = 7680
    # 支持的文件类型
    SUPPORT_FILES_TYPES = ['.pdf', '.docx', '.md', '.txt']

    @staticmethod
    def get_api_key():
        """ 获取API密钥 """
        return os.environ.get('Qwen_API_KEY')


if __name__ == '__main__':
    config = Config()
    api_key = config.get_api_key()
    print(api_key)



    # Ollama 配置
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
    OLLAMA_LLM_MODEL = "qwen2.5:7b"

    # Flask 配置
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    FLASK_DEBUG = True

    MAX_UPLOAD_SIZE_MB = 50
    MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
