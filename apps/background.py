import os
import random
import time
import aiofiles
from fastapi import Depends, status, APIRouter, UploadFile, Body
from .crud import *
from .schemas import *
from typing import Union
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/background/token")


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


# 管理员修改密码
@background.post("/manager/change-password", status_code=200,
                 response_description="changed successfully",
                 summary="修改密码")
async def change_password(password: str = Form(..., min_length=8, max_lengh=20), db: Session = Depends(get_db),
                          current_manager: ManagerMessage = Depends(get_current_manager)):
    hashed_password = hash_password(password)
    change_manager_password(db, current_manager.username, hashed_password)
    return {"message": "success", "detail": "修改成功", "data": {}}


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
    canteen = get_canteen_by_name(db, canteen_message.canteen_name, canteen_message.campus_id)
    if canteen:
        raise HTTPException(status_code=400, detail="餐厅已存在")
    campus = get_campus_by_id(db, canteen_message.campus_id)
    if campus.canteen_num == 9:
        raise HTTPException(status_code=400, detail="添加失败，该校区餐厅编号已满，请联系开发人员")
    add_canteen(db, canteen_message)
    new_canteen = get_canteen_by_name(db, canteen_message.canteen_name, canteen_message.campus_id)
    for level in canteen_message.levels:
        add_level(db, new_canteen.canteen_id, level.level, level.windows_num)
        level_id = get_level_id(new_canteen.canteen_id, level.level)
        for window in level.windows_information:
            new_level = get_level_by_level_id(db, level_id)
            add_window(db, window.windows_name, new_level.level_id, window.windows)
    return {"message": "success", "detail": "添加成功", "data": {}}


# 修改餐厅
@background.put("/canteens", status_code=200, response_description="edited successfully", summary="修改餐厅信息")
async def edit_canteens(canteen_message: CanteenMessage, canteen_id: str = Body(), db: Session = Depends(get_db),
                        current_manager: ManagerMessage = Depends(get_current_manager)):
    canteen = get_canteen_by_canteen_id(db, canteen_id)
    if not canteen:
        raise HTTPException(status_code=404, detail="餐厅不存在")
    canteen.canteen_name = canteen_message.canteen_name
    canteen.level_num = canteen_message.level_num
    db.commit()
    db.refresh(canteen)
    new_levels_id = []
    for level in canteen_message.levels:
        new_level_id = get_level_id(canteen_id, level.level)
        new_levels_id.append(new_level_id)
        old_level = get_level_by_level_id(db, new_level_id)
        if old_level:
            old_level.window_num = level.windows_num
            db.commit()
            db.refresh(old_level)
        if not old_level:
            add_level(db, canteen_id, level.level, level.windows_num)
        new_windows_id = []
        old_windows_id = []
        for window in level.windows_information:
            if window.windows < 10:
                num = "0" + str(window.windows)
            else:
                num = str(window.windows)
            new_window_id = new_level_id + num
            new_windows_id.append(new_window_id)
            old_window = get_window_by_window_id(db, new_window_id)
            if old_window:
                old_window.window_name = window.windows_name
                db.commit()
                db.refresh(old_window)
            if not old_window:
                add_window(db, window.windows_name, new_level_id, window.windows)
        windows = get_windows_by_level_id(db, new_level_id)
        for window in windows:
            old_windows_id.append(window.window_id)
        delete_windows_id = [window_id for window_id in old_windows_id if window_id not in new_windows_id]
        for delete_window_id in delete_windows_id:
            delete_window = get_window_by_window_id(db, delete_window_id)
            dishes = get_dishes_by_window_id(db, delete_window_id)
            for dish in dishes:
                if dish.photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.photos)
                if dish.spare_photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.spare_photos)
                db.delete(dish)
                db.commit()
            db.delete(delete_window)
            db.commit()
    old_levels_id = []
    levels = get_levels_by_canteen_id(db, canteen_id)
    for level in levels:
        old_levels_id.append(level.level_id)
    delete_levels_id = [delete_level_id for delete_level_id in old_levels_id if delete_level_id not in new_levels_id]
    for delete_level_id in delete_levels_id:
        delete_level = get_level_by_level_id(db, delete_level_id)
        windows = get_windows_by_level_id(db, delete_level_id)
        for window in windows:
            dishes = get_dishes_by_window_id(db, window.window_id)
            for dish in dishes:
                if dish.photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.photos)
                if dish.spare_photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.spare_photos)
                db.delete(dish)
                db.commit()
            db.delete(window)
            db.commit()
        db.delete(delete_level)
        db.commit()

    if canteen.campus_id != canteen_message.campus_id:
        canteen = get_canteen_by_name(db, canteen_message.canteen_name, canteen_message.campus_id)
        if canteen:
            raise HTTPException(status_code=400, detail="餐厅已存在")
        campus = get_campus_by_id(db, canteen_message.campus_id)
        if campus.canteen_num == 9:
            raise HTTPException(status_code=400, detail="添加失败，该校区餐厅编号已满，请联系开发人员")
        add_canteen(db, canteen_message)
        new_canteen = get_canteen_by_name(db, canteen_message.canteen_name, canteen_message.campus_id)
        for level in canteen_message.levels:
            add_level(db, new_canteen.canteen_id, level.level, level.windows_num)
            level_id = get_level_id(new_canteen.canteen_id, level.level)
            for window in level.windows_information:
                new_level = get_level_by_level_id(db, level_id)
                add_window(db, window.windows_name, new_level.level_id, window.windows)
        dishes = get_dishes_by_canteen_id(db, canteen_id)
        for dish in dishes:
            dish.canteen_id = new_canteen.canteen_id
            dish.window_id = new_canteen.canteen_id + dish.window_id[2:6]
            dish.dish_id = new_canteen.canteen_id + dish.dish_id[2:10]
            db.commit()
            db.refresh(dish)
        old_canteen = get_canteen_by_canteen_id(db, canteen_id)
        if not old_canteen:
            raise HTTPException(status_code=404, detail="餐厅不存在")
        levels = get_levels_by_canteen_id(db, canteen_id)
        for level in levels:
            windows = get_windows_by_level_id(db, level.level_id)
            for window in windows:
                db.delete(window)
                db.commit()
            db.delete(level)
            db.commit()
        db.delete(old_canteen)
        db.commit()
    return {"message": "success", "detail": "修改成功", "data": {}}


