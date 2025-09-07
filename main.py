from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth_router,user_router,admin_router,vocalist_router,kalam_router,studio_router,notification_router,public_router
app = FastAPI(title="My App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],            # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],            # Allow all headers
)


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(vocalist_router)
app.include_router(kalam_router)
app.include_router(studio_router)
app.include_router(notification_router)
app.include_router(public_router)