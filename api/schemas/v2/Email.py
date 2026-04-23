from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from uuid import UUID
from datetime import datetime

class EmailTemplate(str, Enum):
    error = "error"
    email = "email"
    success = "success"
    alert = "alert"
    welcome = "welcome"
    default = "default"
    sette = "sette"
    
class EmailStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    sent = "sent"
    visualized = "visualized"
    failed = "failed"


class Email_send(BaseModel):
    from_email: EmailStr = Field(..., example="sender@example.com", description="Endereço de e-mail do remetente")
    to_email: EmailStr = Field(..., example="recipient@example.com", description="Endereço de e-mail do destinatário")
    password: str = Field(..., example="senha do remetente", description="Senha do e-mail do remetente")
    template: EmailTemplate = Field(default=EmailTemplate.default, example="Parâmetros adicionais", description="Parâmetros do estilo do e-mail, como 'error' para e-mails de erro, 'email' para e-mails padrão, 'success' para e-mails de sucesso, 'alert' para e-mails de alerta, 'welcome' para e-mails de boas-vindas, nada para e-mails de notificações")
    logo: Optional[str] = Field(None, example="http://example.com/logo.png", description="URL do logo a ser incluído no e-mail, se aplicável")
    subject: str = Field(..., example="Assunto do e-mail", description="Assunto do e-mail a ser enviado")
    message: str = Field(..., example="Conteúdo do e-mail", description="Conteúdo do e-mail a ser enviado")
    
class Email_response(BaseModel):
    id: UUID = Field(..., example="12345678-1234-1234-1234-123456789012", description="ID único do e-mail enviado")
    status: EmailStatus = Field(..., example="queued", description="Status do e-mail, como 'queued' para e-mails na fila, 'processing' para e-mails em processamento, 'sent' para e-mails enviados com sucesso, 'visualized' para e-mails visualizados, 'failed' para e-mails que falharam ao enviar")
    description: str = Field(..., example="E-mail enviado para Fila!", description="Descrição do resultado do envio do e-mail")
    
class Email_status_response(BaseModel):
    id: UUID = Field(..., example="12345678-1234-1234-1234-123456789012", description="ID único do e-mail")
    status: EmailStatus = Field(..., example="sent", description="Status atual do e-mail, como 'queued' para e-mails na fila, 'processing' para e-mails em processamento, 'sent' para e-mails enviados com sucesso, 'visualized' para e-mails visualizados, 'failed' para e-mails que falharam ao enviar")
    from_email: EmailStr = Field(..., example="sender@example.com", description="Endereço de e-mail do remetente")
    to_email: EmailStr = Field(..., example="recipient@example.com", description="Endereço de e-mail do destinatário")
    template: EmailTemplate = Field(default=EmailTemplate.default, example="Parâmetros adicionais", description="Parâmetros do estilo do e-mail, como 'error' para e-mails de erro, 'email' para e-mails padrão, 'success' para e-mails de sucesso, 'alert' para e-mails de alerta, 'welcome' para e-mails de boas-vindas, nada para e-mails de notificações")
    logo: Optional[str] = Field(None, example="http://example.com/logo.png", description="URL do logo a ser incluído no e-mail, se aplicável")
    subject: str = Field(..., example="Assunto do e-mail", description="Assunto do e-mail a ser enviado")
    message: str = Field(..., example="Conteúdo do e-mail", description="Conteúdo do e-mail a ser enviado")
    error_message: Optional[str] = Field(None, example="Falha ao enviar e-mail", description="Mensagem de erro detalhada, se o envio do e-mail falhou")
    visualized_at: Optional[datetime] = Field(None, example="2023-01-01T00:00:00", description="Data e hora em que o e-mail foi visualizado")
    sended_at: Optional[datetime] = Field(None, example="2023-01-01T00:00:00", description="Data e hora em que o e-mail foi enviado")
    