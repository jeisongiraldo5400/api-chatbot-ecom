from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from sqlalchemy import func
from database import get_session
from models.query_log import QueryLog
from models.services import Service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get('/')
def get_dashboard_metrics(session: Session = Depends(get_session)):
  # 1. Total de consultas realizadas en toda la historia
  total_queries = session.exec(select(func.count(QueryLog.id))).one()

  # 2. Tiempo promedio de respuesta de Gemini
  avg_time = session.exec(select(func.avg(QueryLog.response_time))).one()
  avg_time = round(avg_time, 2) if avg_time else 0.0

  # 3. Consultas agrupadas por Servicio (Ej: Cuántas a SAP, cuántas a VPN)
  # Hacemos un JOIN entre servicios y logs, y agrupamos
  statement_by_service = (
    select(Service.name, func.count(QueryLog.id))
    .join(QueryLog, Service.id == QueryLog.service_id)
    .group_by(Service.name)
  )
  query_by_service = session.exec(statement_by_service).all()

  # 4. Las últimas 5 preguntas (para monitoreo en tiempo real)
  statement_recent = (
    select(QueryLog.query_text, QueryLog.answer_text, QueryLog.created_at)
    .order_by(QueryLog.created_at.desc())
    .limit(5)
  )
  latest_queries = session.exec(statement_recent).all()

  return {
    "overview": {
      "total_queries": total_queries,
      "average_response_time_seconds": avg_time
    },
    "usage_by_service": [
      {
        "service_name": name,
        "query_count": count
      }
      for name, count in query_by_service
    ],
    "recent_activity": [
      {
        "question": q[0],
        "answer_preview": q[1][:80] + "...",
        "date": q[2].strftime("%Y-%m-%d %H:%M:%S")
      }
      for q in latest_queries
    ]
  }
