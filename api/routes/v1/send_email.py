from fastapi import APIRouter, Depends, Request, Header
import os
from fastapi_limiter.depends import RateLimiter
from schemas.v1.Email import Email_send, Email_response
import pika
import json
from auth.auth import validade_token
import logging
logger = logging.getLogger(__name__)

async def email_identifier(request: Request):
    try:
        body = await request.json()
        return body.get("to_email", "unknown")
    except:
        return "unknown"



router = APIRouter()

@router.post("/send-email", dependencies=[Depends(validade_token), Depends(RateLimiter(times=5, seconds=3600, identifier=email_identifier))], response_model=Email_response)
async def send_email(email: Email_send):
    try:
        RABBITMQ_USER = os.getenv("RABBITMQ_USER")
        RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
        RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(RABBITMQ_HOST, 5672, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='email')
        
        message = {
            "email": email.message,
            "from": email.from_email,
            "to": email.to_email,
            "subject": email.subject,
            "password": email.password,
            "parameters": email.template,
            "logo": email.logo
        }
        channel.basic_publish(exchange='', routing_key='email',  body=json.dumps(message))
        logger.info(f"E-mail enviado para a fila: {message}")
        return Email_response(message={"message": "E-mail enviado com sucesso!"})
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        return Email_response(message={"message": f"Erro ao enviar e-mail: {str(e)}"})
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()