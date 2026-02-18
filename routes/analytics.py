from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from sqlalchemy import func
from database import get_session
from models.query_log import QueryLog
from models.services import Service
from models.users import User
from security import get_current_user
from models.document import Document
import os

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get('')
def get_dashboard_metrics(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
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


@router.get("/system-health")
def get_system_health(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  """Obtiene el estado de salud del sistema para el Dashboard de Inicio"""

  # 1. Estado de la IA
  # Verificamos si la API Key de Gemini está configurada
  api_key = os.getenv("GOOGLE_API_KEY")
  ai_status = "connected" if api_key else "disconnected"

  # 2. Total de documentos
  total_docs = session.exec(select(func.count(Document.id)).where(Document.deleted_at == None)).one()

  # 3. Documentos fallidos (Los que quedaron en estado 'ERROR')
  # Ajusta 'ERROR' al string exacto que uses en tu base de datos si es diferente
  failed_docs = session.exec(
    select(func.count(Document.id)).where(Document.status == "ERROR", Document.deleted_at == None)
  ).one()

  # 4. Última sincronización
  # Buscamos la fecha máxima (más reciente) de los documentos subidos con éxito
  last_sync_date = session.exec(
    select(func.max(Document.upload_date)).where(Document.status == "READY", Document.deleted_at == None)
  ).one()

  return {
    "ai_status": ai_status,
    "total_documents": total_docs or 0,
    "last_sync": last_sync_date.isoformat() if last_sync_date else None,
    "failed_documents": failed_docs or 0
  }
