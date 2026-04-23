from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

class EmailTemplate(str, Enum):
    error = "error"
    email = "email"
    success = "success"
    alert = "alert"
    welcome = "welcome"
    default = "default"
    sette = "sette"


class Email_send(BaseModel):
    from_email: EmailStr = Field(..., example="sender@example.com", description="Endereço de e-mail do remetente")
    to_email: EmailStr = Field(..., example="recipient@example.com", description="Endereço de e-mail do destinatário")
    subject: str = Field(..., example="Assunto do e-mail", description="Assunto do e-mail a ser enviado")
    message: str = Field(..., example="Conteúdo do e-mail", description="Conteúdo do e-mail a ser enviado")
    password: str = Field(..., example="senha do remetente", description="Senha do e-mail do remetente")
    template: EmailTemplate = Field(default=EmailTemplate.default, example="Parâmetros adicionais", description="Parâmetros do estilo do e-mail, como 'error' para e-mails de erro, 'email' para e-mails padrão, 'success' para e-mails de sucesso, 'alert' para e-mails de alerta, 'welcome' para e-mails de boas-vindas, nada para e-mails de notificações")
    logo: Optional[str] = Field(None, example="http://example.com/logo.png", description="URL do logo a ser incluído no e-mail, se aplicável")
    
class Email_response(BaseModel):
    message: dict = Field(..., example="E-mail enviado com sucesso!", description="Mensagem de resposta indicando o resultado do envio do e-mail")