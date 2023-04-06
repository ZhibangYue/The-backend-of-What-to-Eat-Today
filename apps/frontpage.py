# #from .background import *
#
# # frontpage = APIRouter()
#
#
# # 连接数据库的辅助函数
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# # 定义Token 相关常量
#
# # 密钥
# SECRET_KEY = "b81a5447dba59bda81233e037a5f4d6232f0f84a4ca8633c10ce7b57fe916a2b"
#
# # 加密算法
# ALGORITHM = "HS256"
#
# # Token过期时间
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
#
# # 依赖token登录的url
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="./token")
#
#
# # 创建生成新地访问令牌的工具函数
# def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt
#
#
# # 解码并校验接收到的令牌，然后，返回当前用户。
# async def get_current_manager(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#     manager = get_manager(db, username=token_data.username)
#     if manager is None:
#         raise credentials_exception
#     return manager
#
#
# # 交互文档登录
#
# @background.post("/token", status_code=200, response_model=Token, response_description="login successfully",
#                  summary="前台交互文档登录")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     manager = authenticate_manager(form_data.username, form_data.password, db)
#     if not manager:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": manager.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}
#
#
# # 登录
# @background.post("/managers/login", status_code=200, response_model=Token, response_description="login successfully",
#                  summary="登录")
# async def login_for_access_token(form_data: PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     manager = authenticate_manager(form_data.username, form_data.password, db)
#     if not manager:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="用户名或密码错误",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": manager.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}
