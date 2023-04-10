from .background import *

frontpage = APIRouter()


@frontpage.get("/")
async def star():
    return "Hello,World"

