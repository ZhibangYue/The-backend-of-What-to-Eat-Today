from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/demo"
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://supereat:0nlineTek@eat.mysql.database.azure.com:3306/eat"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
