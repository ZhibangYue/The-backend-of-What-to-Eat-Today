import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from apps import models
from apps.database import engine
from apps.background import background
from apps.frontpage import frontpage

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='今天吃什么',
    description='“今天吃什么”后端接口文档',
    version='0.0.0',
    docs_url='/docs',
    redoc_url='/redocs',
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        '*'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(background, prefix='/background', tags=['后台'])
app.include_router(frontpage, prefix='/frontpage', tags=['前台'])

if __name__ == '__main__':
    uvicorn.run('run:app', reload=True)
