"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException
from ...models.schemas import (
    TripRequests,
    TripPlanResponse,
    ErrorResponse
)
# from ...agents.trip_planner_agent import get_trip_planner_agent


router = APIRouter(prefix="/trip", tags=["旅行规划"])

@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求，生成详细的旅行计划"
)
async def plan_trip(request: TripRequests):
    """
    生成旅行计划
    :param request:旅行请求参数
    :return: 旅行响应计划
    """
    try:
        print(f"\n{'=' * 60}")
        print(f"收到旅行规划请求：")
        print(f"城市：{request.city}")
        print(f"日期：{request.start_date} - {request.end_date}")
        print(f"天数：{request.travel_days}")
        print(f"\n{'=' * 60}")

        # 获取Agent实例
    except:
        pass







