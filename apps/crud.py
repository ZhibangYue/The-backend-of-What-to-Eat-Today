from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from .database import *


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


# 校区函数
# 增加校区
def add_campus(db: Session, name: str):
    campus_dict = {
        "campus_name": name,
        "canteen_num": 0
    }
    campus = Campus(**campus_dict)
    db.add(campus)
    db.commit()
    db.refresh(campus)


# 校区名查校区
def get_campus_by_name(db: Session, name: str):
    return db.query(Campus).filter(Campus.campus_name == name).first()


# 校区id查校区
def get_campus_by_id(db: Session, campus_id: int):
    return db.query(Campus).filter(Campus.campus_id == campus_id).first()


# 餐厅函数
# 对餐厅表进行添加
def add_canteen(db: Session, canteen_message: CanteenMessage):
    campus = get_campus_by_id(db, canteen_message.campus_id)
    campus.canteen_num = campus.canteen_num + 1
    db.commit()
    canteen_id = str(canteen_message.campus_id) + str(campus.canteen_num)
    canteen_dict = {
        "canteen_name": canteen_message.canteen_name,
        "campus_id": canteen_message.campus_id,
        "level_num": canteen_message.level_num,
        "canteen_id": canteen_id
    }

    canteen = Canteens(**canteen_dict)
    db.add(canteen)
    db.commit()
    db.refresh(canteen)


# 餐厅名查餐厅
def get_canteen_by_name(db: Session, name: str):
    return db.query(Canteens).filter(Canteens.canteen_name == name).first()


# 按页获取餐厅
def get_canteens(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Canteens).offset(skip).limit(limit).all()


# 按校区获取餐厅
def get_canteens_filter_campus(db: Session, page: int, limit: int, campus_id: int):
    skip = (page - 1) * limit
    return db.query(Canteens).filter(Canteens).filter(Canteens.campus_id == campus_id).offset(skip).limit(limit).all()


# 获取所有餐厅
def get_all_canteens(db: Session):
    return db.query(Canteens).all()


# 对层数表进行添加
def add_level(db: Session, canteen_id: str, level: int, window_num: int):
    if level > 0:
        a = "0"
    else:
        a = "1"
        level = -level
    level_dict = {
        "level_id": canteen_id + a + str(level),
        "level": level,
        "window_num": window_num,
        "canteen_id": canteen_id
    }
    # canteen = db.query(Canteens).filter(Canteens.id == canteen_id).first()
    # canteen.level_num += 1
    level_x = Levels(**level_dict)
    db.add(level_x)
    db.commit()
    db.refresh(level_x)


# level_id 参数来源 add_level

# 对窗口表进行添加
def add_window(db: Session, name: str, level_id: str, window: int):
    if window < 10:
        num = "0" + str(window)
    else:
        num = str(window)
    window_id = level_id + num
    window_dict = {
        "window_name": name,
        "window_id": window_id,
        "dish_num": 0,
        "level_id": level_id,
        "window": window
    }
    window_x = Windows(**window_dict)
    db.add(window_x)
    db.commit()
    db.refresh(window_x)


# return level_id + str(window)


def get_window(db: Session, canteen_id: str, level: int, window: int):
    if level > 0:
        a = "0"
        level = level
    else:
        a = "1"
        level = level
    if window < 10:
        num = "0" + str(window)
    else:
        num = str(window)
    window_id = canteen_id + a + str(level) + num
    return db.query(Windows).filter(Windows.window_id == window_id).first()


def get_canteen(db: Session, canteen_name: str):
    return db.query(Canteens).filter(Canteens.canteen_name == canteen_name).first()


# window_id 参数来源 add_window或get_window
def make_dish_id(db: Session, window_id: str):
    a = db.query(Windows).filter(Windows.window_id == window_id).first()
    a.dish_num = a.dish_num + 1
    db.commit()
    if a.dish_num < 10:
        num = "00" + str(a.dish_num)
    elif a.dish_num < 100:
        num = "0" + str(a.dish_num)
    else:
        num = str(a.dish_num)
    return str(window_id) + num


# dish_id参数来源 make_dish_id
def add_dish(db: Session, dish_message: DishMessage):
    window = get_window(db, dish_message.canteen_id, dish_message.level, dish_message.window)
    dish_id = make_dish_id(db, window.window_id)
    dish_dict = {
        "dish_id": dish_id,
        "dish_name": dish_message.name,
        "morning": dish_message.morning,
        "noon": dish_message.noon,
        "night": dish_message.night,
        "canteen_id": dish_message.canteen_id,
        "window_id": window.window_id,
        "muslim": dish_message.muslim,
        "photos": dish_message.photos,
        "spare_photos": dish_message.spare_photos,
        "level": dish_message.level,
        "window": dish_message.window,
        "price": dish_message.price,
        "size": dish_message.size
    }
    dish = Dishes(**dish_dict)
    db.add(dish)
    db.commit()
    db.refresh(dish)


def search_dish(db: Session, context: str, page: int, num: int):
    return


def get_dishes_page(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Dishes).offset(skip).limit(limit).all()


def get_dishes_filter_canteen(db: Session, page: int, limit: int, canteen_id: str):
    skip = (page - 1) * limit
    return db.query(Dishes).filter(Dishes.canteen_id == canteen_id).offset(skip).limit(limit).all()


def get_dishes_filter_morning(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Dishes).filter(Dishes.morning == 1).offset(skip).limit(limit).all()


def get_dishes_filter_noon(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Dishes).filter(Dishes.noon == 1).offset(skip).limit(limit).all()


def get_dishes_filter_night(db: Session, page: int, limit: int):
    skip = (page - 1) * limit
    return db.query(Dishes).filter(Dishes.night == 1).offset(skip).limit(limit).all()


# def get_canteens(db: Session, page: int, limit: int):


def get_campus(db: Session):
    return db.query(Campus).all()


def get_level(db: Session, level: int):
    return db.query(Levels).filter(Levels.level == level).first()


def get_levels_by_canteen_id(db: Session, canteen_id: str):
    return db.query(Levels).filter(Levels.canteen_id == canteen_id).all()


def get_windows_by_level_id(db: Session, level_id: str):
    return db.query(Windows).filter(Windows.level_id == level_id).all()


def get_canteen_by_canteen_id(db: Session, canteen_id: str):
    return db.query(Canteens).filter(Canteens.canteen_id == canteen_id).first()


def get_dishes_by_window_id(db: Session, window_id: str):
    return db.query(Dishes).filter(Dishes.window_id == window_id).all()


def get_dish_by_dish_id(db: Session, dish_id: str):
    return db.query(Dishes).filter(Dishes.dish_id == dish_id).all()


def get_window_by_window_id(db: Session, window_id: str):
    return db.query(Windows).filter(Windows.window_id == window_id).first()


def get_level_by_level_id(db: Session, level_id: str):
    return db.query(Levels).filter(Levels.level_id == level_id).first()
