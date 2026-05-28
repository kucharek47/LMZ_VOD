from fastapi import APIRouter, Depends, HTTPException, Request
import jwt
import os
from datetime import datetime, timezone
from API_Router.check import sprawdz_token
from API_Router.request_DB import autoryzuj_uzytkownika, generuj_tokeny_jwt
from API_Router.interfaces import I_Log, I_Refresh
from API_Router.redis_DB import redis_db

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"

router = APIRouter(
    prefix="/user",
    tags=["Logowanie, rejestracja"]
)


@router.post("/login")
async def logowanie(dane_konta: I_Log):
    tokeny = await autoryzuj_uzytkownika(dane_konta.login, dane_konta.haslo)
    if not tokeny:
        raise HTTPException(status_code=401, detail="Zle dane")

    access_token, refresh_token = tokeny
    return {"status": "zalogowano", "access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout")
async def wyloguj(request: Request, dane_uzytkownika: dict = Depends(sprawdz_token)):
    autoryzacja = request.headers.get("Authorization")
    if autoryzacja and autoryzacja.startswith("Bearer "):
        token = autoryzacja.split(" ")[1]
        czas_wygasniecia = dane_uzytkownika.get("exp", 0) - int(datetime.now(timezone.utc).timestamp())
        if czas_wygasniecia > 0:
            await redis_db.setex(f"blacklist_{token}", czas_wygasniecia, "true")

    return {"status": "wylogowano"}


@router.post("/refresh")
async def odswiez_token(dane: I_Refresh):
    try:
        payload = jwt.decode(dane.refresh_token, sekretny_klucz, algorithms=[algorytm_jwt])
        id_uzytkownika = int(payload.get("sub"))

        tokeny = await generuj_tokeny_jwt(id_uzytkownika)
        if not tokeny:
            raise HTTPException(status_code=401, detail="Blad generowania tokenow")

        return {"access_token": tokeny[0], "refresh_token": tokeny[1]}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token wygasl")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Nieprawidlowy token")