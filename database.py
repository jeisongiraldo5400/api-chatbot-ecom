import os
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import event
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

@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET search_path TO public")
    cursor.close()

def init_db():
  SQLModel.metadata.create_all(engine)


def get_session():
  with Session(engine) as session:
    yield session
