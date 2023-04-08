import random
import time

import aiofiles
from fastapi import FastAPI, HTTPException, Depends, Form, status, APIRouter, File, UploadFile, Body
from passlib.context import CryptContext
from .database import SessionLocal
from .crud import *
from .schemas import *
from typing import List, Optional, Union
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

background = APIRouter()

# 加密解密的辅助函数
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 明文密码哈希加密

def hash_password(password: str):
    return pwd_context.hash(password)


# 验证密码
def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


# 连接数据库的辅助函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 验证用户的辅助函数
def authenticate_manager(username: str, password: str, db: Session = Depends(get_db)):
    user = get_manager(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# 定义Token 相关常量

# 密钥
SECRET_KEY = "b81a5447dba59bda81233e037a5f4d6232f0f84a4ca8633c10ce7b57fe916a2b"

# 加密算法
ALGORITHM = "HS256"

# Token过期时间
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 依赖token登录的url
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="./token")


# 创建生成新地访问令牌的工具函数
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 解码并校验接收到的令牌，然后，返回当前用户。
async def get_current_manager(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    manager = get_manager(db, username=token_data.username)
    if manager is None:
        raise credentials_exception
    return manager


async def get_current_active_manager(current_manager: ManagerMessage = Depends(get_current_manager)):
    if not current_manager.permission:
        raise HTTPException(status_code=400, detail="权限不足")
    return current_manager


@background.get("/")
def read_root():
    return {"Hello": "World"}


# 管理员接口

# 添加新管理员（拥有超级管理员权限才可使用）
@background.post("/managers/signin", status_code=201, response_description="created successfully", summary="注册")
async def signup(current_manager: ManagerMessage = Depends(get_current_active_manager),
                 username: str = Form(..., max_length=20),
                 password: str = Form(..., min_length=8, max_lengh=20),
                 db=Depends(get_db)):
    if get_manager(db, username):
        raise HTTPException(detail="用户名已存在", status_code=400)
    hashed_password = hash_password(password)
    add_manager(db, username, hashed_password)
    return {"message": "success", "detail": "注册成功", "data": {}}


# 交互文档登录

@background.post("/token", status_code=200, response_model=Token, response_description="login successfully",
                 summary="交互文档登录")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    manager = authenticate_manager(form_data.username, form_data.password, db)
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": manager.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 登录
@background.post("/managers/login", status_code=200, response_model=Token, response_description="login successfully",
                 summary="登录")
async def login_for_access_token(form_data: PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    manager = authenticate_manager(form_data.username, form_data.password, db)
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": manager.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 删除管理员（拥有超级管理员权限才可使用）
@background.delete("/managers", status_code=200, response_description="deleted successfully",
                   summary="删除管理员")
async def delete_current_manager(username: str, db: Session = Depends(get_db),
                                 current_manager: ManagerMessage = Depends(get_current_active_manager)):
    manager = get_manager(db, username)
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名不存在"
        )
    if manager.permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限不足"
        )
    db.delete(manager)
    db.commit()
    return {"message": "success", "detail": "删除成功", "data": {}}


# 餐厅管理接口

# 增加新餐厅
@background.post("/canteens", status_code=201, response_description="added successfully", summary="增加新餐厅")
async def add_new_canteens(canteen_message: CanteenMessage, db: Session = Depends(get_db),
                           current_manager: ManagerMessage = Depends(get_current_manager)
                           ):
    canteen = get_canteen_by_name(db, canteen_message.canteen_name)
    if canteen:
        raise HTTPException(status_code=400, detail="餐厅已存在")
    add_canteen(db, canteen_message)
    new_canteen = get_canteen_by_name(db, canteen_message.canteen_name)
    for level in canteen_message.levels:
        add_level(db, new_canteen.canteen_id, level.level, level.windows_num)
        for window in level.windows_information:
            new_level = get_level(db, level.level)
            add_window(db, window.windows_name, new_level.level_id, window.windows)
    return {"message": "success", "detail": "添加成功", "data": {}}


