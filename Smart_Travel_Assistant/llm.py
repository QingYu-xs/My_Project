from openai import OpenAI
from prompt_template import Agent_system_prompt

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的 LLM 服务的客户端
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """ 调用 LLM API 来生成回应 """
        print('正在调用大模型...')
        try:
            message = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=False
            )
            answer = response.choices[0].message.content
            print('大模型响应成功')
            return answer
        except Exception as e:
            print(f'调用 LLM API 时发生错误：{e}！')
            return '错误：调用大语言模型服务时出错！'


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    # 加载环境变量
    load_dotenv()

    # ========= 1.配置 LLM 客户端 =========
    API_KEY = os.environ.get('OPENAI_API_KEY')
    BASE_URL = os.environ.get('BASE_URL')
    MODEL = os.environ.get('MODEL_NAME')
    TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

    # 创建大模型客户端对象
    qwen_llm = OpenAICompatibleClient(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY)

    user_input = '你好，请帮我查绚以下重庆的天气，然后根据天气推荐一个合适的旅游景点。'
    prompt_history = [f'用户需求：{user_input}']

    print(f"用户输入：{user_input}\n" + '=' * 40)

    # ========= 3.运行主循环 =========
    for i in range(1):
        print(f'--- 循环{i + 1} ---\n')
        # 3.1 构建 prompt
        full_prompt = '\n'.join(prompt_history)

        # 3.2 调用LLM 进行思考
        llm_output = qwen_llm.generate(full_prompt, system_prompt=Agent_system_prompt)
        print(llm_output)
