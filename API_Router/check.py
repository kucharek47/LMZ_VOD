from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"
bearer_scheme = HTTPBearer()

def czy_token_wazny(token: str) -> bool:
    try:
        jwt.decode(token, sekretny_klucz, algorithms=[algorytm_jwt])
        return True
    except jwt.PyJWTError:
        return False


async def sprawdz_token(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Brak autoryzacji")

    czarna_lista = await redis_db.get(f"blacklist_{token}")
    if czarna_lista:
        raise HTTPException(status_code=401, detail="Token uniewazniony")

    try:
        payload = jwt.decode(token, sekretny_klucz, algorithms=[algorytm_jwt])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token wygasl")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Nieprawidlowy token")
