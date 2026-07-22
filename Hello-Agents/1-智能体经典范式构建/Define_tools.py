"""
为智能体提供一个网页搜索工具，选用 SerpApi, 官网 https://serpapi.com/
获取 API_KEY 添加到 .env 文件中
安装 第三方库
pip install google-search-results

工具三要素：名称、描述、实现
"""
import os
from dotenv import load_dotenv
from serpapi import SerpApiClient

# 加载.env文件中的环境变量
load_dotenv()

def search(query: str) -> str:
    """
    一个基于 SerpApi 的网页搜索引擎工具
    可以智能的解析搜索结果，优先返回直接答案或者只是图谱信息。
    :param query:检索关键词
    :return:搜索结果
    """
    print(f'🔍 正在执行 【SerpApi】 网页搜索：{query}!')
    try:
        api_key = os.getenv('SERPAPI_API_KEY')
        if not api_key:
            return '错误：SERPAPI_API_KEY 未在 .env 文件中配置。'
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn"  # 语言
        }
        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析，检查是否存在google的答案摘要框 或者知识图谱
        if "answer_box_list" in results:
            return '\n'.join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results['answer_box']:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('tittle', '')} \n {res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        return f"抱歉，没有找到关于'{query}' 的信息！"
    except Exception as e:
        return f"搜索时发生错误：{e}!"


if __name__ == '__main__':
    from Universal_tool_executor import ToolExecutor
    # 1. 初始化工具执行器
    tool_executor = ToolExecutor()

    # 2. 注册我们定义好的搜索工具
    search_description = "一个网页搜索引擎，当你需回答相关时事、事实以及在你的知识库中找不到相关信息时，应该使用此工具。"
    tool_executor.register_tool(name='search', description=search_description, func=search)
    print(tool_executor.tools)

    # 3. 打印可用工具
    print(f" \n ---- 可用的工具 ----")
    print(tool_executor.get_available_tools())

    # 4.智能体的Action 调用，问一个实时性的问题
    print(f"\n ---- 执行 Action: search['英伟达最新的GPU型号是什么？'] ----")
    tool_name = 'search'
    tool_input = '英伟达最新的GPU型号是什么？'
    tool_function = tool_executor.get_tool(tool_name)
    if tool_function:
        # 调用工具并返回结果
        observation = tool_function(tool_input)
        print("---- 观察（Observation） ----")
        print(observation)
    else:
        print(f"未找到名为：{tool_name} 的工具！")


