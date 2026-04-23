from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
import uvicorn
from contextlib import asynccontextmanager
from routes.v1.send_email import router as send_email_router_v1
from routes.v2.email import router as send_email_router_v2
from core.logger_conf import setup_logger
import logging
from db.session import engine
from db.create_database import create_database_if_not_exists
from sqlalchemy import text

setup_logger()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicação...")

    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        raise RuntimeError("REDIS_URL não definida")

    redis = aioredis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )

    try:
        await FastAPILimiter.init(redis)
        app.state.redis = redis
        logger.info("✅ Redis conectado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar no Redis: {e}")
        raise RuntimeError("Erro no Redis")

    try:
        create_database_if_not_exists()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Banco conectado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar no banco: {e}")
        raise RuntimeError("Erro no banco")

    yield

    await redis.close()
    await redis.connection_pool.disconnect()

    logger.info("Aplicação finalizada.")
    

app = FastAPI(
    title="📧 Menezes Digital - API de Mensageria",
    description="""
API para envio e rastreamento de e-mails com suporte a filas (RabbitMQ),
cache (Redis) e monitoramento de status.

---

## 🚀 Funcionalidades

- Envio assíncrono de e-mails
- Rastreamento de status em tempo real
- Detecção de abertura (pixel tracking)
- Retry automático em falhas
- Cache com Redis para alta performance

---

## 📊 Status dos E-mails

| Status        | Descrição |
|--------------|----------|
| processing   | Em processamento |
| queued       | Enviado para fila |
| sent         | Enviado com sucesso |
| failed       | Falha no envio |
| visualized   | E-mail aberto |

---

## ⚠️ Observação sobre rastreamento

A detecção de abertura (`visualized`) utiliza pixel invisível.
Clientes como Gmail e Outlook podem pré-carregar imagens,
gerando falsos positivos.

---

## 🔒 Segurança

- Autenticação via Token
- Rate limit: 5 requisições por hora
""",
    version="2.0.0",
    contact={
        "name": "Menezes Digital",
        "url": "https://menezesdigital.com.br",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# rotas
app.include_router(send_email_router_v1, prefix="/v1", tags=["E-mail/v1"], deprecated=True)
app.include_router(send_email_router_v2, prefix="/v2", tags=["E-mail/v2"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3500, log_level="debug")

