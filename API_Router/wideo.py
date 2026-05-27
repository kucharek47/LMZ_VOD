from fastapi import APIRouter, Depends
from API_Router.check import sprawdz_token
from API_Router.request_DB import pobierz_wideo_info
from os import getenv

router = APIRouter(
    prefix="/wideo",
    tags=["Odtwarzacz Wideo"]
)

@router.get("/lista")
async def lista_materialow(wazny_token: str = Depends(sprawdz_token)):
    lista_filmow = [{"id": 1, "tytul": "Hakerzy"}, {"id": 2, "tytul": "Matrix"}]
    return {"katalog": lista_filmow}

@router.get("/stream/{id}")
async def odtwarzaj_wideo(id: int, wazny_token: str = Depends(sprawdz_token)):
    dane_pliku = pobierz_wideo_info(id)
    url = f"https://cdn.serwer.pl/media/{dane_pliku['id']}"
    return {"url": url}
@router.get("/zezwolenie_na_pobieranie")
async def zezwolenie_na_pobieranie(wazny_token: str = Depends(sprawdz_token)):
    return getenv("ENABLE_DOWNLOADS", "false") == "true"