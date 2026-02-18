from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import users, services, documents, chat, analytics, auth, categories
import os

app = FastAPI(
  title="Chatbot Admin API",
  description="Chatbot API",
)

origins_raw = os.getenv("ALLOWED_ORIGINS", "")

origins = [origin.strip() for origin in origins_raw.split(",") if origin]

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Permite peticiones de estas URLs
  allow_credentials=False,  # Permite envío de cookies y headers de autorización (como tu JWT)
  allow_methods=["*"],  # Permite todos los métodos (GET, POST, PATCH, DELETE)
  allow_headers=["*"],  # Permite todos los headers
)


# Routes
app.include_router(users.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
