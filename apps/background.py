from fastapi import FastAPI, HTTPException, Depends, Form, status, APIRouter
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
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
        raise HTTPException(status_code=400, detail="Inactive manager")
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
    return {"message": "注册成功"}


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
    return {"message": "删除成功"}


# 餐厅管理接口

# 增加新餐厅
@background.post("/canteens", status_code=201, response_description="added successfully", summary="增加新餐厅",
                 response_model=ManagerMessage)
async def add_new_canteens(dish_message: DishMessage, db: Session = Depends(get_db),
                           current_manager: ManagerMessage = Depends(get_current_manager),
                           ):
    canteen = get_canteen_by_name(db, dish_message.canteen_id)
    if canteen:
        raise HTTPException(status_code=400, detail="餐厅已存在")
    add_canteen(db, )
    return {"message": "success"}


# 修改餐厅
@background.put("/canteens", status_code=200, response_description="edited successfully", summary="修改餐厅")
async def edit_canteens(dish_message: DishMessage, current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"username": current_manager.username, "message": "success"}


# 获取餐厅信息
@background.get("/canteens", status_code=200, response_description="got successfully", summary="获取餐厅信息")
async def get_current_campus(current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"message": "success", "data": {}}


# 删除餐厅
@background.delete("/canteens", status_code=200, response_description="deleted successfully", summary="删除餐厅")
async def delete_current_canteens(current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"message": "success"}


# 菜品管理接口
# 增加新菜品
@background.post("/dishes", status_code=201, response_description="added successfully", summary="增加新菜品")
async def add_new_dishes(
        current_manager: ManagerMessage = Depends(get_current_manager),
        db: Session = Depends(get_db)
):
    return {"username": current_manager.username, "message": "success"}


# 修改菜品
@background.put("/dishes", status_code=200, response_description="edited successfully", summary="修改菜品")
async def edit_dishes(current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"username": current_manager.username, "message": "success"}


# 获取菜品信息
@background.get("/dishes", status_code=200, response_description="got successfully", summary="获取菜品信息")
async def get_current_dishes(current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"message": "success", "data": {}}


# 删除菜品
@background.delete("/dishes", status_code=200, response_description="deleted successfully", summary="删除菜品")
async def delete_current_canteens(current_manager: ManagerMessage = Depends(get_current_manager)):
    return {"message": "success"}

# 上传图片