# 修改餐厅
@background.put("/canteens", status_code=200, response_description="edited successfully", summary="修改餐厅")
async def edit_canteens(canteen_message: EditCanteenMessage, db: Session = Depends(get_db),
                        current_manager: ManagerMessage = Depends(get_current_manager)):
    canteen = get_canteen_by_canteen_id(db, canteen_message.canteen_id)
    if not canteen:
        raise HTTPException(status_code=400, detail="餐厅不存在")
    canteen.canteen_name = canteen_message.canteen_name
    canteen.level_num = canteen_message.level_num
    db.commit()
    db.refresh(canteen)

    return {"message": "success", "detail": "修改成功", "data": {}}


# 按页获取餐厅信息


@background.get("/canteens", status_code=200, response_description="got successfully", summary="获取餐厅信息")
async def get_canteens_by_page(page: int, limit: int, db: Session = Depends(get_db),
                               current_manager: ManagerMessage = Depends(get_current_manager),
                               ):
    canteens = get_canteens(db, page, limit)
    canteens_information = []
    levels_information = []
    for canteen in canteens:
        levels = get_levels_by_canteen_id(db, canteen.canteen_id)
        for level in levels:
            windows = get_windows_by_level_id(db, level.level_id)
            windows_information = [{
                "windows_name": window.window_name,
                "windows_id": window.window_id
            } for window in windows]
            level_information = {
                "level_id": level.level_id,
                "windows_num": level.window_num,
                "windows_information": windows_information,
            }
            levels_information.append(level_information)
        canteen_information = {"canteen_name": canteen.canteen_name,
                               "canteen_id": canteen.canteen_id,
                               "level_num": canteen.level_num,
                               "campus": {
                                   "campus_name": get_campus_by_id(db, canteen.campus_id).campus_name,
                                   "campus_id": canteen.campus_id,
                               },
                               "levels_information": levels_information}
        canteens_information.append(canteen_information)
    return {"message": "success", "detail": "获取成功", "data": {"canteens_information": canteens_information}}


# 删除餐厅
@background.delete("/canteens", status_code=200, response_description="deleted successfully", summary="删除餐厅")
async def delete_current_canteen(canteen_id: str, db: Session = Depends(get_db),
                                 current_manager: ManagerMessage = Depends(get_current_manager)):
    canteen = get_canteen_by_canteen_id(db, canteen_id)
    if not canteen:
        raise HTTPException(status_code=400, detail="餐厅不存在")
    levels = get_levels_by_canteen_id(db, canteen_id)
    for level in levels:
        windows = get_windows_by_level_id(db, level.level_id)
        for window in windows:
            dishes = get_dishes_by_window_id(window.window_id)
            for dish in dishes:
                db.delete(dish)
                db.commit()
            db.delete(window)
            db.commit()
        db.delete(level)
        db.commit()
    db.delete(canteen)
    db.commit()
    return {"message": "success", "detail": "删除成功", "data": {}}


# 获取校区与其id的对应序列
@background.get("/campus", status_code=200, response_description="got successfully", summary="获取校区与其id的对应序列")
async def get_canteens_campus(db: Session = Depends(get_db),
                              current_manager: ManagerMessage = Depends(get_current_manager)):
    campuses = get_campus(db)
    campuses_information = []
    for campus in campuses:
        campus_information = {
            "campus_name": campus.campus_name,
            "campus_id": campus.campus_id
        }
        campuses_information.append(campus_information)
    return {"message": "success", "detail": "获取成功", "data": {"campus": campuses_information}}


# 按校区筛选餐厅
@background.get("/canteens/by-campus", status_code=200, response_description="got successfully",
                summary="按校区筛选餐厅")