# 按页获取餐厅信息
@background.get("/canteens", status_code=200, response_description="got successfully", summary="按页获取餐厅信息")
async def get_canteens_by_page(page: int, limit: int, db: Session = Depends(get_db),
                               current_manager: ManagerMessage = Depends(get_current_manager),
                               ):
    canteens = get_canteens(db, page, limit)
    canteens_information = get_canteens_message(db, canteens)
    canteens_num = len(get_all_canteens(db))
    total_page = get_total_page(canteens_num, limit)
    if not canteens_information:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            canteens = get_canteens(db, page, limit)
            canteens_information = get_canteens_message(db, canteens)
            if not canteens_information:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功",
            "data": {"canteens_information": canteens_information,
                     "page_information": {"page": page, "total_page": total_page}}}


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
            dishes = get_dishes_by_window_id(db, window.window_id)
            for dish in dishes:
                if dish.photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.photos)
                if dish.spare_photos:
                    if os.path.exists(dish.photos):
                        os.remove(dish.spare_photos)
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
    canteens_information = get_canteens_message(db, canteens)
    canteens_num = len(get_canteens_by_campus_id(db, campus_id))
    total_page = get_total_page(canteens_num, limit)
    if not canteens_information:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            canteens = get_canteens_filter_campus(db, page, limit, campus_id)
            canteens_information = get_canteens_message(db, canteens)
            if not canteens_information:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功",
            "data": {"canteens_information": canteens_information,
                     "page_information": {"page": page, "total_page": total_page}}}


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
async def edit_dish(dish_message: DishMessage, dish_id: str = Body(), db: Session = Depends(get_db),
                    current_manager: ManagerMessage = Depends(get_current_manager)):
    dish = get_dish_by_dish_id(db, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    new_window = get_window(db, dish_message.canteen_id, dish_message.level, dish_message.window)
    if not new_window:
        raise HTTPException(status_code=404, detail="此窗口不存在")
    if dish.photos:
        if dish.photos != dish_message.photos:
            if os.path.exists(dish.photos):
                os.remove(dish.photos)
    if dish.spare_photos:
        if dish.spare_photos != dish_message.spare_photos:
            if os.path.exists(dish.photos):
                os.remove(dish.spare_photos)
    if new_window.window_id == dish.window_id:
        dish.dish_name = dish_message.name
        dish.morning = dish_message.morning
        dish.noon = dish_message.noon
        dish.night = dish_message.night
        dish.muslim = dish_message.muslim
        dish.price = dish_message.price
        dish.photos = dish_message.photos
        dish.spare_photos = dish_message.spare_photos
        db.commit()
        db.refresh(dish)
    else:
        db.delete(dish)
        db.commit()
        add_dish(db, dish_message)
    return {"message": "success", "detail": "修改成功", "data": {}}


# 按页获取菜品信息
@background.get("/dishes", status_code=200, response_description="got successfully", summary="按页获取菜品信息")
async def get_dishes_by_page(page: int, limit: int, db: Session = Depends(get_db),
                             current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = get_dishes_page(db, page, limit)
    dishes_information = get_dishes_message(db, dishes)
    dishes_num = len(get_all_dishes(db))
    total_page = get_total_page(dishes_num, limit)
    if not dishes_information:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            dishes = get_dishes_page(db, page, limit)
            dishes_information = get_dishes_message(db, dishes)
            if not dishes_information:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information},
            "page_information": {"page": page, "total_page": total_page}}


