import fastapi
#import uvicorn
from fastapi.responses import StreamingResponse
from utils.logger import Logger
#from utils.config import Config


web = fastapi.FastAPI()
@web.get("/get_logs")
async def get_logs():
    return StreamingResponse(Logger._generate_log_output(), media_type="text/plain")


#if __name__ == "__main__":
#    uvicorn.run(web, host=Config().get("host"), port=Config().get("port"))