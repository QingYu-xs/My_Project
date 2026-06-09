from dotenv import load_dotenv
from llm import OpenAICompatibleClient
import os
from prompt_template import Agent_system_prompt
import re
# 导入工具
from tools import available_tools

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

while True:
    # ========= 2.初始化 =========
    # user_input = '你好，请帮我查绚以下重庆的天气，然后根据天气推荐一个合适的旅游景点，并计算一下预算金额。'
    user_input = input('请输入你的需求：')
    if user_input in ['q', 'exit', 'quit']:
        break
    prompt_history = [f'用户需求：{user_input}']

    print(f"用户输入：{user_input}\n" + '+' * 100)

    # ========= 3.运行主循环 =========
    for i in range(5):
        print(f'--- 步骤{i + 1} ---\n')
        # 3.1 构建 prompt
        full_prompt = '\n'.join(prompt_history)

        # 3.2 调用LLM 进行思考
        llm_output = qwen_llm.generate(full_prompt, system_prompt=Agent_system_prompt)
        # 模型可能会输出多余的 Thought-Action，需要截断
        match = re.search(r'(Thought:.*?Action:.*?)(?=\ns*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print('已截断多余的 Thought-Action 对')
        print(f"模型输出：\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 3.3 解析并执行行动
        action_match = re.search(f"Action:(.*)", llm_output, re.DOTALL)
        if not action_match:
            observation = "错误：未能解析到 Action 字段，请确保你的回复严格遵循'Thought:... Action:...'的格式。"
            observation_str = f"Observation:{observation}"
            print(f"{observation_str}\n" + '==' * 30)
            prompt_history.append(observation_str)
            continue
        action_str = action_match.group(1).strip()

        if action_str.startswith('Finish'):
            final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
            print(f"任务完成，最终答案：{final_answer}")
            break

        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)', args_str))

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未定义的工具 {tool_name}"

        # 3.4 记录观察结果
        observation_str = f"Observation：{observation}"
        print(f'{observation_str}\n' + '==' * 30)
        prompt_history.append(observation_str)


