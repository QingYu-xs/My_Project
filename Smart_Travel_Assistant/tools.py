import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from mapping_relation import CITY_TIMEZONE_MAP, WEEK_MAP
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

def get_city_timezone(city_name: str) -> str:
    """
    根据城市名称获取对应的时区
    优先精确匹配，其次模糊匹配，最后兜底 UTC+8
    :param city_name: 城市名称
    :return: 时区字符串，如 'Asia/Shanghai'
    """
    # 第一步：精确匹配
    if city_name in CITY_TIMEZONE_MAP:
        return CITY_TIMEZONE_MAP[city_name]
    # 第二步：模糊匹配（"北京市" 也能匹配到 "北京"）
    for know_city, timezone in CITY_TIMEZONE_MAP.items():
        if know_city in city_name or city_name in know_city:
            return timezone
    # 第三步：默认返回中国时区
    return 'Asia/Shanghai'


def get_current_time(timezone_str: str) -> dict:
    """
    根据时区获取当前城市的本地日期和时间
    时区查询失败时自动降级使用本地时间
    :param timezone_str: 时区字符串
    :return: 包含日期和星期的字典
    """
    try:
        tz = ZoneInfo(timezone_str)
        now = datetime.now(tz)
        return {
            'date': now.strftime('%Y年%m月%d日'),
            'weekday': now.strftime('%A')
        }
    except Exception as e:
        print(f'{e}，时区时间获取失败，使用本地时间！')
        now = datetime.now()
        return {
            'date': now.strftime('%Y年%m月%d日'),
            'weekday': now.strftime('%A')
        }


def get_weather(city_name: str):
    """
    通过 wttr.in 免费 API 查询实时天气
    :param city_name: 城市名
    :return: 结构化的天气信息字典
    """
    url = f'https://wttr.in/{city_name}?format=j1'
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            print(f'状态码{resp.status_code}, 请求失败！')
            return None
        weather_data = resp.json()
        current_condition = weather_data.get('current_condition')[0]
        weather_desc = current_condition.get('weatherDesc')[0]['value']
        temperature = current_condition.get('temp_C')
        timezone_str = get_city_timezone(city_name)
        city_time_info = get_current_time(timezone_str)

        return {
            '日期': f'{city_time_info["date"]} {WEEK_MAP[city_time_info["weekday"]]}',
            '城市': city_name,
            '天气': weather_desc,
            '温度': f"{temperature}℃",
        }
    except requests.exceptions.RequestException as e:
        return f'网络请求失败--{e}'
    except (KeyError, IndexError) as e:
        return f'数据解析失败！可能是城市名无效！--{e}'


def get_attraction(city: str, weather: str):
    """
    根据城市和天气，用 Tavily 搜索引擎查找推荐的旅游景点
    :param city: 城市名称
    :param weather: 天气状况
    :return: 优化后的旅游景点推荐
    """
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        return '错误：未配置TAVILY_API_KEY环境变量'
    tavily_client = TavilyClient(api_key=api_key)
    # 构建精确查询：把天气条件带上，让搜索更相关
    query = f"`{city}`在`{weather}`天气下最值得去的旅游景点及推荐理由"
    try:
        resp = tavily_client.search(query=query, search_depth='basic', include_answer=True)
        if resp.get('answer'):
            return resp['answer']
        formatted_res = []
        for res in resp.get('result', []):
            formatted_res.append(f"-{res['title']}: {res['content']}")
        if not formatted_res:
            return '抱歉，没有找到相关的旅游景点推荐'
        return '根据搜索结果，为您找到以下信息：\n' + '\n'.join(formatted_res)
    except Exception as e:
        return f"错误：执行Tavily搜索时出错--{e}"