# 删除菜品
@background.delete("/dishes", status_code=200, response_description="deleted successfully", summary="删除菜品")
async def delete_current_dish(dish_id: str, db: Session = Depends(get_db),
                              current_manager: ManagerMessage = Depends(get_current_manager)):
    dish = get_dish_by_dish_id(db, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    if dish.photos:
        if os.path.exists(dish.photos):
            os.remove(dish.photos)
    if dish.spare_photos:
        if os.path.exists(dish.photos):
            os.remove(dish.spare_photos)
    db.delete(dish)
    db.commit()

    return {"message": "success", "detail": "删除成功", "data": {}}


# 按餐厅筛选菜品
@background.get("/dishes/by-canteen", status_code=200, response_description="got successfully",
                summary="按餐厅筛选菜品")
async def get_dishes_by_canteen(canteen_id: str, page: int, limit: int, db: Session = Depends(get_db),
                                current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = get_dishes_filter_canteen(db, page, limit, canteen_id)
    dishes_information = get_dishes_message(db, dishes)
    dishes_num = len(get_dishes_by_canteen_id(db, canteen_id))
    total_page = get_total_page(dishes_num, limit)
    if not dishes_information:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            dishes = get_dishes_filter_canteen(db, page, limit, canteen_id)
            dishes_information = get_dishes_message(db, dishes)
            if not dishes_information:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information},
            "page_information": {"page": page, "total_page": total_page}}


# 按时间筛选菜品
@background.get("/dishes/by-date", status_code=200, response_description="got successfully",
                summary="按时间筛选菜品")
async def get_dishes_by_time(page: int, limit: int, morning: bool, noon: bool, night: bool,
                             db: Session = Depends(get_db),
                             current_manager: ManagerMessage = Depends(get_current_manager)):
    dishes = get_dishes_filter_time(db, morning, noon, night, page, limit)
    dishes_information = get_dishes_message(db, dishes)
    dishes_num = len(get_dishes_by_times(db, morning, noon, night))
    total_page = get_total_page(dishes_num, limit)
    if not dishes_information:
        if page == 1:
            raise HTTPException(status_code=404, detail="获取失败，无更多信息")
        if page > total_page:
            page = total_page
            dishes = get_dishes_filter_time(db, morning, noon, night, page, limit)
            dishes_information = get_dishes_message(db, dishes)
            if not dishes_information:
                raise HTTPException(status_code=404, detail="获取失败，无更多信息")
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information},
            "page_information": {"page": page, "total_page": total_page}}


# 获取窗口及其id的序列
@background.get("/windows", status_code=200, response_description="got successfully", summary="获取窗口及其id的序列")
async def get_windows(db: Session = Depends(get_db), current_manager: ManagerMessage = Depends(get_current_manager)):
    canteens = get_all_canteens(db)
    canteens_information = []
    for canteen in canteens:
        levels = get_levels_by_canteen_id(db, canteen.canteen_id)
        levels_information = []
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
async def add_photo(photo: UploadFile, current_manager: ManagerMessage = Depends(get_current_manager)
                    ):
    zh = photo.filename.split(".").pop()
    dir_path = "./static/"
    file_name = str(random.randint(10000, 99999) + time.time()) + "." + zh
    file_path = dir_path + file_name
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await photo.read())
    return {"message": "success", "detail": "上传成功", "data": {"url": file_path}}
