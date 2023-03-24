from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base


# import MySQLdb
# import sys


class Managers(Base):
    __tablename__ = "managers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(20), unique=True, index=True)
    HashedPassword = Column(String(20))
    permission = Column(Boolean)  # 超级管理员权限
    dish = relationship("Dishes", back_populates="manager")  # 查询manager添加的dishes


class Dishes(Base):
    __tablename__ = "dishes"
    id = Column(String(9), primary_key=True, index=True)
    DishName = Column(String(15), index=True)  #
    # 供饭时间
    morning = Column(Boolean)
    noon = Column(Boolean)
    night = Column(Boolean)
    CanteenID = Column(String(2), ForeignKey("canteens.id"))
    Muslim = Column(Boolean)  # 是否清真
    # level = Column(Integer)  # 楼层   可改为tinyint
    # window = Column(Integer)  # 窗口   可改为tinyint
    """
    ！！！！！！！改为通过id分解   2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号 + 3位dish编号！！！！！！！
    """
    # labels = Column()  # 标签
    photos = Column(String(70))  # 图片  url储存
    SparePhotos = Column(String(70))  # 备用图片   url储存
    likes = Column(Integer)  # 点赞数
    # ManagerId = Column(Integer, ForeignKey("managers.id"))
    manager = relationship("Managers", back_populates="dish")  # 查询添加dish的manager


class Canteens(Base):  # 餐厅
    __tablename__ = "canteens"
    id = Column(String(2), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id
    CanteenName = Column(String(10), index=True)
    CampusID = Column(Integer, index=True)
    LevelNum = Column(Integer)  # 楼层数   可改为tinyint
    # WindowNum =Column(Integer)
    # level = relationship("Levels", back_populates="dish")


class Campus(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    CampusName = Column(String(10), index=True)
    CanteenNum = Column(Integer)


class Levels(Base):
    __tablename__ = "levels"
    id = Column(String(4), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id
    # level = Column(Integer)  # 楼层   可改为tinyint
    WindowNum = Column(Integer)  # 窗口数   可改为tinyint
    # CanteenId = Column(String(2), ForeignKey("canteens.id"))


class Windows(Base):
    __tablename__ = "windows"
    id = Column(String(6), primary_key=True, index=True)
    # 2位餐厅（校区编号+餐厅编号）id  + 2位楼层id +2位 窗口编号
    WindowName = Column(String(10), index=True)
    DishNum = Column(Integer)
    # CanteenId = Column(String(2), ForeignKey("canteens.id"))
    # LevelId = Column(String(4), ForeignKey("levels.id"))
