import time
from db.models.email import Email
from schemas.v2.Email import EmailStatus
from core.rabbit_connection import RabbitMQClient
import asyncio
import logging
logger = logging.getLogger(__name__)

async def publish_with_retry(message, db, email_id):
    max_attempts = 3
    delay = 0.5

    for attempt in range(1, max_attempts + 1):
        try:
            with RabbitMQClient() as rabbit:
                rabbit.publish(message)

            db.query(Email).filter(Email.id == email_id).update({
                "status": EmailStatus.queued.value
            })
            db.commit()

            return True, attempt

        except Exception as e:
            logger.error(f"Erro ao publicar mensagem (tentativa {attempt}): {str(e)}")
            db.query(Email).filter(Email.id == email_id).update({
                "attempts": attempt,
                "error_message": str(e)
            })
            db.commit()

            if attempt < max_attempts:
                await asyncio.sleep(delay)

    return False, max_attempts