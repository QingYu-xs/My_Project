import json
import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient
from llm import OpenAICompatibleClient
from datetime import datetime
from tools import get_weather

load_dotenv()

API_KEY = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')
MODEL = os.environ.get('MODEL_NAME')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

PREFERENCE_LABELS = {
    "经典": "经典地标、历史古迹、必打卡景点",
    "美食": "特色美食街、当地餐厅、小吃夜市",
    "文化": "博物馆、艺术馆、民俗文化体验",
    "自然": "自然风光、公园、山水景区",
    "拍照": "网红打卡点、摄影圣地、观景台",
    "亲子": "亲子乐园、科技馆、适合家庭的活动"
}

WEATHER_TIPS = {
    "Sunny": "紫外线较强，建议做好防晒措施，随身携带饮用水",
    "Clear": "天气晴好，适合户外活动，注意早晚温差",
    "Partly cloudy": "多云天气，体感舒适，适合全天出行",
    "Cloudy": "阴天，光线较暗拍照效果一般，建议带薄外套",
    "Overcast": "阴天，可能有短暂降雨，建议带伞",
    "Rain": "有雨，建议携带雨具，准备室内景点作为备选",
    "Light rain": "小雨，建议带伞，户外景点仍可正常游览",
    "Moderate rain": "中雨，建议优先安排室内活动",
    "Heavy rain": "大雨，建议调整行程以室内场馆为主",
    "Patchy rain nearby": "局部有雨，建议随身带伞，关注实时天气变化",
    "Thundery outbreaks": "有雷暴可能，建议避免露天活动",
    "Snow": "有雪，注意防寒保暖，关注交通信息",
    "Fog": "有雾，能见度较低，驾车出行需谨慎",
    "Mist": "薄雾，对出行影响较小，注意路面湿滑",
    "Haze": "有霾，建议减少户外长时间活动，佩戴口罩"
}


def search_attractions(destination, preferences):
    """
    用 Tavily 搜索引擎获取目的地的景点信息
    设 5 秒超时，失败时快速返回提示而不是让用户等几十秒
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    pref_text = "、".join(preferences) if preferences else "热门旅游"
    q = f"{destination} {pref_text} 旅游景点 推荐 攻略 2025"
    try:
        r = client.search(query=q, search_depth="basic", include_answer=True, max_results=10)
        p = []
        if r.get("answer"):
            p.append(f"综述: {r['answer']}")
        for x in r.get("results", []):
            p.append(f"- {x.get('title', '')}: {x.get('content', '')[:200]}")
        return "\n".join(p) if p else "未找到相关景点信息"
    except Exception as e:
        # 快速失败：网络不通时直接返回提示，不阻塞流程
        return f"搜索景点服务暂时不可用（{type(e).__name__}），将基于已有知识生成行程"


def generate_itinerary(destination, days, preferences):
    """
    核心函数：生成结构化行程
    流程：获取天气 -> 搜索景点 -> 构造 Prompt -> 调用 LLM -> 解析 JSON
    """
    llm = OpenAICompatibleClient(model=MODEL, base_url=BASE_URL, api_key=API_KEY)

    # 第一步：查询目的地当前天气（设了 5 秒超时，失败不影响行程生成）
    weather_info = get_weather(destination)
    weather_text = ""
    weather_data_for_output = None
    if weather_info and isinstance(weather_info, dict):
        weather_desc = weather_info.get("天气", "")
        weather_temp = weather_info.get("温度", "")
        weather_date = weather_info.get("日期", "")
        matched_tip = ""
        for key, tip in WEATHER_TIPS.items():
            if key.lower() in weather_desc.lower() or weather_desc.lower() in key.lower():
                matched_tip = tip
                break
        if not matched_tip:
            matched_tip = "天气情况一般，建议根据实时情况调整出行安排"
        weather_text = f"{weather_date}，{destination}天气：{weather_desc}，{weather_temp}。{matched_tip}"
        weather_data_for_output = {
            "date": weather_date,
            "weather": weather_desc,
            "temperature": weather_temp,
            "tip": matched_tip
        }
    else:
        weather_text = f"未能获取{destination}的实时天气信息"
        weather_data_for_output = {
            "date": "",
            "weather": "未知",
            "temperature": "",
            "tip": "建议出行前查询当地天气预报"
        }

    # 第二步：搜索景点信息（设了超时，失败也不阻塞）
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
  "weather": {
    "date": "日期",
    "weather": "天气状况",
    "temperature": "温度",
    "tip": "注意事项"
  },
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

当前天气信息：{weather_text}

参考信息：
{info}

请直接输出 JSON 格式的完整行程规划，并将天气信息填入 weather 字段。"""

    try:
        # 第一级，直接解析 JSON
        resp = llm.generate(usr, sys)
        # 第二级， 提取 markdown 代码块
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', resp)
        js = m.group(1) if m else resp
        result = json.loads(js.strip())
        if "weather" not in result or not result["weather"]:
            result["weather"] = weather_data_for_output
        return result
    except Exception as e:
        try:
            # 第三级，找第一个 { 和最后一个 }
            s = resp.find("{")
            e2 = resp.rfind("}")
            if s != -1 and e2 != -1:
                result = json.loads(resp[s:e2 + 1])
                if "weather" not in result or not result["weather"]:
                    result["weather"] = weather_data_for_output
                return result
        except:
            pass
        return {"error": f"生成行程失败: {e}", "raw": resp, "weather": weather_data_for_output}


def format_itinerary_text(data):
    """
    格式化行程为 Markdown
    """
    if "error" in data:
        return f"{data['error']}"
    dest = data.get("destination", "")
    days = data.get("days", 0)
    prefs = data.get("preferences", [])
    weather = data.get("weather", {})
    itin = data.get("itinerary", [])
    pt = "、".join(prefs) if prefs else "无特定偏好"
    lines = [f"**{dest} {days}天行程规划**", f"偏好标签：{pt}", ""]
    if weather:
        w = weather.get("weather", "")
        t = weather.get("temperature", "")
        tip = weather.get("tip", "")
        if w:
            lines.append(f"当前天气：{w} {t}")
        if tip:
            lines.append(f"出行提醒：{tip}")
        lines.append("")
    for day in itin:
        n = day.get("day", 0)
        th = day.get("theme", "")
        su = day.get("summary", "")
        lines.append(f"--- 第{n}天 ---")
        lines.append(f"主题：{th}")
        if su:
            lines.append(f"{su}")
        lines.append("")
        for si, s in enumerate(day.get("spots", []), 1):
            lines.append(f"{si}. {s.get('name', '')}")
            if s.get("description"):
                lines.append(f"   {s['description']}")
            if s.get("duration"):
                lines.append(f"   时长: {s['duration']}")
            if s.get("tips"):
                lines.append(f"   提示: {s['tips']}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    d = generate_itinerary("北京", 3, ["经典", "美食"])
    if "error" in d:
        print(f"失败: {d['error']}")
    else:
        print(format_itinerary_text(d))

