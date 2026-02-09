from fastapi import FastAPI
from database import init_db
from routes import users

app = FastAPI(
  title="Chatbot Admin API",
  description="Chatbot API",
)


# create table init app
@app.on_event("startup")
def on_startup():
  init_db()


# Routes
app.include_router(users.router)
