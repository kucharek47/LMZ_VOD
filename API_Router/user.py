from fastapi import APIRouter, Depends, HTTPException
import jwt
import os
from API_Router.check import sprawdz_token
from API_Router.request_DB import autoryzuj_uzytkownika, generuj_tokeny_jwt
from API_Router.interfaces import I_Log
from API_Router.interfaces import I_Refresh

sekretny_klucz = os.getenv("KEY_S", "tymczasowy_sekretny_klucz")
algorytm_jwt = "HS256"

router = APIRouter(
    prefix="/user",
    tags=["Logowanie, rejestracja"]
)

@router.post("/login")
async def logowanie(dane_konta: I_Log):
    tokeny = await autoryzuj_uzytkownika(dane_konta.nazwa, dane_konta.haslo)
    if not tokeny:
        raise HTTPException(status_code=401, detail="Zle dane")

    access_token, refresh_token = tokeny
    return {"status": "zalogowano", "access_token": access_token, "refresh_token": refresh_token}


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


@router.get("/login_test")
async def login_test(dane_uzytkownika: dict = Depends(sprawdz_token)):
    return {"status": "sukces", "id_uzytkownika": dane_uzytkownika.get("sub")}