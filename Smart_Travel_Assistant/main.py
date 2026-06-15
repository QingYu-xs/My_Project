from dotenv import load_dotenv
from llm import OpenAICompatibleClient
import os
from prompt_template import Agent_system_prompt
import re
from tools import available_tools

# 加载 .env 文件中的环境变量（API密钥等配置）
load_dotenv()

# ========= 1. 从环境变量读取 LLM 配置 =========
API_KEY = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')
MODEL = os.environ.get('MODEL_NAME')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# 创建大模型客户端（兼容 OpenAI 接口的模型都可以用）
qwen_llm = OpenAICompatibleClient(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY)

# 主循环：持续接收用户输入，直到输入 q/exit/quit 退出
while True:
    # ========= 2. 获取用户输入并初始化 =========
    user_input = input('请输入你的需求：')
    if user_input in ['q', 'exit', 'quit']:
        break
    # prompt_history 保存整个对话的上下文，每轮追加模型输出和工具返回结果
    prompt_history = [f'用户需求：{user_input}']

    print(f"用户输入：{user_input}\n" + '+' * 100)

    # ========= 3. ReAct 循环：最多执行 5 轮 =========
    # 每一轮：模型思考 -> 输出 Action -> 解析并调用工具 -> 观察结果 -> 进入下一轮
    for i in range(5):
        print(f'--- 步骤{i + 1} ---\n')

        # 3.1 把整个对话历史拼接成一个完整的 prompt 喂给模型
        full_prompt = '\n'.join(prompt_history)

        # 3.2 调用 LLM 生成回复，期望输出格式为 "Thought: ... Action: ..."
        llm_output = qwen_llm.generate(full_prompt, system_prompt=Agent_system_prompt)

        # 模型有时会一次输出多对 Thought-Action，用正则截取第一对
        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print('已截断多余的 Thought-Action 对')

        print(f"模型输出：\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 3.3 从模型输出中解析 Action 字段
        action_match = re.search(r"Action:(.*)", llm_output, re.DOTALL)
        if not action_match:
            # 没解析到 Action，追加一条错误观察，让模型自己纠正格式
            observation = "错误：未能解析到 Action 字段，请确保你的回复严格遵循'Thought:... Action:...'的格式。"
            observation_str = f"Observation:{observation}"
            print(f"{observation_str}\n" + '==' * 30)
            prompt_history.append(observation_str)
            continue

        action_str = action_match.group(1).strip()

        # 如果 Action 以 Finish 开头，说明模型认为任务已完成，提取最终答案并结束
        if action_str.startswith('Finish'):
            final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
            print(f"任务完成，最终答案：{final_answer}")
            break

        # 解析工具名：从 "get_weather(city_name="北京")" 中提取 "get_weather"
        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        # 解析参数：提取括号内的参数字符串
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        # 将参数解析为字典：{"city_name": "北京"}
        kwargs = dict(re.findall(r'(\w+)="([^"]*)', args_str))

        # 3.4 调用对应的工具函数
        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未定义的工具 {tool_name}"

        # 把工具返回的结果作为 Observation 追加到上下文，供下一轮推理使用
        observation_str = f"Observation：{observation}"
        print(f'{observation_str}\n' + '==' * 30)
        prompt_history.append(observation_str)


