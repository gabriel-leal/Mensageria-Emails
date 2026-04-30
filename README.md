# 📧 Mensageria Email API

API de mensageria assíncrona para envio e rastreamento de e-mails, utilizando **FastAPI**, **RabbitMQ**, **Redis** e **Docker**.

---

## 🚀 Visão Geral

Este projeto foi desenvolvido para:

- 📤 Enviar e-mails de forma assíncrona (fila)
- 🔁 Garantir retry em caso de falha
- 📊 Consultar status de envio
- 👁️ Rastrear abertura de e-mails (pixel tracking)
- ⚡ Alta performance com cache (Redis)
- 🐳 Deploy containerizado com Docker

---

## 🧱 Arquitetura

Cliente → API (FastAPI)
↓
RabbitMQ (fila)
↓
Worker (envio)
↓
SMTP (envio real)

Redis (cache)
PostgreSQL (persistência)


---

## 📚 Documentação da API

Acesse a documentação interativa (Swagger):

👉 https://apimensageria.menezesdigital.com.br/docs#/

---

## 🛠️ Tecnologias Utilizadas

- ⚡ FastAPI
- 🐍 Python 3.12
- 🐇 RabbitMQ
- 🧠 Redis
- 🐘 PostgreSQL
- 🐳 Docker / Docker Compose
- 🔁 GitHub Actions (CI/CD)

---

## 📦 Funcionalidades

### 📤 Envio de e-mail

- **Endpoint:** `POST /v2/send-email`
- Envia o e-mail para fila
- Processamento assíncrono via worker

---

### 📊 Consulta de status

- **Endpoint:** `GET /v2/email-status/{email_id}`

Retorna:

- Status do envio
- Mensagem de erro (se houver)
- Data de envio
- Data de visualização

---

### 📬 Listagem de e-mails

- **Endpoint:** `GET /v2/emails`
- Filtro por remetente (`From`)

---

### 👁️ Tracking de abertura

- **Endpoint:** `GET /v2/update-status/{email_id}`

Utiliza pixel invisível no HTML do e-mail:

```html
<img src="https://apimensageria.menezesdigital.com.br/v2/update-status/{email_id}?Status=visualized&Token=TOKEN" width="1" height="1" />

## 🚀 CI/CD

Pipeline automatizado com GitHub Actions:

- 🧪 Executa testes
- 🐳 Build das imagens Docker
- 🚀 Deploy automático na VPS

---

## 🔁 Confiabilidade

O sistema utiliza:

- ✅ Mensagens persistentes no RabbitMQ
- ✅ ACK manual no worker
- ✅ Retry controlado
- ✅ Cache com Redis
- 🚧 (Em evolução) Dead Letter Queue

---

## 📌 Roadmap

- [ ] Dead Letter Queue (DLQ)
- [ ] Dashboard de monitoramento
- [ ] Métricas de entrega
- [ ] Melhor detecção de abertura real
- [ ] Blue-Green deploy completo

---

## 👨‍💻 Autor

**Gabriel Leal Menezes**  
Menezes Digital
