import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY")

async def validade_token(Authorization: str = Header(...)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Token não informado")
    
    # sua lógica de validação aqui
    if Authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Token inválido")
    return True