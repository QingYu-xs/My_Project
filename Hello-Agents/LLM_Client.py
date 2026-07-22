from dotenv import load_dotenv
import os
from typing import List, Dict
from openai import OpenAI


# 加载.env文件中的环境变量
load_dotenv()

class LLM_Client:
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, timeout: int = None):
        """
        初始化客户端，优先使用传入的参数，没传则从 .env 文件读取
        """
        self.model = model or os.getenv('QWEN_MODEL_ID') or os.getenv('GLM_MODEL_ID')
        self.api_key = api_key or os.getenv('QWEN_API_KEY') or os.getenv('GLM_API_KEY')
        self.base_url = base_url or os.getenv('QWEN_BASE_URL') or os.getenv('GLM_BASE_URL')
        self.timeout = timeout or int(os.getenv('QWEN_TIMEOUT', 60)) or int(os.getenv('GLM_TIMEOUT', 60))

        if not all([self.model, self.api_key, self.base_url]):
            raise ValueError('模型ID、API密钥和服务地址必须提供或者在 .env 文件中定义！')

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0.5) -> str | None:
        """
        调用大模型进行思考，并返回其响应
        :param messages:消息列表
        :param temperature:模型思维活跃度
        """
        print(f'🧠 正在调用{self.model}大模型...')
        # try:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,  # 流式输出
        )
        # 处理流式响应
        print(f'✅ {self.model}大模型响应成功！')
        # 上下文列表
        collected_content = []
        for chunk in response:
            if chunk.choices and len(chunk.choices):
                content = chunk.choices[0].delta.content or ""
                print(content, end='', flush=True)
                collected_content.append(content)
        print()
        return ''.join(collected_content)

        # except Exception as e:
        #     print()
        #     print(f"❌调用LLMAPI时发生错误: {e}")
        #     return None


if __name__ == '__main__':
    try:
        llm_client = LLM_Client()

        example_messages = [
            {'role': 'system', 'content': '你是一个编写 Python 代码的编程助手，你需要尽可能的帮助用户。'},
            {'role': 'user', 'content': '写一个冒泡排序算法。'}
        ]
        print(f'{"==" * 10}调用大模型{"==" * 10}')
        response_text = llm_client.think(messages=example_messages)
        if response_text:
            print('\n\n --- 完整模型响应 ---')
            print(response_text)

    except ValueError as e:
        print(e)
