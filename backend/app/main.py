from fastapi import FastAPI

from app.routes.chat import router as chat_router

app = FastAPI(
    title="ERKEK AI",
    version="0.1.0"
)

app.include_router(chat_router)


@app.get("/")
def home():
    return {
        "name": "ERKEK AI",
        "status": "online",
        "version": "0.1.0"
    }