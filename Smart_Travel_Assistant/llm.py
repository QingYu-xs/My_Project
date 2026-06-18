from openai import OpenAI
from prompt_template import Agent_system_prompt

class OpenAICompatibleClient:
    """
    兼容 OpenAI 接口的 LLM 客户端封装
    支持任何实现了 OpenAI API 规范的服务（通义千问、GPT、Claude 等）
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        # 初始化 OpenAI 客户端，只需要替换 base_url 就能切换到不同的模型服务
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用 LLM 生成回复"""
        print('正在调用大模型...')
        try:
            # 构造消息列表：system 角色设定行为，user 角色输入 prompt
            message = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=False  # 非流式输出，一次性拿到完整回复
            )
            answer = response.choices[0].message.content
            print('大模型响应成功！')
            return answer
        except Exception as e:
            print(f'调用 LLM API 时发生错误：{e}！')
            return '错误：调用大语言模型服务时出错！'


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()

    API_KEY = os.environ.get('OPENAI_API_KEY')
    BASE_URL = os.environ.get('BASE_URL')
    MODEL = os.environ.get('MODEL_NAME')

    qwen_llm = OpenAICompatibleClient(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY)

    user_input = '你好，请帮我查绚以下重庆的天气，然后根据天气推荐一个合适的旅游景点。'
    prompt_history = [f'用户需求：{user_input}']

    print(f"用户输入：{user_input}\n" + '=' * 40)

    for i in range(1):
        print(f'--- 循环{i + 1} ---\n')
        full_prompt = '\n'.join(prompt_history)
        llm_output = qwen_llm.generate(full_prompt, system_prompt=Agent_system_prompt)
        print(llm_output)

