from pydantic import BaseModel
from typing import Union


# Token 相关模型

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class ManagerMessage(BaseModel):
    username: str
    permission: bool

    class Config:
        orm_mode = True


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
