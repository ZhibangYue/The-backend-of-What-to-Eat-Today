import os
import time
import aiofiles
from .utils import *
from .crud import *
from fastapi import APIRouter, UploadFile
import random

frontpage = APIRouter()


# 获取token的依赖
@frontpage.post("/token", response_model=Token)
async def login_for_access_token(openid: str, db=Depends(get_db)):
    user = authenticate_user(db, openid)
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
        data={"sub": openid}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 注册
@frontpage.post(
    "/signup",
    summary="注册",
    status_code=201,
    response_description="Created Successfully"
)
def login(user: UserBase, db=Depends(get_db)):
    """
    注册接口，用户初次使用需注册，将用户名，个性签名存入数据库，同时返回token，有效期为30天
    - :param user:请求体参数，包括code，用户名，个性签名
    - :param db:数据库需要
    - :return:会返回token储存在data里
    """

    # 前端发来临时登录凭证code，后端反解openid查看注册状态
    openid = get_wx(user.code)
    # 通过openid来寻找用户
    user_old = get_user_by_openid(db, openid)
    # 设置过期时间
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # 生成token
    access_token = create_access_token(
        data={"sub": openid}, expires_delta=access_token_expires
    )
    # 如果用户已存在
    if user_old:
        return {
            "message": "fail",
            "detail": "用户已注册",
            "data": {"access_token": access_token, "token_type": "bearer"},
        }

    # 如未查找到，则注册
    add_user(db, openid, user.username, user.personal_signature)
    return {
        "message": "success",
        "detail": "注册成功",
        "data": {"access_token": access_token, "token_type": "bearer"},
    }


# code换取token
@frontpage.get("/get-token")
def get_token(code: str, db: Session = Depends(get_db)):
    """
    code换取token
    :param db:
    :param code:临时登录凭证
    :return:
    """
    # 前端发来临时登录凭证code，后端反解openid查看注册状态
    openid = get_wx(code)
    # 通过openid来寻找用户

    user_old = get_user_by_openid(db, openid)
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


@frontpage.post("/user/head_sculpture")
async def change_head_sculpture(
        head_sculpture: UploadFile,
        user: UserMessage = Depends(get_current_user),
        db=Depends(get_db),
):
    """
    更换头像，上传的文件在请求体里，以表单数据形式发出。返回文件名。可以通过/static/xxx.jpg访问。
    :param head_sculpture:头像路径
    :param user: token鉴定身份
    :param db: 数据库需要
    :return:
    """
    # 后缀名
    zh = head_sculpture.filename.split(".").pop()
    # 静态文件储存目录
    dir_path = "./static/"
    # 文件名，储存进数据库
    file_name = str(random.randint(10000, 99999) + time.time()) + "." + zh
    # 文件路径
    file_path = dir_path + file_name
    # 尝试写入
    # try:
    # with open(file_path, "wb") as f:
    #     shutil.copyfileobj(avatar.file, f)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await avatar.read())
    # except:
    #     return {"message": "fail", "detail": "头像上传失败", "data": user.profile}
    # 删除原有头像
    if user.head_sculpture != "":
        os.remove(user.head_sculpture)
    # 更新数据库
    user.head_sculpture = file_path
    db.commit()
    db.refresh(user)
    return {"message": "success", "detail": "头像更新成功", "data": {"url": user.head_sculpture}}


@frontpage.get("/dishes", status_code=200, response_description="got successfully", summary="获取菜品信息")
async def get_this_dishes(user: UserMessage = Depends(get_current_user), db: Session = Depends(get_db), level: int = 1,
                          canteen_id: str = '0'):
    dishes = get_dishes_by_canteen_and_level(db, canteen_id, level)
    dishes_information = get_dish_message(db, dishes, user.openid)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


# @frontpage.get("/draw_dish", status_code=200, response_description="got successfully", summary="随机抽取菜品")
# async def draw_dish(db: Session = Depends(get_db), canteen_id: str = '0', timex: str = '0'):
#
#     return random_draw(db, canteen_id, timex)

@frontpage.get("/draw_dishes", status_code=200, response_description="got successfully", summary="随机抽取菜品")
async def draw_dish(db: Session = Depends(get_db),
                    canteen_id: str = '01', timex: str = '0'):
    dishes = get_dishes_by_name_and_time(db, canteen_id, timex)
    dishes_information = get_dish_message(db, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}


@frontpage.get("/likes", status_code=200, response_description="got successfully", summary="查询单个菜品点赞")
async def get_like_status(dish_id: str, user: UserMessage = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    like = get_like(db, user.openid, dish_id)
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
async def chang_like_status(dish_id: str, user: UserMessage = Depends(get_current_user), db: Session = Depends(get_db)):
    like = get_like(db, user.openid, dish_id)
    dish = get_dish_by_dish_id(db, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="点赞或取消失败，菜品不存在")
    if not like:
        add_like(db, user.openid, dish_id)
        new_like = get_like(db, user.openid, dish_id)
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


@frontpage.get("/records", status_code=200, response_description="get successfully", summary="获取点赞记录")
async def get_likes_records(user: UserMessage = Depends(get_current_user), db: Session = Depends(get_db)):
    records_information = search_likes_records(db, user.openid)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": records_information}}


@frontpage.get("/search", status_code=200, response_description="get successfully", summary="搜索菜品")
async def search_dishes(word: str, db: Session = Depends(get_db)):
    dishes = search_dishes_by_name(db, word)
    dishes_information = get_dish_message(db, dishes)
    return {"message": "success", "detail": "获取成功", "data": {"dishes_information": dishes_information}}
