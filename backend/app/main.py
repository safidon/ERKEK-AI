from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router
from app.routes.sessions import router as sessions_router
from app.routes.profile import router as profile_router

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="ERKEK AI",
    version="0.1.0"
)


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# ROUTES
# =====================================================

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(profile_router)


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    return {
        "name": "ERKEK AI",
        "status": "online",
        "version": "0.1.0"
    }