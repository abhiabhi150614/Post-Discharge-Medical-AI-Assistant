from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load env vars before importing other modules that might rely on them
load_dotenv()

from .routers import chat
from .db import engine, Base

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Post Discharge AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
