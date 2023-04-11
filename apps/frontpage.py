import json

from fastapi import APIRouter, Depends, requests
from sqlalchemy.orm import Session
from .models import *
from .schemas import *
from .crud import *
import datetime
from .background import *

frontpage = APIRouter()

# 鉴权需要
APPID = "wx0d164561b0573e5c"
SECRET = "6e85660d10f135e6732b79125626d4bd"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
# Bearer令牌，从"/token"这一url处获取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 校验密码是否匹配
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# 加密密码
def get_password_hash(password):
    return pwd_context.hash(password)


# 鉴别用户
def authenticate_user(db: Session, openid: str):
    user = get_user_openid(db, openid)
    # 如果用户不存在则返回假
    if not user:
        return False
    # if not verify_password(student_number, user.hashed_password):
    #     return False
    return user


# 生成token
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """
    生成token
    :param data: 待加密，字典类型
    :param expires_delta: 过期时间，timedelta（datetime）类型
    :return: 加密的jwt令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    # 预先定义好错误
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 对令牌解码
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        openid: str = payload.get("sub")
        if openid is None:
            raise credentials_exception
        token_data = TokenData(openid=openid)
    except JWTError:
        raise credentials_exception
    # 解码得到openid，在数据库中查找
    user = get_user_openid(db, openid=token_data.openid)
    # 如果反解失败，那么提出错误
    if user is None:
        raise credentials_exception
    return user


@frontpage.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)
):
    user = authenticate_user(db, form_data.username)
    if not user:
        # 如果身份鉴定未通过
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unrecognized student",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 设置过期时间
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # 生成token
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def get_wx(code):
    data = {"appid": APPID,
            "secret": SECRET,
            "js_code": code,
            "grant_type": "authorization_code"}
    res = requests.get("https://api.weixin.qq.com/sns/jscode2session", params=data)
    # 微信api来鉴别身份
    wxdict = json.loads(res.text)
    openid = wxdict.get("openid")
    if openid:
        return openid
    # code无效
    if wxdict["errcode"] == 40029 or wxdict["errcode"] == 40125:
        raise HTTPException(status_code=400, detail="Incorrect code")
    # wx服务器繁忙
    elif wxdict["errcode"] == 45011 or wxdict["errcode"] == -1:
        raise HTTPException(status_code=429, detail="Too busy server")
    # 用户不安全
    elif wxdict["errcode"] == 40226:
        raise HTTPException(status_code=403, detail="Not permitted user")
    elif wxdict["errcode"] == 40163:
        raise HTTPException(status_code=408, detail="Request timeout")
    else:
        raise HTTPException(status_code=401)


# 注册
@frontpage.post(
    "/signup",
    summary="注册",
    status_code=201,
    response_description="Created Successfully"
)
def login(user: int, db=Depends(get_db)):
    """
    注册接口，用户初次使用需注册，将学号、姓名、手机号存入数据库，同时返回token，有效期为30天
    - :param user:请求体参数，包括学号student_number（str），name（str）、phone（str）
    - :param db:数据库需要
    - :return:会返回token储存在data里
    """

    # 前端发来临时登录凭证code，后端反解openid查看注册状态
    openid = get_wx(user.id)
    # 通过openid来寻找用户
    user_old = get_user_openid(db, openid)
    # 设置过期时间
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # 生成token
    access_token = create_access_token(
        data={"sub": openid}, expires_delta=access_token_expires
    )
    # 如果用户已存在
    if user_old:
        if user_old.student_number != user.student_number:
            raise HTTPException(status_code=403, detail="Suspicious user")
        return {
            "message": "fail",
            "detail": "用户已注册",
            "data": {"access_token": access_token, "token_type": "bearer"},
        }
    student_number = user.student_number
    name = user.name
    phone = user.phone
    # 如未查找到，则注册
    add_user(db, student_number, name, phone, openid)
    return {
        "message": "success",
        "detail": "注册成功",
        "data": {"access_token": access_token, "token_type": "bearer"},
    }


# code换取token
@frontpage.get("/get_token")
def get_token(code: str):
    """
    code换取token
    :param code:临时登录凭证
    :return:
    """
    # 前端发来临时登录凭证code，后端反解openid查看注册状态
    openid = get_wx(code)
    # 通过openid来寻找用户
    user_old = get_user_openid(db, openid)
    if not user_old:
        raise HTTPException(status_code=401, detail="Unrecognized user")
    # 设置过期时间
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # 生成token
    access_token = create_access_token(
        data={"sub": openid}, expires_delta=access_token_expires
    )
    # 返回token
    return {
        "message": "success",
        "detail": "成功获取token",
        "data": {"access_token": access_token, "token_type": "bearer"},
    }


@frontpage.get("/dishes", status_code=200, response_description="got successfully", summary="获取菜品信息")
async def get_this_dishes(openid: str, db: Session = Depends(get_db), level: int = 1, canteen_id: str = '0'):
    dishes = get_dishes_by_canteen_and_level(db, canteen_id, level)
    dishes_information = get_dish_message(db, dishes, openid)
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


@frontpage.get("/likes", status_code=200, response_description="got successfully", summary="查询单个菜品点赞")
async def get_like_status(dish_id: str, openid: str, db: Session = Depends(get_db)):
    like = get_like(db, openid, dish_id)
    dish = get_dish_by_dish_id(db, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
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


@frontpage.put("/likes", status_code=200, response_description="changed successfully", summary="点赞或取消赞")
async def chang_like_status(dish_id: str, openid: str, db: Session = Depends(get_db)):
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
