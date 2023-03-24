from sqlalchemy.orm import Session
from . import models
from models import *
from fastapi import HTTPException


# 具体变量的含义参见 models.py
def add_manager(db: Session, username: str, hashed_password: str):
    manager_dict = {
        "username": username,
        "HashedPassword": hashed_password,
    }
    manager = Managers(**manager_dict)
    db.add(manager)
    db.commit()
    db.refresh(manager)


# 按用户名查找
def get_manager(db: Session, username: str):
    return db.query(Managers).filter(Managers.username == username).first()


def add_campus(db: Session, name: str):
    campus_dict = {
        "CampusName": name,
        "CanteenNum": 0
    }
    campus = Campus(**campus_dict)
    db.add(campus)
    db.commit()
    db.refresh(campus)


def add_campus_canteen_num(db: Session, canteen_id: int):
    campus = get_campus_by_id(db, canteen_id)
    campus.CanteenNum += 1


# 可以判断餐厅是否存在
def get_campus_by_name(db: Session, name: str):
    return db.query(Campus).filter(Campus.CampusName == name).first()


def get_campus_by_id(db: Session, campus_id: int):
    return db.query(Campus).filter(Campus.id == campus_id).first()


def add_canteen(db: Session, canteen_name: str, campus_id: int):
    canteen_dict = {
        "CanteenName": canteen_name,
        "CampusID": campus_id,
        "LevelNum": 0,
        "id": str(campus_id) + str(get_campus_by_id(db, campus_id).CanteenNum + 1)
    }
    add_campus_canteen_num(db, campus_id)
    canteen = Canteens(**canteen_dict)
    db.add(canteen)
    db.commit()
    db.refresh(canteen)


# 可验证餐厅名
def get_canteen_by_name(db: Session, name: str):
    return db.query(Canteens).filter(Canteens.CanteenName == name).first()


def add_level(db: Session, canteen_id: str, level: int):
    if level > 0:
        a = "0"
    else:
        a = "1"
        level = -level
    level_dict = {
        "id": canteen_id + a + str(level),
        "WindowNum": 0
    }
    canteen = db.query(Canteens).filter(Canteens.id == canteen_id).first()
    canteen.LevelNum += 1
    level_x = Levels(**level_dict)
    db.add(level_x)
    db.commit()
    db.refresh(level_x)
    return canteen_id + a + str(level)


# level_id 参数来源 add_level
def add_window(db: Session, name: str, level_id: str, window: int):
    window_dict = {
        "WindowName": name,
        "id": level_id + str(window),
        "DishNum": 0
    }
    window_x = Windows(**window_dict)
    db.add(window_x)
    db.commit()
    db.refresh(window_x)
    return level_id + str(window)


def get_window(db: Session, canteen_id: str, level: int, window: int):
    return db.query(Windows).filter(Windows.id == (canteen_id + str(level) + str(window))).first()


def get_canteen(db: Session, canteen_name: str):
    return db.query(Canteens).filter(Canteens.CanteenName == canteen_name).first()


# window_id 参数来源 add_window或get_window
def make_dish_id(db: Session, window_id: str):
    a = db.query(Windows).filter(Windows.id == window_id).first()
    a.DishNum += 1
    return window_id + str(a.DishNum)


# dish_id参数来源 make_dish_id
def add_dish(db: Session, manager_id: int,
             name: str, morning: bool, noon: bool, night: bool, canteen_id: str, muslim: bool, photos: str,
             spare_photos: str, dish_id: str):
    dish_dict = {
        "DishName": name,
        "morning": morning,
        "noon": noon,
        "night": night,
        "CanteenID": canteen_id,
        "Muslim": muslim,
        "photos": photos,
        "SparePhotos": spare_photos,
        "manager": manager_id,
        "id": dish_id
    }
    dish = Dishes(**dish_dict)
    db.add(dish)
    db.commit()
    db.refresh(dish)






def search_dish(db: Session, context: str, page: int, num: int):
    return
# def get_user(db: Session, username: str):
#     return db.query(User).filter(User.name == username).first()