async def get_canteens_by_campus(page: int, limit: int, campus_id: int, db: Session = Depends(get_db),
                                 current_manager: ManagerMessage = Depends(get_current_manager)):
    canteens = get_canteens_filter_campus(db, page, limit, campus_id)
    canteens_information = []
    levels_information = []
    for canteen in canteens:
        levels = get_levels_by_canteen_id(db, canteen.canteen_id)
        for level in levels:
            windows = get_windows_by_level_id(db, level.level_id)
            windows_information = [{
                "windows_name": window.window_name,
                "windows_id": window.window_id
            } for window in windows]
            level_information = {
                "level_id": level.level_id,
                "windows_num": level.window_num,
                "windows_information": windows_information,
            }
            levels_information.append(level_information)
        canteen_information = {"canteen_name": canteen.canteen_name,
                               "canteen_id": canteen.canteen_id,
                               "level_num": canteen.level_num,
                               "campus": {
                                   "campus_name": get_campus_by_id(db, canteen.campus_id).campus_name,
                                   "campus_id": canteen.campus_id,
                               },
                               "levels_information": levels_information}
        canteens_information.append(canteen_information)
    return {"message": "success", "detail": "获取成功", "data": {"canteens_information": canteens_information}}


#


# 菜品管理接口
# 增加新菜品
@background.post("/dishes", status_code=201, response_description="added successfully", summary="增加新菜品")
async def add_new_dish(dish_message: DishMessage,
                       current_manager: ManagerMessage = Depends(get_current_manager),
                       db: Session = Depends(get_db)
                       ):
    add_dish(db, dish_message)
    return {"message": "success", "detail": "添加成功", "data": {}}


# 修改菜品
@background.put("/dishes", status_code=200, response_description="edited successfully", summary="修改菜品信息")
async def edit_dish(dish_message: EditDishMessage, db: Session = Depends(get_db),
                    current_manager: ManagerMessage = Depends(get_current_manager)):
    dish = get_dish_by_dish_id(db, dish_message.dish_id)
    if not dish:
        raise HTTPException(status_code=400, detail="菜品不存在")
    dish.dish_name = dish_message.name
    dish.morning = dish_message.morning
    dish.noon = dish_message.noon
    dish.night = dish_message.night
    dish.muslim = dish_message.muslim
    dish.price = dish_message.price
    dish.size = dish_message.size
    db.commit()
    db.refresh(dish)
    return {"message": "success", "detail": "修改成功", "data": {}}


