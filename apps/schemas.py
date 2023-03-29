from pydantic import BaseModel
from typing import Union


# Token 相关模型

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


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
