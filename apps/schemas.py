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


# 校区信息模型
class CampusMessage(BaseModel):
    id: int
    campus_name: str
    canteen_num: int

    class Config:
        orm_mode = True


# 层数信息模型
class LevelMessage(BaseModel):
    level_id: str
    level: int
    window_num: int
    canteen_id: int

    class Config:
        orm_mode = True


# 窗口信息模型
class WindowsInformation(BaseModel):
    windows_name: str
    windows: int

    class Config:
        orm_mode = True


# 窗口模型
class WindowsMessage(BaseModel):
    level: int
    windows_num: int
    windows_information: list[WindowsInformation]

    class Config:
        orm_mode = True


# 餐厅信息模型
class CanteenMessage(BaseModel):
    canteen_name: str
    campus_id: int
    level_num: int
    levels: list[WindowsMessage]

    class Config:
        orm_mode = True


# 菜品信息模型
class DishMessage(BaseModel):
    name: str
    morning: bool
    noon: bool
    night: bool
    canteen_id: str
    muslim: bool
    photos: str
    spare_photos: str
    price: float
    size: str
    level: int
    window: int

    class Config:
        orm_mode = True


class EditDishMessage(BaseModel):
    dish_id: str
    name: str
    morning: bool
    noon: bool
    night: bool
    muslim: bool
    photos: str
    spare_photos: str
    price: float
    size: str

    class Config:
        orm_mode = True


class EditCanteenMessage(BaseModel):
    canteen_id: str
    canteen_name: str
    level_num: int
    levels: list[WindowsMessage]

    class Config:
        orm_mode = True


class DateMessage(BaseModel):
    page: int
    limit: int
    morning: bool
    noon: bool
    night: bool
