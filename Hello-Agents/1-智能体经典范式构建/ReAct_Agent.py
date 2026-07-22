"""
现在将所有独立的组件, LLM客户端和工具执行器组装起来，构建一个完整的ReAct智能体。
"""
import re

from LLM_Client import LLM_Client
from Universal_tool_executor import ToolExecutor

# 1.系统提示词设计
"""
    * 角色定义：“你是一个有能力调用外部工具的智能助手”，设定 LLM 的角色
    * 工具清单（{tools}）：告知大模型有哪些可用的“手脚”。
    * 格式规约（Thought/Action）：这是最重要的部分，强制大模型结构化输出，让我们能够通过代码精确解析其意图。
    * 动态上下文（{question/history}）：将用户的历史问题和不断累积的交互历史不断注入，让大模型基于完整的上下文进行决策。
"""
# ReAct 提示词模板
REACt_PROMPT_TEMPLATE = """
你是一个有能力调用外部工具的智能助手，你需要根据用户的问题，调用工具使用中文来回答问题。

可用工具如下：
{{tools}}

请严格按照以下格式进行回应：
Thought: 你的思考过程，用于分析问题，拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一
- `{{tool_name}}[{{tool_input}}]`: 调用一个可用的工具。
- `Finish[最终结果]`: 当你认为以获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action: 字段后使用 Finish[最终结果] 来输出最终结果。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""


# 2.核心循环的实现
#  ReActAgent 的核心是一个循环，不断的“格式化提示词-> 调用LLM -> 执行动作 -> 整合结果”，直到任务完成或者达到最大步数限制。
class ReActAgent:
    def __init__(self, llm_client: LLM_Client, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        """
        运行一个ReAct智能体来回答一个问题
        :param question:
        :return:None
        """
        # 每一次运行时重置历史记录
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"------ 第{current_step}步 ------")

            # (1) 格式化提示词
            tools_desc = self.tool_executor.get_available_tools()
            history_str = '\n'.join(self.history)
            prompt = REACt_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # (2) 调用大模型进行思考
            messages = [{"role": "user", " content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print('错误，LLM未能返回有效响应！')
                break

            # 4. 工具调用与执行
            # (3) 解析LLM输出
            thought, action = self.parse_output(response_text)
            if thought:
                print(f"思考：{thought}")
            if not action:
                print(f"警告：未能解析出有效的Action，流程终止!")
                break
            # (4) 执行 Action
            if action.startswith('Finish'):
                # 如果是Finish 指令，提取最终答案并结束
                final_answer = re.match(r"Finish\[(.*)\]", action).group(1)
                print(f"最终答案：{final_answer}")
                return final_answer

            tool_name, tool_input = self.parse_action(action)
            if not tool_name or not tool_input:
                # 处理无效的Action 格式
                continue
            print(f'行动：{tool_name}[{tool_input}]')

            tool_function = self.tool_executor.get_tool(tool_name)
            if not tool_function:
                observation = f"错误：未找到名为'{tool_name}'的工具！"
            else:
                observation = tool_function(tool_input)
                print(f"观察：{observation}")
                # 将本轮的Action和Observation 添加到历史记录中
                self.history.append(f"Action: {action}")
                self.history.append(f"Observation: {observation}")

            # 循环结束
            print("已达到最大步数，流程终止！")
            return None

    # 3.实现输出解析器
    def parse_output(self, text: str):
        """
        解析 LLM 的输出，获取Thought和Action
        负责从LLM 的完整响应中分离出 Though 和 Action 两个主要部分
        """
        # Thought: 匹配到Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        r"""
        分解说明：
        r"Thought:\s*(.*?)(?=\nAction:|$)"
        Thought:     - 匹配字面量 "Thought:"
        \s*          - 匹配0个或多个空白字符（空格、换行等）
        (.*?)        - 非贪婪捕获组，匹配任意字符（包括换行符，因为有DOTALL标志）
        (?=\nAction:|$) - 正向先行断言，确保后面跟着 "\nAction:" 或者字符串结尾
        DOTALL       - 让 . 也能匹配换行符
        """

        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def parse_action(self, action_text: str):
        """
        解析 action 字符串，获取工具名称和输入
        负责进一步解析 Action 字符串，例如从 search[华为最新手机]中提取出工具名称 search 和 工具输入 华为最新手机
        """
        match = re.match(r'(\w+)\[(.*)\]', action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None


if __name__ == '__main__':
    llm_client = LLM_Client()
    tool_executor = ToolExecutor()
    react_agent = ReActAgent(llm_client=llm_client, tool_executor=tool_executor)
    question = input('请输入你的问题：').strip()
    react_agent.run(question)

