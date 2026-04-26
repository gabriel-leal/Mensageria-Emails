from fastapi import APIRouter, Depends, Request, status
from fastapi_limiter.depends import RateLimiter
from schemas.v2.Email import Email_send, Email_response, EmailStatus, Email_status_response
from auth.auth import validade_token
from db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Request
from services.v2.email import email_status_service, emails_status_service, send_email_service, update_status_service

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
    return await send_email_service(email, db, request)
        

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
    return await email_status_service(email_id, db, request)
        

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
async def emails_status(From: str, db: Session = Depends(get_db), request: Request = None):
    return await emails_status_service(From, db, request)
        

@router.get("/update-status/{email_id}", dependencies=[Depends(RateLimiter(times=5, seconds=3600))], response_description="Atualiza o status do e-mail", status_code=status.HTTP_200_OK, description="""
Este endpoint é usado como pixel de rastreamento.

Quando o e-mail é aberto, o cliente carrega uma imagem invisível,
disparando essa rota automaticamente.

Isso atualiza o status para `visualized`.
""")
async def update_status(email_id: str, Status: EmailStatus, Token: str, db: Session = Depends(get_db), request: Request = None):
    return await update_status_service(email_id, Status, Token, db, request)