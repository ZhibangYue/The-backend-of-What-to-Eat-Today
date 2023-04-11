from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from .crud import *
import datetime
from .background import *

frontpage = APIRouter()


# 交互文档登录

@frontpage.get("/dishes", status_code=200, response_description="got successfully", summary="获取菜品信息")
async def get_this_dishes(openid: int, db: Session = Depends(get_db), level: int = 1, canteen_id: str = '0'):
    dishes = get_dishes_by_canteen_and_level(db, canteen_id, level)
    dishes_information = get_dish_message(db, openid, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# @frontpage.get("/draw_dish", status_code=200, response_description="got successfully", summary="随机抽取菜品")
# async def draw_dish(db: Session = Depends(get_db), canteen_id: str = '0', timex: str = '0'):
#
#     return random_draw(db, canteen_id, timex)

@frontpage.get("/draw_dishes", status_code=200, response_description="got successfully", summary="随机抽取菜品")
async def draw_dish(openid: int, db: Session = Depends(get_db), canteen_id: str = '01', timex: str = '0'):
    dishes = get_dishes_by_name_and_time(db, canteen_id, timex)
    dishes_information = get_dish_message(db, openid, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


@frontpage.get("/likes", status_code=200, response_description="got successfully", summary="查询单个菜品点赞")
async def get_like_status(dish_id: str, openid: int, db: Session = Depends(get_db)):
    like = get_like(db, openid, dish_id)
    dish = get_dish_by_dish_id(db, dish_id)
    if not like:
        return {"message": "success", "detail": "获取成功", "data": {"like_information": {
            "like": False,
            "time": None,
            "like_num": dish.likes
        }}}
    if like:
        return {"message": "success", "detail": "获取成功", "data": {"like_information": {
            "like": True,
            "time": like.date_,
            "like_num": dish.likes
        }}}


@frontpage.put("/likes", status_code=200, response_description="changed successfully", summary="点赞或取消")
async def chang_like_status(dish_id: str, openid: int, db: Session = Depends(get_db)):
    like = get_like(db, openid, dish_id)
    dish = get_dish_by_dish_id(db, dish_id)
    if not like:
        add_like(db, openid, dish_id)
        new_like = get_like(db, openid, dish_id)
        dish.likes = dish.likes + 1
        db.commit()
        db.refresh(dish)
        return {"message": "success", "detail": "点赞成功", "data": {"like_information": {
            "like": True,
            "time": new_like.date_,
            "like_num": dish.likes
        }}}
    if like:
        dish.likes = dish.likes - 1
        db.commit()
        db.refresh(dish)
        db.delete(like)
        db.commit()
        return {"message": "success", "detail": "取消点赞成功", "data": {"like_information": {
            "like": False,
            "time": None,
            "like_num": dish.likes
        }}}
