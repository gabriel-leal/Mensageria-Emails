from dotenv import load_dotenv
load_dotenv()
import json 
import pika
import os
import time
from femail import envia_email
from db.session import SessionLocal
from db.models.email import Email
from core.Email import EmailStatus
from sqlalchemy import text
from core.logger_conf import setup_logger
from auth.hash import decrypt_password
import logging

setup_logger()
logger = logging.getLogger(__name__)


RABBITMQ_USER = os.getenv("RABBITMQ_USER")
if not RABBITMQ_USER:
    raise ValueError("RABBITMQ_USER environment variable is not set")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
if not RABBITMQ_PASSWORD:
    raise ValueError("RABBITMQ_PASSWORD environment variable is not set")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
if not RABBITMQ_HOST:
    raise ValueError("RABBITMQ_HOST environment variable is not set")

db = SessionLocal()

# Retry loop
for i in range(10):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(RABBITMQ_HOST, 5672, '/', credentials)
        connection_rabbit = pika.BlockingConnection(parameters)
        logger.info("Conectado ao RabbitMQ - SUCESSO FINAL")
        db.execute(text("SELECT 1"))
        logger.info("✅ Banco conectado com sucesso!")
        break
    except pika.exceptions.AMQPConnectionError:
        logger.warning(f"RabbitMQ e Postgres não está pronto, tentando novamente em 5s... ({i+1}/10)")
        time.sleep(5)
else:
    raise Exception("Não foi possível conectar ao RabbitMQ após várias tentativas.")


def callback(ch, method, properties, body):
    data = json.loads(body)
    email_id = data["id"]
    email = data['email']
    from_address = data['from']
    to_address = data['to']
    subject = data['subject']
    parameters = data.get('parameters', 'email')
    logo = data.get('logo', None) 
    
    db.query(Email).filter(Email.id == email_id).update({Email.status: EmailStatus.processing})
    db.commit()

    try:
        password = decrypt_password(db.query(Email).filter(Email.id == email_id).first().password)
        envia_email(email, from_address, to_address, subject, password, parameters, logo, email_id)
        db.query(Email).filter(Email.id == email_id).update({Email.status: EmailStatus.sent})
        db.query(Email).filter(Email.id == email_id).update({Email.sent_at: text('CURRENT_TIMESTAMP')})
        db.commit()
        logger.info(f"Email sent to {to_address}")
    except Exception as e:
        logger.error(f"Error sending email to {to_address}: {e}")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(RABBITMQ_HOST, 5672, '/', credentials)
connection_rabbit = pika.BlockingConnection(parameters)
channel = connection_rabbit.channel()

channel.queue_declare(queue='email')
channel.basic_consume(queue='email', on_message_callback=callback, auto_ack=True)
print('Waiting for messages.... To exit press CTRL+C')
channel.start_consuming()


