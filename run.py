import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

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

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="public/assets"), name="static")
app.mount("/pics", StaticFiles(directory="public/pics"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        '*'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory="public")


@app.get("/")
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


app.include_router(frontpage, prefix='/frontpage', tags=['前台'])
app.include_router(background, prefix='/background', tags=['后台'])


if __name__ == '__main__':
    uvicorn.run('run:app', reload=True)
