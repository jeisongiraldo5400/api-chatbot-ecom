from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import users, services, documents, chat, analytics, auth
import os

app = FastAPI(
  title="Chatbot Admin API",
  description="Chatbot API",
)

origins_raw = os.getenv("ALLOWED_ORIGINS", "")

origins = [origin.strip() for origin in origins_raw.split(",") if origin]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,  # Permite peticiones de estas URLs
  allow_credentials=True,  # Permite envío de cookies y headers de autorización (como tu JWT)
  allow_methods=["*"],  # Permite todos los métodos (GET, POST, PATCH, DELETE)
  allow_headers=["*"],  # Permite todos los headers
)


# create table init app
@app.on_event("startup")
def on_startup():
  init_db()


# Routes
app.include_router(users.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
