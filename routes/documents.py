from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlmodel import Session, select, delete
from uuid import UUID
from database import get_session
from models.document import Document, DocumentStatus
from services.s3_service import s3_client
import hashlib
from models.users import User
from security import get_current_user

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from models.chunk import DocumentChunk
import os

import tempfile  # Librería nativa de Python
from langchain_community.document_loaders import PyPDFLoader

router = APIRouter(prefix="/documents", tags=['Documents'])


async def process_document_task(document_id: UUID, session_factory):
  with session_factory() as session:
    try:
      db_doc = session.get(Document, document_id)
      if not db_doc: return

      db_doc.status = DocumentStatus.PROCESSING
      session.add(db_doc)
      session.commit()

      # --- CAMBIO AQUÍ: Descargamos el archivo manualmente ---
      # Creamos un archivo temporal para no llenar el disco del servidor
      with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        # Usamos tu cliente de boto3 para bajar el archivo de S3
        s3_client.s3.download_fileobj(s3_client.bucket_name, db_doc.s3_key, tmp_file)
        tmp_path = tmp_file.name

      # Ahora usamos PyPDFLoader que NO pide 'unstructured' ni 'pi_heif'
      loader = PyPDFLoader(tmp_path)
      raw_documents = loader.load()

      # Borrar el archivo temporal después de leerlo
      if os.path.exists(tmp_path):
        os.remove(tmp_path)
      # --- FIN DEL CAMBIO ---

      text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
      )
      chunks = text_splitter.split_documents(raw_documents)

      embeddings_model = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        output_dimensionality=768
      )

      for chunk in chunks:
        vector = embeddings_model.embed_query(chunk.page_content)

        new_chunk = DocumentChunk(
          document_id=db_doc.id,
          content=chunk.page_content,
          page_number=chunk.metadata.get("page", 1),
          embedding=vector
        )
        session.add(new_chunk)

      db_doc.status = DocumentStatus.READY
      session.add(db_doc)
      session.commit()
      print(f"Documento {document_id} procesado con éxito.")

    except Exception as e:
      print(f"Error procesando documento {document_id}: {str(e)}")
      db_doc.status = DocumentStatus.ERROR
      session.add(db_doc)
      session.commit()


@router.post("/upload")
async def upload_document(
  background_tasks: BackgroundTasks,
  service_id: int = Form(...),
  title: str = Form(...),
  file: UploadFile = File(...),
  session: Session = Depends(get_session),
  current_user: User = Depends(get_current_user)
):
  if not file.filename.endswith(".pdf"):
    raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

  try:
    file_content = await file.read()
    file_hash = hashlib.md5(file_content).hexdigest()

    await file.seek(0)

    s3_key = s3_client.upload_file(file)

    new_doc = Document(
      title=title,
      service_id=service_id,
      s3_key=s3_key,
      hash_md5=file_hash,
      status=DocumentStatus.PENDING
    )

    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)

    from database import engine
    from sqlmodel import Session as SQLSession

    def session_factory():
      return SQLSession(engine)

    background_tasks.add_task(process_document_task, new_doc.id, session_factory)

    return {"message": "Procesamiento iniciado", "document_id": new_doc.id}

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")


@router.get("")
def get_all_documents(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  """Obtiene todos los documentos ordenados por el más reciente"""
  # Usamos desc() para que los últimos que subas aparezcan arriba en tu tabla
  statement = select(Document).order_by(Document.upload_date.desc())
  documents = session.exec(statement).all()

  return documents


@router.delete("/{document_id}")
def delete_document(document_id: UUID, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
  """Elimina un documento y todos sus vectores de entrenamiento"""
  db_doc = session.get(Document, document_id)

  if not db_doc:
    raise HTTPException(status_code=404, detail="Documento no encontrado")

  # IMPORTANTE: Aquí eliminamos el registro de la DB
  # (Opcionalmente, más adelante podríamos decirle a boto3 que también borre el PDF físico de S3)
  session.delete(db_doc)
  session.commit()

  return {"message": "Documento y vectores de entrenamiento eliminados correctamente"}


@router.get("/{document_id}/view")
def view_document(document_id: UUID, session: Session = Depends(get_session)):
  """Genera una URL segura y temporal para ver el PDF directamente desde S3"""

  # 1. Buscar el documento en la base de datos
  db_doc = session.get(Document, document_id)
  if not db_doc:
    raise HTTPException(status_code=404, detail="Documento no encontrado")

  try:
    # 2. Generar la URL firmada (por defecto la configuramos para que dure 1 hora)
    presigned_url = s3_client.get_download_url(db_doc.s3_key)

    # 3. Retornar la URL al frontend
    return {
      "title": db_doc.title,
      "url": presigned_url
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error al generar el enlace de S3: {str(e)}")


@router.post("/{document_id}/reprocess")
async def reprocess_document(
  document_id: UUID,
  background_tasks: BackgroundTasks,
  session: Session = Depends(get_session),
  current_user: User = Depends(get_current_user)
):
  """Limpia los errores y vuelve a enviar el documento a la cola de procesamiento IA"""

  # 1. Buscar el documento
  db_doc = session.get(Document, document_id)

  if not db_doc:
    raise HTTPException(status_code=404, detail="Documento no encontrado")

  # 2. Solo permitimos reprocesar los que fallaron
  if db_doc.status != DocumentStatus.ERROR:
    raise HTTPException(status_code=400, detail="Solo se pueden reprocesar documentos en estado ERROR")

  try:
    # 3. Limpiar fragmentos (chunks) huérfanos
    # Si el proceso anterior falló por la mitad, borramos la basura para no duplicar datos
    statement = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    session.exec(statement)

    # 4. Cambiamos el estado de vuelta a PENDING para la UI
    db_doc.status = DocumentStatus.PENDING
    session.add(db_doc)
    session.commit()

    # 5. Preparamos la fábrica de sesiones para el BackgroundTask (Igual que en upload)
    from database import engine
    from sqlmodel import Session as SQLSession

    def session_factory():
      return SQLSession(engine)

    # 6. Reutilizamos tu función original enviándola al fondo
    background_tasks.add_task(process_document_task, db_doc.id, session_factory)

    return {"message": "Reprocesamiento iniciado", "document_id": db_doc.id}

  except Exception as e:
    session.rollback()
    raise HTTPException(status_code=500, detail=f"Error al intentar reprocesar: {str(e)}")
