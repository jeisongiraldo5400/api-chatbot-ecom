from fastapi import FastAPI
from database import init_db
from routes import users, services, documents, chat, analytics, auth

app = FastAPI(
  title="Chatbot Admin API",
  description="Chatbot API",
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