def calculate_travel_budget(destination: str, days: int = 7, budget_level: str = "中等") -> dict:
    """
    根据目的地、天数和预算等级计算旅行预算
    覆盖 25+ 城市，分经济/中等/豪华三档，按固定比例分配
    :param destination: 目的地城市
    :param days: 旅行天数
    :param budget_level: 预算等级（经济/中等/豪华）
    :return: 预算详情（住宿/餐饮/交通/门票/总计）
    """
    # 各城市日均消费基准（元/天）
    cost_data = {
        # 一线城市
        '北京': {'经济': 300, '中等': 600, '豪华': 1500},
        '上海': {'经济': 350, '中等': 700, '豪华': 1800},
        '广州': {'经济': 280, '中等': 550, '豪华': 1300},
        '深圳': {'经济': 300, '中等': 600, '豪华': 1500},
        # 新一线城市
        '成都': {'经济': 200, '中等': 450, '豪华': 1200},
        '重庆': {'经济': 200, '中等': 400, '豪华': 1000},
        '杭州': {'经济': 250, '中等': 550, '豪华': 1400},
        '武汉': {'经济': 220, '中等': 450, '豪华': 1100},
        '西安': {'经济': 200, '中等': 400, '豪华': 1000},
        '南京': {'经济': 250, '中等': 500, '豪华': 1200},
        '苏州': {'经济': 250, '中等': 500, '豪华': 1200},
        '长沙': {'经济': 180, '中等': 380, '豪华': 900},
        '天津': {'经济': 220, '中等': 450, '豪华': 1100},
        '郑州': {'经济': 180, '中等': 380, '豪华': 900},
        # 热门旅游城市
        '厦门': {'经济': 280, '中等': 550, '豪华': 1300},
        '青岛': {'经济': 250, '中等': 500, '豪华': 1200},
        '大连': {'经济': 230, '中等': 480, '豪华': 1100},
        '三亚': {'经济': 350, '中等': 800, '豪华': 2000},
        '昆明': {'经济': 200, '中等': 400, '豪华': 1000},
        '丽江': {'经济': 200, '中等': 450, '豪华': 1100},
        '大理': {'经济': 180, '中等': 400, '豪华': 1000},
        '桂林': {'经济': 180, '中等': 380, '豪华': 900},
        # 西北/东北
        '哈尔滨': {'经济': 200, '中等': 400, '豪华': 1000},
        '沈阳': {'经济': 200, '中等': 420, '豪华': 1000},
        '兰州': {'经济': 180, '中等': 350, '豪华': 800},
        '乌鲁木齐': {'经济': 200, '中等': 400, '豪华': 1000},
        # 特别行政区
        '香港': {'经济': 500, '中等': 1200, '豪华': 3000},
        '澳门': {'经济': 450, '中等': 1000, '豪华': 2500},
    }

    # 如果目的地在字典中找不到，默认用北京的消费水平
    city_costs = cost_data.get(destination, cost_data['北京'])
    daily_cost = city_costs.get(budget_level, 500)

    # 按固定比例分配：住宿40%、餐饮30%、交通20%、门票10%
    budget = {
        '住宿': round(daily_cost * 0.4 * days, 2),
        '餐饮': round(daily_cost * 0.3 * days, 2),
        '交通': round(daily_cost * 0.2 * days, 2),
        '门票': round(daily_cost * 0.1 * days, 2),
        '总计': daily_cost * days
    }
    return budget


# 工具注册表：统一注册所有工具函数
# 新增工具只需在这里加一行，main.py 无需改动
available_tools = {
    'get_weather': get_weather,
    'get_attraction': get_attraction,
    'calculate_travel_budget': calculate_travel_budget
}


# 测试代码：验证各工具函数的可用性
if __name__ == '__main__':
    test_cities = ['北京', '东京', '纽约', '伦敦', '上海']
    for _city in test_cities:
        print("=" * 75)
        result_weather = get_weather(_city)
        print(result_weather)
        print()
        result_attraction = get_attraction(result_weather['城市'], result_weather['天气'])
        print(result_attraction)
        print(calculate_travel_budget(result_weather['城市'], 7))