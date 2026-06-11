"""
LLM / Embedding 工厂
根据 API 类型（qwen / zhipu / deepseek）创建对应的模型实例。
对 qwen 的 Embedding 使用自定义 QwenEmbeddings 以兼容 Dashscope 格式。
"""
import os
from langchain_openai import ChatOpenAI
from models.qwen_embedding import QwenEmbeddings
from config.settings import Config


class LlmFactory:
    """根据 API 提供商类型，统一创建 Embedding 和 LLM 实例"""

    @staticmethod
    def create_embedding(api_type: str, api_key: str, base_url: str = None):
        """
        创建 Embedding 模型实例

        - qwen：     使用自定义 QwenEmbeddings（适配 Dashscope 的 input 格式）
        - zhipu：    使用 OpenAIEmbeddings（兼容 OpenAI 格式）
        - deepseek： 使用 OpenAIEmbeddings（兼容 OpenAI 格式）
        """
        api_type = api_type.lower()
        api_config = Config.API_KEYS.get(api_type)
        if not api_config:
            raise ValueError(f"不支持的 API 类型: {api_type}")

        base = base_url or api_config["base_url"]

        if api_type == "qwen":
            # 通义千问需要用自定义适配器，因为其 /embeddings 接口不接受列表批量
            return QwenEmbeddings(
                api_key=api_key,
                model=api_config["embedding_model"],
                base_url=base,
            )

        # 智谱 / DeepSeek 使用标准 OpenAI 格式即可
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=api_config["embedding_model"],
            openai_api_key=api_key,
            base_url=base,
        )

    @staticmethod
    def create_llm(api_type: str, api_key: str, base_url: str = None, temperature: float = 0.7):
        """创建对话 LLM 实例。所有支持的 API 都提供 OpenAI 兼容的聊天接口。"""
        api_type = api_type.lower()
        api_config = Config.API_KEYS.get(api_type)
        if not api_config:
            raise ValueError(f"不支持的 API 类型: {api_type}")

        base = base_url or api_config["base_url"]
        return ChatOpenAI(
            model=api_config["llm_model"],
            openai_api_key=api_key,
            base_url=base,
            temperature=temperature,
        )

    @staticmethod
    def get_support_api_types():
        """返回所有可用的 API 提供商列表"""
        return list(Config.API_KEYS.keys())
