import json
import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient
from llm import OpenAICompatibleClient
from datetime import datetime

load_dotenv()

API_KEY = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')
MODEL = os.environ.get('MODEL_NAME')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# 偏好标签
PREFERENCE_LABELS = {
    "经典": "经典地标、历史古迹、必打卡景点",
    "美食": "特色美食街、当地餐厅、小吃夜市",
    "文化": "博物馆、艺术馆、民俗文化体验",
    "自然": "自然风光、公园、山水景区",
    "拍照": "网红打卡点、摄影圣地、观景台",
    "亲子": "亲子乐园、科技馆、适合家庭的活动"
}


def search_attractions(destination, preferences):
    client = TavilyClient(api_key=TAVILY_API_KEY)
    pref_text = "、".join(preferences) if preferences else "热门旅游"
    q = f"{destination} {pref_text} 旅游景点 推荐 攻略 2025"
    try:
        r = client.search(query=q, search_depth="basic", include_answer=True, max_results=10)
        p = []
        if r.get("answer"): p.append(f"综述: {r['answer']}")
        for x in r.get("results", []): p.append(f"- {x.get('title', '')}: {x.get('content', '')[:200]}")
        return "\n".join(p) if p else "未找到相关景点信息"
    except Exception as e:
        return f"搜索景点时出错: {e}"


def generate_itinerary(destination, days, preferences):
    llm = OpenAICompatibleClient(model=MODEL, base_url=BASE_URL, api_key=API_KEY)
    info = search_attractions(destination, preferences)
    pd = "\n".join(f"- {k}: {v}" for k, v in PREFERENCE_LABELS.items())
    sp = "、".join(preferences) if preferences else "全部"
    sd = datetime.now().strftime("%Y年%m月%d日")

    sys = """你是一个专业的旅行规划师。请根据用户的需求生成详细的行程规划。

你必须以纯 JSON 格式输出，不要包含任何其他文字、Markdown代码块标记或说明。

输出格式要求：
{
  "destination": "目的地",
  "days": 天数,
  "preferences": ["偏好标签列表"],
  "itinerary": [
    {
      "day": 1,
      "date": "月日",
      "theme": "当日主题",
      "summary": "当日简要概述",
      "spots": [
        {
          "name": "景点名称",
          "description": "简短描述",
          "category": "经典/美食/文化/自然/拍照/亲子",
          "duration": "建议游玩时间",
          "tips": "小贴士"
        }
      ]
    }
  ]
}

要求：
1. 每天安排 3-5 个景点
2. 景点在时间线上合理
3. 景点距离合理，不需长途奔波
4. 根据用户偏好标签重点推荐
5. 包含交通和用餐推荐
6. description 20字以内"""

    usr = f"""请为以下旅行需求规划行程：

目的地：{destination}
天数：{days} 天
出发日期：{sd}
偏好标签：{sp}

偏好的详细说明：
{pd}

参考信息：
{info}

请直接输出 JSON 格式的完整行程规划。"""

    try:
        resp = llm.generate(usr, sys)
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', resp)
        js = m.group(1) if m else resp
        return json.loads(js.strip())
    except Exception as e:
        try:
            s = resp.find("{")
            e2 = resp.rfind("}")
            if s != -1 and e2 != -1:
                return json.loads(resp[s:e2 + 1])
        except Exception as e:
            print(f"解析 JSON 时发生错误：{e}")
            pass
        return {"error": f"生成行程失败: {e}", "raw": resp}


def format_itinerary_text(data):
    if "error" in data: return f"{data['error']}"
    dest = data.get("destination", "")
    days = data.get("days", 0)
    prefs = data.get("preferences", [])
    itin = data.get("itinerary", [])
    pt = "、".join(prefs) if prefs else "无特定偏好"
    lines = [f"**{dest} {days}天行程规划**", f"偏好标签：{pt}", ""]
    for day in itin:
        n = day.get("day", 0)
        th = day.get("theme", "")
        su = day.get("summary", "")
        lines.append(f"--- 第{n}天 ---")
        lines.append(f"主题：{th}")
        if su: lines.append(f"{su}")
        lines.append("")
        for si, s in enumerate(day.get("spots", []), 1):
            em = {"经典": "", "美食": "", "文化": "", "自然": "", "拍照": "", "亲子": ""}
            lines.append(f"{si}. {s.get('name', '')}")
            if s.get("description"): lines.append(f"   {s['description']}")
            if s.get("duration"): lines.append(f"   时长: {s['duration']}")
            if s.get("tips"): lines.append(f"   提示: {s['tips']}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    d = generate_itinerary("北京", 3, ["经典", "美食"])
    if "error" in d:
        print(f"失败: {d['error']}")
    else:
        print(format_itinerary_text(d))
