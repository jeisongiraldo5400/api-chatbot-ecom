import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

load_dotenv()

postgres_url = os.getenv("DATABASE_URL")

if not postgres_url:
  print("--- DEBUG VARIABLES ---")
  print(f"Variables detectadas: {list(os.environ.keys())}")
  print("-----------------------")
  raise ValueError("La variable de entorno de Postgres no está configurada")

if postgres_url.startswith("postgres://"):
    postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(postgres_url, echo=True)

def init_db():
  SQLModel.metadata.create_all(engine)


def get_session():
  with Session(engine) as session:
    yield session
