from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status
import json
from .crud import *
from datetime import timedelta, datetime
from jose import JWTError, jwt
import requests


# 连接数据库的辅助函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 鉴权需要
APPID = ""
SECRET = ""
SECRET_KEY = ""
ALGORITHM = ""
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Bearer令牌，从"/token"这一url处获取
oauth2_scheme_1 = OAuth2PasswordBearer(tokenUrl="/frontpage/token")


# 鉴别用户
def authenticate_user(db: Session, openid: str):
    user = get_user_by_openid(db, openid)
    # 如果用户不存在则返回假
    if not user:
        return False
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


async def get_current_user(token: str = Depends(oauth2_scheme_1), db=Depends(get_db)):
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
    user = get_user_by_openid(db, openid=token_data.openid)
    # 如果反解失败，那么提出错误
    if user is None:
        raise credentials_exception
    return user


def get_wx(code):
    data = {"appid": APPID,
            "secret": SECRET,
            "js_code": code,
            "grant_type": "authorization_code"}
    res = requests.get("https://api.weixin.qq.com/sns/jscode2session", params=data)
    # 微信api来鉴别身份
    wx_dict = json.loads(res.text)
    openid = wx_dict.get("openid")
    if openid:
        return openid
    # code无效
    if wx_dict["errcode"] == 40029 or wx_dict["errcode"] == 40125:
        raise HTTPException(status_code=400, detail="Incorrect code")
    # wx服务器繁忙
    elif wx_dict["errcode"] == 45011 or wx_dict["errcode"] == -1:
        raise HTTPException(status_code=429, detail="Too busy server")
    # 用户不安全
    elif wx_dict["errcode"] == 40226:
        raise HTTPException(status_code=403, detail="Not permitted user")
    elif wx_dict["errcode"] == 40163:
        raise HTTPException(status_code=408, detail="Request timeout")
    else:
        raise HTTPException(status_code=401)
