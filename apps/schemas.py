from pydantic import BaseModel
from typing import Union
from fastapi import Form


# Token 相关模型

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


# 登录表单
class PasswordRequestForm:

    def __init__(
            self,
            username: str = Form(),
            password: str = Form()
    ):
        self.username = username
        self.password = password


# 管理员信息模型
class ManagerMessage(BaseModel):
    username: str
    permission: bool

    class Config:
        orm_mode = True


# 菜品信息模型
class DishMessage(BaseModel):
    manager_id: int
    name: str
    morning: bool
    noon: bool
    night: bool
    canteen_id: str
    muslim: bool
    photos: str
    spare_photos: str
    dish_id: str
    price: float
    size: str

    class Config:
        orm_mode = True


# 餐厅信息模型
class CanteenMessage(BaseModel):
    id: int
    canteen_name: str
    campus_id: int
    level_num: int
    window_num: int

    class Config:
        orm_mode = True


# 校区信息模型
class CampusMessage(BaseModel):
    id: int
    campus_name: str
    canteen_num: int

    class Config:
        orm_mode = True


# 层数信息模型
class LevelMessage(BaseModel):
    id: str
    level: int
    window_num: int
    canteen_id: int

    class Config:
        orm_mode = True


# 窗口信息模型
class WindowsMessage(BaseModel):
    id: str
    window_name: str
    dish_num: int
    canteen_id: int
    level_id: int

    class Config:
        orm_mode = True
