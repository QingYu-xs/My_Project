"""数据模型定义"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from pydantic import ConfigDict

"""
Field 函数是Pydantic库中的一个重要工具，主要作用如下：
1.字段约束和验证：可以设置字段的约束条件，如 必填、默认值、长度限制等
2.文档说明：为字段提供描述信息和示例，便于API文档生成
3.类型提示增强：配合Pydantic的类型检查机制，提供更严格的运行时验证
"""


# ---- 请求模型 ----
class TripRequests(BaseModel):
    """旅行规划请求"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "city": "北京",
                "start_date": "2026-07-22",
                "end_date": "2026-07-22",
                "traval_days": 3,
                "transportation": '高铁',
                "accommodation": '经济型酒店',
                "preferences": ["历史文化", "拍照"],
                "free_text_input": "希望多安排一些博物馆"
            }
        }
    )

    city: str = Field(..., description='目的地城市', examples=['北京'])  # ... ：表示盖该字段为必填项
    start_date: str = Field(..., description='开始日期 YYYY-MM-DD', examples=['2026-07-22'])
    end_date: str = Field(..., description='结束日期 YYYY-MM-DD', examples=['2026-07-25'])
    travel_days: int = Field(..., description='旅行天数', ge=1, le=3, examples=[3])  # ge: 大于等于， le: 小于等于
    transportation: str = Field(..., description='交通方式', examples=['公共交通'])
    accommodation: str = Field(..., description='住宿偏好', examples=['经济型酒店', '民宿'])
    preferences: List[str] = Field(default=[], description='旅行偏好标签', examples=['历史文化', '美食'])  # default=[] 该字段默认值为 []
    free_text_input: Optional[str] = Field(default='', description='额外要求', examples=['希望多安排一些博物馆'])


class POISearchRequests(BaseModel):
    """POI搜索请求"""
    keyboards: str = Field(..., description='搜索的关键词', examples=["故宫"])
    city: str = Field(..., description="城市", examples=["北京"])
    city_limit: bool = Field(default=True, description='是否限制在城市范围内')


class RouteRequests(BaseModel):
    """路线规划请求"""
    origin_address: str = Field(..., description="起始地址", examples=["北京市朝阳区阜通东大街6号"])
    destination_address: str = Field(..., description='重点地址', examples=["北京市海淀区上地十街10号"])
    origin_city: Optional[str] = Field(default=None, description="起点城市")
    destination_city: Optional[str] = Field(default=None, description="终点城市")
    route_type: str = Field(default="walking", description="路线类型: walking/driving/transit")


# ---- 响应模型 ----

class Location(BaseModel):
    """地理位置"""
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")


class Attraction(BaseModel):
    """景点信息"""
    name: str = Field(..., description="景点名称")
    address: str = Field(..., description='地址')
    location: Location = Field(..., description="经纬度坐标")
    visit_duration: int = Field(..., description="建议游览时间（分钟）")
    description: str = Field(..., description="景点描述")
    category: Optional[str] = Field(default="景点", description="景点类别")
    rating: Optional[float] = Field(default_factory=list, description="景点图片url列表")
    poi_id: Optional[str] = Field(default="", description="POI ID")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    ticket_price: int = Field(default=0, description="门票价格（元）")


