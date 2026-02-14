import boto3
import os
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()


class S3Service:
  def __init__(self):
    self.s3 = boto3.client(
      's3',
      aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
      aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
      region_name=os.getenv("AWS_REGION")
    )
    self.bucket_name = os.getenv("AWS_S3_BUCKET")

  def upload_file(self, file: UploadFile, s3_folder: str = "documents") -> str:
    """
    Sube un archivo a S3 y retorna la s3_key (ruta).
    """
    try:
      # Generamos la ruta dentro del bucket: ejemplo "documents/manual_sap.pdf"
      file_name = file.filename
      s3_key = f"{s3_folder}/{file_name}"

      # Subir el archivo
      self.s3.upload_fileobj(
        file.file,
        self.bucket_name,
        s3_key,
        ExtraArgs={"ContentType": file.content_type}  # Importante para que el navegador lo lea bien
      )

      return s3_key

    except NoCredentialsError:
      raise Exception("Credenciales de AWS no encontradas")
    except Exception as e:
      raise Exception(f"Error al subir a S3: {str(e)}")

  def get_download_url(self, s3_key: str):
    """Genera una URL temporal (firmada) para descargar el archivo"""
    return self.s3.generate_presigned_url(
      'get_object',
      Params={'Bucket': self.bucket_name, 'Key': s3_key},
      ExpiresIn=3600  # La URL expira en 1 hora
    )


# Instancia global para usar en los routers
s3_client = S3Service()

