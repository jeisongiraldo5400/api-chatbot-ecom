from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.chunk import DocumentChunk
from models.document import Document
from models.query_log import QueryLog
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import time
from security import get_current_user
from models.users import User

router = APIRouter(prefix="/chat", tags=["Chat"])

embeddings_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", output_dimensionality=768)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.0)


@router.post("/ask")
async def ask_chatbot(
  question: str,
  service_id: int,
  session: Session = Depends(get_session),
  current_user: User = Depends(get_current_user)
):
  start_time = time.time()

  try:
    # 1. Convertir la pregunta del usuario en un Vector
    query_vector = embeddings_model.embed_query(question)

    # 2. Búsqueda Vectorial en Postgres con "Hard Filter" de servicio
    # Usamos una consulta SQL pura a través de session para aprovechar pgvector
    # Buscamos los 5 fragmentos más parecidos que pertenezcan al servicio elegido
    statement = (
      select(DocumentChunk.id, DocumentChunk.content, DocumentChunk.page_number)
      .join(Document, Document.id == DocumentChunk.document_id)
      .where(Document.service_id == service_id)
      .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
      .limit(5)
    )

    results = session.exec(statement).all()

    if not results:
      return {"answer": "Lo siento, no encontré información sobre eso en los manuales de este servicio."}

    # 3. Construir el contexto para Gemini
    context_text = "\n\n".join([f"[Página {r.page_number}]: {r.content}" for r in results])

    # 4. Prompt de Sistema (Strict RAG)
    system_prompt = SystemMessage(content=(
      "Eres un asistente técnico de soporte interno. Tu única fuente de verdad es el CONTEXTO proporcionado. "
      "Si la respuesta no está en el contexto, di que no lo sabes. No inventes nada. "
      f"CONTEXTO:\n{context_text}"
    ))

    human_prompt = HumanMessage(content=question)

    # 5. Generar respuesta con Gemini
    ai_response = llm.invoke([system_prompt, human_prompt])

    # 6. Calcular el tiempo de respuesta y guardamos los logs
    end_time = time.time()
    response_time = round(end_time - start_time, 2)

    chunk_ids = [str(r.id) for r in results]

    new_log = QueryLog(
      user_id=current_user.id,
      service_id=service_id,
      query_text=question,
      answer_text=ai_response.content,
      context_chunks_ids=chunk_ids,
      response_time=response_time
    )
    session.add(new_log)
    session.commit()

    return {
      "answer": ai_response.content,
      "sources": [{"page": r.page_number} for r in results]
    }

  except Exception as e:
    print(f"Error en el Chat: {str(e)}")
    raise HTTPException(status_code=500, detail="Error al procesar la consulta")
