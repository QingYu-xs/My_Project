"""
LLM 模型工厂 - 根据不同的 APIl类型创建对应的模型实例
"""
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from config.settings import Config
import os
load_dotenv()

class Llm_Factory:
    """ LLM 工厂"""

    @staticmethod
    def create_embedding(api_type: str, api_key: str, base_url: str = None):
        """
        创建词嵌入模型
        :param api_type: API类型（qwen/zhipu/deepseek）
        :param api_key:API密钥
        :param base_url:自定义url
        :return: OpenAIEmbedding实例
        """
        if api_type not in Config.API_TYPES:
            raise ValueError(f'不支持的API类型：{api_type}')
        # api配置
        api_config = Config.API_KEYS[api_type]
        finale_base_url = base_url or api_config['base_url']

        return OpenAIEmbeddings(
            model=api_config['embedding_model'],
            openai_api_key=api_key,
            base_url=finale_base_url
        )

    @staticmethod
    def create_llm(api_type: str, api_key: str, base_url: str = None, temperature: float = 0.7):
        """
        创建大语言模型
        :param api_type: API类型(qwen/zhipu/deepseek)
        :param api_key: API密钥
        :param base_url: 自定义基础url
        :param temperature: 温度参数
        :return: ChatOpenAI实例
        """
        if api_type not in Config.API_TYPES:
            raise ValueError(f'不支持的API类型：{api_type}')

        api_config = Config.API_KEYS[api_type]
        final_base_url = base_url or api_config['base_url']

        return ChatOpenAI(
            model=api_config['llm_model'],
            openai_api_key=api_key,
            base_url=final_base_url,
            temperature=temperature
        )

    @staticmethod
    def get_support_api_types():
        """获取支持的API类型列表"""
        return list(Config.API_KEYS.keys())


if __name__ == '__main__':
    # 创建词嵌入模型
    embedding_model = Llm_Factory.create_embedding(api_type='qwen', api_key=os.environ.get('Qwen_API_KEY'))

    # 创建大模型
    llm = Llm_Factory.create_llm(api_type='qwen', api_key=os.environ.get('Qwen_API_KEY'))