class Meal(BaseModel):
    """餐饮信息"""
    type: str = Field(..., description="餐饮类型：breakfast/lunch/snack")
    name: str = Field(..., description="餐饮名称")
    address: Optional[str] = Field(default=None, description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度坐标")
    description: Optional[str] = Field(default=None, description="描述")
    estimated_cost: int = Field(default=0, description="预估费用（元）")


class Hotel(BaseModel):
    """餐饮信息"""
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Optional[Location] = Field(default=None, description="酒店位置")
    price_range: str = Field(default="", description="价格范围")
    rating: str = Field(default="", description="评分")
    distance: str = Field(default="", description="距离经典的位置")
    type: str = Field(default="", description="酒店类型")
    estimated_cost: int = Field(default=0, description="预估费用(元/晚)")


class DayPlan(BaseModel):
    """单日行程"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_index: int = Field(..., description="第几天（从0开始）")
    description: str = Field(..., description="当日行程描述")
    transportation: str = Field(..., description="交通方式")
    accommodation: str = Field(..., description="住宿")
    hotel: Optional[Hotel] = Field(default=None, description="推荐酒店")
    attractions: List[Attraction] = Field(default=[], description="景点列表")
    meals: List[Meal] = Field(default=[], description="餐饮列表")


class WeatherInfo(BaseModel):
    """天气信息"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_weather: str = Field(default="", description="白天天气")
    night_weather: str = Field(default="", description="夜间天气")
    day_temp: Union[int, str] = Field(default=0, description="白天温度")
    night_temp: Union[int, str] = Field(default=0, description="夜间温度")
    wind_direction: str = Field(default="", description="风向")
    wind_power: str = Field(default="", description="风力")

    """
    @field_validator('day_temp', 'night_temp', mode='before') 这个装饰器是 Pydantic 库中用于字段验证的重要工具，它的作用如下：
    作用解释：
    1.字段验证：对 day_temp 和 night_temp 这两个字段进行验证和预处理
    2.预处理模式：mode='before' 表示在数据被赋值给字段之前执行此验证器
    3.数据转换：通常用于将输入的数据转换为期望的格式，比如将字符串温度值转换为整数或处理特殊的温度表示（如"℃"符号）
    在这个天气信息模型中，由于温度可能以不同格式传入（如包含温度单位的字符串），这个验证器会先对输入进行处理，确保最终存储的是符合 Union[int, str] 类型要求的数据。
    """

    @field_validator('day_temp', 'night_temp', mode='before')
    @classmethod
    def parse_temperature(cls, v):
        """解析温度，移除 ℃ 等单位"""
        if isinstance(v, str):
            v = v.replace("℃", '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v


class Budget(BaseModel):
    """预算信息"""
    total_attractions: int = Field(default=0, description="总景点预算（元）")
    total_hotels: int = Field(default=0, description="总酒店预算（元）")
    total_meals: int = Field(default=0, description="总餐饮预算（元）")
    total_transportation: int = Field(default=0, description="交通方式预算（元）")
    total: int = Field(default=0, description="总预算（元）")


class TripPlan(BaseModel):
    """旅行计划"""
    city: str = Field(..., description="目的地城市")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: List[DayPlan] = Field(..., description="每日行程")
    weather_info: List[WeatherInfo] = Field(default=[], description="天气信息")
    overall_suggestions: str = Field(..., description="总体建议")
    budget: Optional[Budget] = Field(default=None, description="预算信息")


class TripPlanResponse(BaseModel):
    """旅行计划响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[TripPlan] = Field(default=None, description="旅行计划数据")


class POIInfo(BaseModel):
    """POI信息"""
    id: str = Field(..., description="POI ID")
    name: str = Field(..., description="名称")
    type: str = Field(..., description="类型")
    address: str = Field(..., description="地址")
    location: Location = Field(..., description="经纬度坐标")
    tel: Optional[str] = Field(default=None, description="电话")


class POISearchResponse(BaseModel):
    """POI搜索响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: List[POIInfo] = Field(default=[], description="POI列表")


class RouteInfo(BaseModel):
    """路线信息"""
    distance: float = Field(..., description="距离(米)")
    duration: int = Field(..., description="时间(秒)")
    route_type: str = Field(..., description="路线类型")
    description: str = Field(..., description="路线描述")


class RouteResponse(BaseModel):
    """路线规划响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[RouteInfo] = Field(default=None, description="路线信息")


class WeatherResponse(BaseModel):
    """天气查询响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: List[WeatherInfo] = Field(default=[], description="天气信息")


# ============ 错误响应 ============

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")




