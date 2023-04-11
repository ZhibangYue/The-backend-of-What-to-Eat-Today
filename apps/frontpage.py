from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from .crud import *
from .background import *

frontpage = APIRouter()


# 交互文档登录

@frontpage.get("/dishes", status_code=200, response_description="got successfully", summary="获取菜品信息")
async def get_this_dishes(db: Session = Depends(get_db), level: int = 1, canteen_id: str = '0'):
    dishes = get_dishes_by_canteen_and_level(db, canteen_id, level)
    dishes_information = get_dish_message(db, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# @frontpage.get("/draw_dish", status_code=200, response_description="got successfully", summary="随机抽取菜品")
# async def draw_dish(db: Session = Depends(get_db), canteen_id: str = '0', timex: str = '0'):
#
#     return random_draw(db, canteen_id, timex)

@frontpage.get("/draw_dishes", status_code=200, response_description="got successfully", summary="随机抽取菜品")
async def draw_dish(db: Session = Depends(get_db), canteen_id: str = '01', timex: str = '0'):
    dishes = get_dishes_by_name_and_time(db, canteen_id, timex)
    dishes_information = get_dish_message(db, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


@frontpage.get("/likes", status_code=200, response_description="got successfully", summary="查询点赞状态")
async def get_like_status():
    return 0
