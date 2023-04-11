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


class Dishes(Base):
    __tablename__ = "dishes"
    dish_id = Column(String(9), primary_key=True, index=True)
    dish_name = Column(String(15), index=True)  #
    # 供饭时间
    morning = Column(Boolean)
    noon = Column(Boolean)
    night = Column(Boolean)
    canteen_id = Column(String(2))
    window_id = Column(String(6), primary_key=True, index=True)
    muslim = Column(Boolean)  # 是否清真
    level = Column(Integer)  # 楼层   可改为tinyint
    window = Column(Integer)  # 窗口   可改为tinyint
    price = Column(Float)
    size = Column(String(5))

    """
    ！！！！！！！改为通过id分解   2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号 + 3位dish编号！！！！！！！
    """
    # labels = Column()  # 标签
    photos = Column(String(70))  # 图片  url储存
    spare_photos = Column(String(70))  # 备用图片   url储存
    likes = Column(Integer)  # 点赞数


class Canteens(Base):  # 餐厅
    __tablename__ = "canteens"
    canteen_id = Column(String(2), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id
    canteen_name = Column(String(10), index=True)
    campus_id = Column(Integer, index=True)
    level_num = Column(Integer)  # 楼层数   可改为tinyint


class Campus(Base):
    __tablename__ = "campus"
    campus_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campus_name = Column(String(10), index=True)
    canteen_num = Column(Integer)


class Levels(Base):
    __tablename__ = "levels"
    level_id = Column(String(4), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id
    level = Column(Integer)  # 楼层   可改为tinyint
    window_num = Column(Integer)  # 窗口数   可改为tinyint
    canteen_id = Column(String(2))  # ForeignKey("canteens.id")


class Windows(Base):
    __tablename__ = "windows"
    window_id = Column(String(6), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号
    window_name = Column(String(10), index=True)
    dish_num = Column(Integer)
    level_id = Column(String(4))
    window = Column(Integer)


# 前台表
class Users(Base):
    __tablename__ = "users"
    openid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(15), unique=True)


class Like(Base):
    __tablename__ = "like"
    unique_identifier=Column(Integer,primary_key=True, index=True)
    openid = Column(Integer, index=True)  # user id
    dish_id = Column(String(9), index=True)
    date_ = Column(DateTime)