# 按页获取菜品信息
@background.get("/dishes", status_code=200, response_description="got successfully", summary="按页获取菜品信息")
async def get_dishes_by_page(page: int, limit: int, db: Session = Depends(get_db),
                             current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = get_dishes_page(db, page, limit)
    dishes_information = []
    for dish in dishes:
        window = get_window_by_window_id(db, dish.window_id)
        level = get_level_by_level_id(db, window.level_id)
        canteen = get_canteen_by_canteen_id(db, level.canteen_id)
        campus = get_campus_by_id(db, canteen.campus_id)
        dish_information = {
            "dish_name": dish.dish_name,
            "dish_id": dish.dish_id,
            "muslim": dish.muslim,
            "date":
                {
                    "morning": dish.morning,
                    "noon": dish.noon,
                    "night": dish.night,
                },
            "position":
                {
                    "campus": {
                        "campus_id": campus.campus_id,
                        "campus_name": campus.campus_name,
                    },
                    "level": {
                        "level_id": level.level_id,
                        "level": level.level
                    },
                    "window":
                        {
                            "window_id": window.window_id,
                            "window_name": window.window_name,
                        }
                }
        }
        dishes_information.append(dish_information)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# 删除菜品
@background.delete("/dishes", status_code=200, response_description="deleted successfully", summary="删除菜品")
async def delete_current_dish(dish_id: str, db: Session = Depends(get_db),
                              current_manager: ManagerMessage = Depends(get_current_manager)):
    dish = get_dish_by_dish_id(db, dish_id)
    if not dish:
        raise HTTPException(status_code=400, detail="菜品不存在")
    db.delete(dish)
    db.commit()

    return {"message": "success", "detail": "删除成功", "data": {}}


# 按餐厅筛选菜品
@background.get("/dishes/by-canteen", status_code=200, response_description="got successfully",
                summary="按餐厅筛选菜品")
async def get_dishes_by_canteen(canteen_id: str, page: int, limit: int, db: Session = Depends(get_db),
                                current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = get_dishes_filter_canteen(db, page, limit, canteen_id)
    dishes_information = []
    for dish in dishes:
        window = get_window_by_window_id(db, dish.window_id)
        level = get_level_by_level_id(db, window.level_id)
        canteen = get_canteen_by_canteen_id(db, level.canteen_id)
        campus = get_campus_by_id(db, canteen.campus_id)
        dish_information = {
            "dish_name": dish.dish_name,
            "dish_id": dish.dish_id,
            "muslim": dish.muslim,
            "date":
                {
                    "morning": dish.morning,
                    "noon": dish.noon,
                    "night": dish.night,
                },
            "position":
                {
                    "campus": {
                        "campus_id": campus.campus_id,
                        "campus_name": campus.campus_name,
                    },
                    "level": {
                        "level_id": level.level_id,
                        "level": level.level
                    },
                    "window":
                        {
                            "window_id": window.window_id,
                            "window_name": window.window_name,
                        }
                }
        }
        dishes_information.append(dish_information)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# 按时间筛选菜品
@background.get("/dishes/by-date", status_code=200, response_description="got successfully",
                summary="按时间筛选菜品")
async def get_dishes_by_time(page: int, limit: int, morning: bool, noon: bool, night: bool,
                             db: Session = Depends(get_db),
                             current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = []
    if morning:
        morning_dishes = get_dishes_filter_morning(db, page, limit)
        for dish in morning_dishes:
            dishes.append(dish)
    if noon:
        noon_dishes = get_dishes_filter_noon(db, page, limit)
        for dish in noon_dishes:
            dishes.append(dish)
    if night:
        night_dishes = get_dishes_filter_night(db, page, limit)
        for dish in night_dishes:
            dishes.append(dish)
    dishes = list(set(dishes))
    dishes_information = []
    for dish in dishes:
        window = get_window_by_window_id(db, dish.window_id)
        level = get_level_by_level_id(db, window.level_id)
        canteen = get_canteen_by_canteen_id(db, level.canteen_id)
        campus = get_campus_by_id(db, canteen.campus_id)
        dish_information = {
            "dish_name": dish.dish_name,
            "dish_id": dish.dish_id,
            "muslim": dish.muslim,
            "date":
                {
                    "morning": dish.morning,
                    "noon": dish.noon,
                    "night": dish.night,
                },
            "position":
                {
                    "campus": {
                        "campus_id": campus.campus_id,
                        "campus_name": campus.campus_name,
                    },
                    "level": {
                        "level_id": level.level_id,
                        "level": level.level
                    },
                    "window":
                        {
                            "window_id": window.window_id,
                            "window_name": window.window_name,
                        }
                }
        }
        dishes_information.append(dish_information)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# 获取窗口及其id的序列
@background.get("/windows", status_code=200, response_description="got successfully", summary="获取窗口及其id的序列")
async def get_windows(db: Session = Depends(get_db), current_manager: ManagerMessage = Depends(get_current_manager)):
    canteens = get_all_canteens(db)
    canteens_information = []
    levels_information = []
    for canteen in canteens:
        levels = get_levels_by_canteen_id(db, canteen.canteen_id)
        for level in levels:
            windows = get_windows_by_level_id(db, level.level_id)
            windows_information = [{
                "window": window.window,
                "window_id": window.window_id
            } for window in windows]
            level_information = {
                "level": level.level,
                "windows_information": windows_information,
            }
            levels_information.append(level_information)
        canteen_information = {"canteen_name": canteen.canteen_name,
                               "canteen_id": canteen.canteen_id,
                               "campus": {
                                   "campus_name": get_campus_by_id(db, canteen.campus_id).campus_name,
                                   "campus_id": canteen.campus_id,
                               },
                               "levels_information": levels_information}
        canteens_information.append(canteen_information)
    return {"message": "success", "detail": "获取成功", "data": {"canteens_information": canteens_information}}


# 上传图片
@background.post("/photos", status_code=201, response_description="added successfully", summary="上传图片")
async def add_photo(photo: UploadFile, current_manager: ManagerMessage = Depends(get_current_manager),
                    ):
    zh = photo.filename.split(".").pop()
    dir_path = "./static/"
    file_name = str(random.randint(10000, 99999) + time.time()) + "." + zh
    file_path = dir_path + file_name
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await photo.read())
    return {"message": "success", "detail": "上传成功", "data": {"url": file_path}}
