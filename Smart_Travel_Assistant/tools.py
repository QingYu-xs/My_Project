import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
# 导入时区映射关系和星期映射关系
from mapping_relation import CITY_TIMEZONE_MAP, WEEK_MAP
from tavily import TavilyClient
from dotenv import load_dotenv


# 加载 .env 文件中的环境变量
load_dotenv()

def get_city_timezone(city_name: str) -> str:
    """
    根据城市名称获取对应的时区
    :param city_name: 城市
    :return: 时区字符串，如'Asia/Shanghai'
    """
    # 直接匹配
    if city_name in CITY_TIMEZONE_MAP:
        return CITY_TIMEZONE_MAP[city_name]
    # 尝试部分匹配（例如用户输入`北京市`也能匹配到`北京`），遍历城市和对应的时区
    for know_city, timezone in CITY_TIMEZONE_MAP.items():
        if know_city in city_name or city_name in know_city:
            return timezone

    # 默认返回 UTC+8 （中国时区）
    return 'Asia/Shanghai'


def get_current_time(timezone_str: str) -> dict:
    """
    根据时区获取当前城市的日期和时间
    :param timezone_str: 时区字符串
    :return: 包含日期、时间、时区信息的字典
    """
    try:
        # 当前时区
        tz = ZoneInfo(timezone_str)
        now = datetime.now(tz)  # 获取当前时区的当前时间
        time_info = {
            'date': now.strftime('%Y年%m月%d日'),
            'weekday': now.strftime('%A')
        }
        return time_info

    except Exception as e:
        print(f'{e}，时区时间获取失败，使用本地时间！')
        # 如果时区获取失败么使用本地时间
        now = datetime.now()
        time_info = {
            'date': now.strftime('Y%年%m月%d日'),
            'weekday': now.strftime('%A')
        }
        return time_info


def get_weather(city_name: str):
    """
    通过调用 wttr.in API 查询真实的天气信息
    :param city_name: 城市
    :return: 返回当前城市的天气和温度（摄氏度）
    """
    url = f'https://wttr.in/{city_name}?format=j1'
    try:
        # 发送网络请求 获取天气响应数据
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f'状态码{resp.status_code}, 请求失败！')
        else:
            weather_data = resp.json()
            # 当前状况(字典)
            current_condition = weather_data.get('current_condition')[0]
            # 天气状况
            weather_desc = current_condition.get('weatherDesc')[0]['value']
            # 温度
            temperature = current_condition.get('temp_C')
            # 获取城市对应的时区
            timezone_str = get_city_timezone(city_name)
            # 获取当前城市的本地时间
            city_time_info = get_current_time(timezone_str)
            # 返回格式化的天气数据
            weather_res = {
                '📅日期': f'{city_time_info["date"]} {WEEK_MAP[city_time_info["weekday"]]}',
                '📍城市': city_name,
                '🌤️天气': weather_desc,
                '🌡️ 温度': f"{temperature}℃",

            }
            return weather_res

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f'网络请求失败！-- {e}'
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f'数据解析失败！可能是城市名无效！-- {e}'


def get_attraction(city: str, weather: str):
    """
    根据指定城市和天气 使用 Tavily Search API 搜索并返回优化后的旅游景点。
    :param city: 城市名称
    :param weather: 天气
    :return:优化后的旅游景点
    """
    # 1.从环境变量中读取PAI密钥
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        return '错误：未配置TAVILY_API_KEY环境变量'
    # 2.初始化Tavily客户端
    tavily_client = TavilyClient(api_key=api_key)

    # 3.构造一个精确的查询
    query = f"`{city}`在 `{weather}`天气下最值得去的旅游景点继推荐理由"
    try:
        # 4. 调用API，include_answer=True会返回一个综合性的回答
        resp = tavily_client.search(query=query, search_depth='basic', include_answer=True)
        # 5. Tavily返回的结果已经非常干净，可以直接使用
        if resp.get('answer'):
            return resp['answer']
        # 如果没有综合性的回，则格式化原始结果
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
    :param destination: 目的地城市
    :param days: 旅行天数
    :param budget_level: 预算等级（经济/中等/豪华）
    :return: 预算详情
    """
    # 各地消费水平基准数据（每天）
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

    city_costs = cost_data.get(destination, cost_data['北京'])  # 默认北京
    daily_cost = city_costs.get(budget_level, 500)

    budget = {
        '住宿': daily_cost * 0.4 * days,
        '餐饮': daily_cost * 0.3 * days,
        '交通': daily_cost * 0.2 * days,
        '门票': daily_cost * 0.1 * days,
        '总计': daily_cost * days
    }

    return budget


# 将所有工具函数放到一个字典，方便后续调用
available_tools = {
    'get_weather': get_weather,
    'get_attraction': get_attraction,
    'calculate_travel_budget': calculate_travel_budget
}


# 测试代码
if __name__ == '__main__':
    # 测试不同城市的天气和时间
    test_cities = ['北京', '东京', '纽约', '伦敦', '上海']
    for _city in test_cities:
        print("=" * 75)
        result_weather = get_weather(_city)
        print(result_weather)
        print()
        result_attraction = get_attraction(result_weather['📍城市'], result_weather['🌤️天气'])
        print(result_attraction)
        print(calculate_travel_budget(result_weather['📍城市'], 7))


