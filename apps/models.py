from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from typing import Union


# import MySQLdb
# import sys

# 后台表
class Managers(Base):
    __tablename__ = "managers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(20), unique=True, index=True)
    hashed_password = Column(String(255))
    permission = Column(Boolean)  # 超级管理员权限


class Campus(Base):
    __tablename__ = "campus"
    campus_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campus_name = Column(String(20), index=True)
    canteen_num = Column(Integer)


class Canteens(Base):  # 餐厅
    __tablename__ = "canteens"
    canteen_id = Column(String(2), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id
    canteen_name = Column(String(10), index=True)
    campus_id = Column(Integer, ForeignKey("campus.campus_id"), index=True)
    level_num = Column(Integer)  # 楼层数   可改为tinyint


class Levels(Base):
    __tablename__ = "levels"
    level_id = Column(String(4), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id
    level = Column(Integer)  # 楼层   可改为tinyint
    window_num = Column(Integer)  # 窗口数   可改为tinyint
    canteen_id = Column(String(2), ForeignKey("canteens.canteen_id"))  # ForeignKey("canteens.id")


class Windows(Base):
    __tablename__ = "windows"
    window_id = Column(String(6), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号
    window_name = Column(String(10), index=True)
    dish_num = Column(Integer)
    level_id = Column(String(4), ForeignKey("levels.level_id"))  #
    window = Column(Integer)


class Dishes(Base):
    __tablename__ = "dishes"
    dish_id = Column(String(9), primary_key=True, index=True)
    dish_name = Column(String(15), index=True)  #
    # 供饭时间
    morning = Column(Boolean, index=True)
    noon = Column(Boolean, index=True)
    night = Column(Boolean, index=True)
    canteen_id = Column(String(2), ForeignKey("canteens.canteen_id"), index=True)
    window_id = Column(String(6), index=True)
    muslim = Column(Boolean, index=True)  # 是否清真
    level = Column(Integer, index=True)  # 楼层   可改为tinyint
    window = Column(Integer, index=True)  # 窗口   可改为tinyint
    price = Column(Float)
    size = Column(String(5))

    """
    ！！！！！！！改为通过id分解   2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号 + 3位dish编号！！！！！！！
    """
    # labels = Column()  # 标签
    photos = Column(String(70))  # 图片  url储存
    spare_photos = Column(String(70))  # 备用图片   url储存
    likes = Column(Integer)  # 点赞数


# 前台表
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    openid = Column(String(90), primary_key=True, index=True)
    user_name = Column(String(15), unique=True)
    personal_signature = Column(String(70))
    head_sculpture = Column(String(70))


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    openid = Column(Integer, ForeignKey("users.id"))  # user id
    dish_id = Column(String(9), index=True)
    date_ = Column(DateTime)

# 已修改为最新
