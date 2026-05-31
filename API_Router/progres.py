from typing import Optional
from fastapi import APIRouter, Depends
from API_Router.check import sprawdz_token
from API_Router.request_DB import aktualizuj_postep, pobierz_czas_wideo, reczna_zmiana_statusu
from API_Router.interfaces import I_Postep, I_WideoCzas, I_Zmiana_Statusu

router = APIRouter(
    prefix="/progress",
    tags=["Zarzadzanie czasem ogladania"]
)

@router.post("/update")
async def zaktualizuj_czas(dane_postepu: I_Postep, dane_uzytkownika: dict = Depends(sprawdz_token)):
    id_uzytkownika = int(dane_uzytkownika.get("sub"))
    await aktualizuj_postep(id_uzytkownika, dane_postepu)
    return {"status": "zaktualizowano"}

@router.post("/status")
async def zmien_status(dane_zmiany: I_Zmiana_Statusu, dane_uzytkownika: dict = Depends(sprawdz_token)):
    id_uzytkownika = int(dane_uzytkownika.get("sub"))
    await reczna_zmiana_statusu(id_uzytkownika, dane_zmiany)
    return {"status": "zmieniono"}

@router.get("/time/{media_id}", response_model=I_WideoCzas)
async def pobierz_czas(media_id: int, odcinek_id: Optional[int] = None, dane_uzytkownika: dict = Depends(sprawdz_token)):
    id_uzytkownika = int(dane_uzytkownika.get("sub"))
    czas = await pobierz_czas_wideo(id_uzytkownika, media_id, odcinek_id)
    return I_WideoCzas(obejrzany_czas=czas)