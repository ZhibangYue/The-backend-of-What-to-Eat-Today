from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from fastapi import HTTPException


# 具体变量的含义参见 models.py
def add_manager(db: Session, username: str, hashed_password: str, permission: bool = False):
    manager_dict = {
        "username": username,
        "hashed_password": hashed_password,
        "permission": permission
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
        "campus_name": name,
        "canteen_num": 0
    }
    campus = Campus(**campus_dict)
    db.add(campus)
    db.commit()
    db.refresh(campus)


def add_campus_canteen_num(db: Session, canteen_id: int):
    campus = get_campus_by_id(db, canteen_id)
    campus.canteen_num += 1


# 可以判断餐厅是否存在
def get_campus_by_name(db: Session, name: str):
    return db.query(Campus).filter(Campus.campus_name == name).first()


def get_campus_by_id(db: Session, campus_id: int):
    return db.query(Campus).filter(Campus.id == campus_id).first()


def add_canteen(db: Session, canteen_name: str, campus_id: int):
    canteen_dict = {
        "canteen_name": canteen_name,
        "campus_id": campus_id,
        "level_num": 0,
        "id": str(campus_id) + str(get_campus_by_id(db, campus_id).canteen_num + 1)
    }
    add_campus_canteen_num(db, int(str(campus_id) + str(get_campus_by_id(db, campus_id).canteen_num + 1)))
    canteen = Canteens(**canteen_dict)
    db.add(canteen)
    db.commit()
    db.refresh(canteen)


# 可验证餐厅名
def get_canteen_by_name(db: Session, name: str):
    return db.query(Canteens).filter(Canteens.canteen_name == name).first()


def add_level(db: Session, canteen_id: str, level: int):
    if level > 0:
        a = "0"
    else:
        a = "1"
        level = -level
    level_dict = {
        "id": canteen_id + a + str(level),
        "window_num": 0
    }
    canteen = db.query(Canteens).filter(Canteens.id == canteen_id).first()
    canteen.level_num += 1
    level_x = Levels(**level_dict)
    db.add(level_x)
    db.commit()
    db.refresh(level_x)
    return canteen_id + a + str(level)


# level_id 参数来源 add_level
def add_window(db: Session, name: str, level_id: str, window: int):
    window_dict = {
        "window_name": name,
        "id": level_id + str(window),
        "dish_num": 0
    }
    window_x = Windows(**window_dict)
    db.add(window_x)
    db.commit()
    db.refresh(window_x)
    return level_id + str(window)


def get_window(db: Session, canteen_id: str, level: int, window: int):
    return db.query(Windows).filter(Windows.id == (canteen_id + str(level) + str(window))).first()


def get_canteen(db: Session, canteen_name: str):
    return db.query(Canteens).filter(Canteens.canteen_name == canteen_name).first()


# window_id 参数来源 add_window或get_window
def make_dish_id(db: Session, window_id: str):
    a = db.query(Windows).filter(Windows.id == window_id).first()
    a.dish_num += 1
    return window_id + str(a.dish_num)


# dish_id参数来源 make_dish_id
def add_dish(db: Session, dish_message: DishMessage):
    dish_dict = {
        "dish_name": dish_message.name,
        "morning": dish_message.morning,
        "noon": dish_message.noon,
        "night": dish_message.night,
        "canteen_id": dish_message.canteen_id,
        "muslim": dish_message.muslim,
        "photos": dish_message.photos,
        "spare_photos": dish_message.spare_photos,
        "manager": dish_message.manager_id,
        "id": dish_message.dish_id

    }
    dish = Dishes(**dish_dict)
    db.add(dish)
    db.commit()
    db.refresh(dish)


def search_dish(db: Session, context: str, page: int, num: int):
    return
# def get_user(db: Session, username: str):
#     return db.query(User).filter(User.name == username).first()
