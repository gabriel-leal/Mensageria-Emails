from datetime import datetime
from uuid import uuid4
from fastapi import Depends, HTTPException, status, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from auth.hash import encrypt_password
from core.retry_rabbitmq import publish_with_retry
from db.session import get_db
from schemas.v2.Email import Email_status_response
from db.models.email import Email
from schemas.v2.Email import Email_send, Email_response, EmailStatus
import logging
logger = logging.getLogger(__name__)

async def send_email_service(email: Email_send, db: Session = Depends(get_db), request: Request = None):
    email_id = str(uuid4())

    try:
        db_email = Email(
            id=email_id,
            from_email=email.from_email,
            to_email=email.to_email,
            subject=email.subject,
            message=email.message,
            password=encrypt_password(email.password),
            status=EmailStatus.processing.value,
            template=email.template,
            logo=email.logo,
            attempts=0,
            created_at=text('CURRENT_TIMESTAMP'),
            updated_at=text('CURRENT_TIMESTAMP')
        )
        db.add(db_email)
        db.commit()
        
        message = {
            "id": email_id,
            "email": email.message,
            "from": email.from_email,
            "to": email.to_email,
            "subject": email.subject,
            "parameters": email.template.value,
            "logo": email.logo
        }
        succes, attempts = await publish_with_retry(message, db, email_id)
        if not succes:
            logger.error(f"Falha ao publicar após {attempts} tentativas")

            db.query(Email).filter(Email.id == email_id).update({
                "status": EmailStatus.failed.value,
                "updated_at": text('CURRENT_TIMESTAMP'),
                "error_message": f"Falha após {attempts} tentativas"
            })
            db.commit()

            return Response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=Email_response(
                    id=email_id,
                    status=EmailStatus.failed,
                    description="Falha ao enviar e-mail para fila"
                ).model_dump(mode="json")
            )
        logger.info(f"E-mail enviado para a fila: {message}")
        redis = request.app.state.redis
        cached = await redis.get(f"email_status:{email_id}")
        if cached:
            await redis.delete(f"email_status:{email_id}")
        cached_from = await redis.get(f"emails_from:{email.from_email}")
        if cached_from:
            await redis.delete(f"emails_from:{email.from_email}")
        return Email_response(id=email_id, status=EmailStatus.queued, description="E-mail enviado para Fila!")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao enviar e-mail: {str(e)}"
)
        
        
async def email_status_service(email_id: str, db: Session = Depends(get_db), request: Request = None):
    try:
        redis = request.app.state.redis
        cached = await redis.get(f"email_status:{email_id}")
        if cached:
            return Email_status_response.model_validate_json(cached)
        else:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="E-mail não encontrado")
            
            response_data = {
                "id": email.id,
                "status": EmailStatus(email.status),
                "from_email": email.from_email,
                "to_email": email.to_email,
                "template": email.template,
                "logo": email.logo,
                "subject": email.subject,
                "message": email.message,
            }
            if email.error_message:
                response_data["error_message"] = email.error_message
            if email.visualized_at:
                response_data["visualized_at"] = email.visualized_at
            if email.sent_at:
                response_data["sended_at"] = email.sent_at

            await redis.set(f"email_status:{email_id}", Email_status_response(**response_data).model_dump_json(), ex=600)
            return Email_status_response(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar status do e-mail: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao consultar status do e-mail: {str(e)}"
)
        
        
async def emails_status_service(From: str, db: Session = Depends(get_db), request: Request = None):
    try:
        redis = request.app.state.redis
        cached = await redis.get(f"emails_from:{From}")
        if cached:
            return [Email_status_response.model_validate_json(item) for item in eval(cached)]
        else:
            emails = db.query(Email).filter(Email.from_email == From).all()
            if not emails:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="E-mails não encontrados")
            
            response = []
            for email in emails:
                data = {
                    "id": email.id,
                    "status": EmailStatus(email.status),
                    "from_email": email.from_email,
                    "to_email": email.to_email,
                    "template": email.template,
                    "logo": email.logo,
                    "subject": email.subject,
                    "message": email.message,
                }

                if email.error_message:
                    data["error_message"] = email.error_message
                if email.visualized_at:
                    data["visualized_at"] = email.visualized_at
                if email.sent_at:
                    data["sended_at"] = email.sent_at

                response.append(Email_status_response(**data))
            await redis.set(f"emails_from:{From}", str([item.model_dump_json() for item in response]), ex=600)
            return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar status do e-mail: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao consultar status do e-mail: {str(e)}"
)
        

async def update_status_service(email_id: str, Status: EmailStatus, Token: str, db: Session = Depends(get_db), request: Request = None):
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="E-mail não encontrado")
        if email.status == EmailStatus.visualized.value:
            return Response(content=b"", media_type="image/png")
        if (datetime.now() - email.sent_at).seconds < 20:
            return Response(content=b"", media_type="image/png")
        if Status == EmailStatus.visualized:
            email.visualized_at = text('CURRENT_TIMESTAMP')
            email.updated_at = text('CURRENT_TIMESTAMP')
            email.status = Status.value
        db.commit()
        redis = request.app.state.redis
        cached = await redis.get(f"email_status:{email_id}")
        if cached:
            await redis.delete(f"email_status:{email_id}")
        cached_from = await redis.get(f"emails_from:{email.from_email}")
        if cached_from:
            await redis.delete(f"emails_from:{email.from_email}")
        return Response(
            content=b"",
            media_type="image/png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar status do e-mail: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao atualizar status do e-mail: {str(e)}"
    )