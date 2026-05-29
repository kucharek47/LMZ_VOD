from fastapi import APIRouter, Depends, HTTPException, Request, Response
import jwt
import os
import json
from datetime import datetime, timezone
from API_Router.check import sprawdz_token
from API_Router.request_DB import autoryzuj_uzytkownika, generuj_tokeny_jwt, pobierz_uzytkownikow_nie_adminow
from API_Router.interfaces import I_Log
from API_Router.redis_DB import baza_redis
from fastapi.encoders import jsonable_encoder

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
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=45 * 60
    )
    odpowiedz_serwera.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return {"status": "zalogowano"}


@router.post("/logout")
async def wyloguj(request: Request, response: Response, dane_uzytkownika: dict = Depends(sprawdz_token)):
    token = request.cookies.get("access_token")
    if token:
        czas_wygasniecia = dane_uzytkownika.get("exp", 0) - int(datetime.now(timezone.utc).timestamp())
        if czas_wygasniecia > 0:
            await baza_redis.setex(f"blacklist_{token}", czas_wygasniecia, "true")

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


@router.get("/all")
async def pobierz_wszystkich():
    klucz_cache = "uzytkownicy_nie_admini"

    try:
        dane_cache = await baza_redis.get(klucz_cache)
        if dane_cache:
            return json.loads(dane_cache)
    except Exception:
        pass

    lista_uzytkownikow = await pobierz_uzytkownikow_nie_adminow()

    try:
        await baza_redis.setex(klucz_cache, 300, json.dumps(jsonable_encoder(lista_uzytkownikow)))
    except Exception:
        pass

    return lista_uzytkownikow