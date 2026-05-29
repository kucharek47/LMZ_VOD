from fastapi import APIRouter, Depends, HTTPException, Request, Response
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
async def logowanie(dane_konta: I_Log, odpowiedz_serwera: Response):
    tokeny = await autoryzuj_uzytkownika(dane_konta.login, dane_konta.haslo)
    if not tokeny:
        raise HTTPException(status_code=401, detail="Zle dane")

    access_token, refresh_token = tokeny

    odpowiedz_serwera.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return {"status": "zalogowano", "access_token": access_token}


@router.post("/logout")
async def wyloguj(request: Request, response: Response, dane_uzytkownika: dict = Depends(sprawdz_token)):
    token = request.cookies.get("access_token")
    if token:
        czas_wygasniecia = dane_uzytkownika.get("exp", 0) - int(datetime.now(timezone.utc).timestamp())
        if czas_wygasniecia > 0:
            await redis_db.setex(f"blacklist_{token}", czas_wygasniecia, "true")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"status": "wylogowano"}


@router.post("/refresh")
async def odswiez_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Brak tokenu odswiezania")

    try:
        payload = jwt.decode(refresh_token, sekretny_klucz, algorithms=[algorytm_jwt])
        id_uzytkownika = int(payload.get("sub"))

        tokeny = await generuj_tokeny_jwt(id_uzytkownika)
        if not tokeny:
            raise HTTPException(status_code=401, detail="Blad generowania tokenow")

        response.set_cookie(key="access_token", value=tokeny[0], httponly=True, samesite="lax", max_age=45 * 60)
        response.set_cookie(key="refresh_token", value=tokeny[1], httponly=True, samesite="lax",
                            max_age=7 * 24 * 60 * 60)

        return {"status": "odswiezono"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token wygasl")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Nieprawidlowy token")


@router.get("/check")
async def sprawdz_autoryzacje(dane_uzytkownika: dict = Depends(sprawdz_token)):
    return {"status": "ok"}