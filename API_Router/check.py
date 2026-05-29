from fastapi import Request, HTTPException
import jwt
import os
from API_Router.redis_DB import baza_redis

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"

async def sprawdz_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Brak tokenu")

    czy_zablokowany = await baza_redis.get(f"blacklist_{token}")
    if czy_zablokowany:
        raise HTTPException(status_code=401, detail="Token wygasl")

    try:
        payload = jwt.decode(token, sekretny_klucz, algorithms=[algorytm_jwt])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token wygasl")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Zly token")