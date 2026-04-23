from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import text
from schemas.v2.Email import Email_send, Email_response, EmailStatus, Email_status_response
from auth.auth import validade_token
import logging
logger = logging.getLogger(__name__)
from uuid import uuid4
from db.session import get_db
from sqlalchemy.orm import Session
from db.models.email import Email
from core.retry_rabbitmq import publish_with_retry
from auth.hash import encrypt_password
from fastapi import Request

async def email_identifier(request: Request):
    try:
        body = await request.json()
        return body.get("to_email", "unknown")
    except:
        return "unknown"



router = APIRouter()

@router.post("/send-email", dependencies=[Depends(validade_token), Depends(RateLimiter(times=5, seconds=3600, identifier=email_identifier))], response_model=Email_response, status_code=status.HTTP_200_OK, 
description="""

Envia um e-mail de forma assíncrona utilizando fila (RabbitMQ).

---

## ⚙️ Funcionamento

1. O e-mail é registrado no banco
2. É enviado para uma fila
3. Um worker processa o envio
4. O status pode ser consultado posteriormente

---

## 📌 Observações

- O envio não é imediato (assíncrono)
- Em caso de falha, o sistema realiza tentativas automáticas
- O status inicial será `processing` ou `queued`
- O campo `template` deve ser um dos valores disponíveis acima, se não passar nada vai ser o template padrão
- O campo `logo` é opcional e pode ser usado para personalizar o e-mail com a logo da sua empresa. Se não for fornecido, o template padrão será usado sem logo.

---

### 📧 Templates disponíveis:

#### 🟦 Template padrão
<img src="https://menezesdigital.com.br/images/templates/padrao.png" width="400"/>

#### 🟧 Template Alerta
<img src="https://menezesdigital.com.br/images/templates/alert.png" width="400"/>

#### 🟦 Template Email
<img src="https://menezesdigital.com.br/images/templates/email.png" width="400"/>

#### 🟩 Template Sucesso
<img src="https://menezesdigital.com.br/images/templates/success.png" width="400"/>

#### 🟥 Template erro
<img src="https://menezesdigital.com.br/images/templates/error.png" width="400"/>

#### 🟦 Template bem-vindo
<img src="https://menezesdigital.com.br/images/templates/welcome.png" width="400"/>

""")
async def send_email(email: Email_send, db: Session = Depends(get_db), request: Request = None):
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
            attempts=0
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
        

@router.get("/email-status/{email_id}", dependencies=[Depends(validade_token), Depends(RateLimiter(times=5, seconds=3600))], response_model=Email_status_response, response_model_exclude_none=True, status_code=status.HTTP_200_OK, description="""
     
Consulta o status de um e-mail específico.

---

## ⚡ Performance
- Cache em Redis (10 minutos)

---

## 📊 Retorno

Inclui:

- Status atual
- Dados do envio
- Datas importantes

---

## 📅 Campos de data

- `sended_at` → envio
- `visualized_at` → abertura

---

## ⚠️ Observação

Abertura baseada em pixel pode não ser 100% precisa.       
            
""")
async def email_status(email_id: str, db: Session = Depends(get_db), request: Request = None):
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
        

@router.get("/emails", dependencies=[Depends(validade_token), Depends(RateLimiter(times=5, seconds=3600))], response_model=list[Email_status_response], response_model_exclude_none=True , status_code=status.HTTP_200_OK, description="""
Retorna todos os e-mails enviados por um remetente.

---

## 🔎 Parâmetro

- `From` → e-mail do remetente

---

## ⚡ Performance

- Cache Redis (10 minutos)

---

## 📊 Retorno

Lista contendo:

- ID
- Status
- Destinatário
- Conteúdo
- Datas

---

## 📌 Uso comum

- Histórico de envios
- Auditoria
- Monitoramento            
""")
async def email_status(From: str, db: Session = Depends(get_db), request: Request = None):
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
        
@router.get("/update-status/{email_id}", dependencies=[Depends(RateLimiter(times=5, seconds=3600))], response_description="Atualiza o status do e-mail", status_code=status.HTTP_200_OK, description="""
Este endpoint é usado como pixel de rastreamento.

Quando o e-mail é aberto, o cliente carrega uma imagem invisível,
disparando essa rota automaticamente.

Isso atualiza o status para `visualized`.
""")
async def update_status(email_id: str, Status: EmailStatus, Token: str, db: Session = Depends(get_db), request: Request = None):
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