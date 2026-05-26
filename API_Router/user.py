from fastapi import APIRouter, Depends, HTTPException
from API_Router.check import sprawdz_token
from API_Router.request_DB import autoryzuj_uzytkownika, pobierz_uzytkownika
from API_Router.interfaces import I_Log

router = APIRouter(
    prefix="/user",
    tags=["Logowanie, rejestracja"]
)

@router.post("/login")
async def logowanie(dane_konta: I_Log):
    stan_logowania = autoryzuj_uzytkownika(dane_konta)
    if not stan_logowania:
        raise HTTPException(status_code=401, detail="Zle dane")
    return {"status": "zalogowano", "token": "bezpieczny_klucz"}

@router.post("/register")
async def logowanie(dane_konta: I_Log):
    stan_logowania = autoryzuj_uzytkownika(dane_konta)
    if not stan_logowania:
        raise HTTPException(status_code=401, detail="Zle dane")
    return {"status": "zalogowano", "token": "bezpieczny_klucz"}

@router.get("/profil")
async def profil(id: int, wazny_token: str = Depends(sprawdz_token)):
    dane_uzytkownika = pobierz_uzytkownika(id)
    return {"dane": dane_uzytkownika}
@router.get("/avatars")
async def avatars():
    return {"name": "path"}