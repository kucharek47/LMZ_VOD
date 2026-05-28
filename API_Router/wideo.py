import os
import re
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from API_Router.check import sprawdz_token
from API_Router.redis_DB import redis_db
from API_Router.request_DB import (
    pobierz_ostatnio_ogladane, pobierz_filmy, pobierz_seriale,
    pobierz_kategorie, pobierz_sciezke_wideo
)
from API_Router.interfaces import I_Ostatnio_Ogladane
from typing import List, Optional

router = APIRouter(
    prefix="/wideo",
    tags=["Odtwarzacz Wideo"]
)


@router.get("/pobierz/{id_wideo}")
async def pobierz_wideo(id_wideo: int, czy_serial: bool = False, dane_uzytkownika: dict = Depends(sprawdz_token)):
    sciezka = await pobierz_sciezke_wideo(id_wideo, czy_serial)

    if not sciezka or not os.path.exists(sciezka):
        raise HTTPException(status_code=404, detail="Nie znaleziono pliku")

    nazwa_pliku = os.path.basename(sciezka)
    return FileResponse(
        path=sciezka,
        media_type="video/mp4",
        filename=nazwa_pliku,
        headers={"Content-Disposition": f"attachment; filename={nazwa_pliku}"}
    )


@router.get("/zrodlo/{id_wideo}")
async def zrodlo_wideo(id_wideo: int, czy_serial: bool = False, dane_uzytkownika: dict = Depends(sprawdz_token)):
    sciezka = await pobierz_sciezke_wideo(id_wideo, czy_serial)

    if not sciezka or not os.path.exists(sciezka):
        raise HTTPException(status_code=404, detail="Nie znaleziono pliku")

    return FileResponse(
        path=sciezka,
        media_type="video/mp4",
        content_disposition_type="inline"
    )


@router.get("/stream/{id_wideo}")
async def stream_wideo(request: Request, id_wideo: int, czy_serial: bool = False,
                       dane_uzytkownika: dict = Depends(sprawdz_token)):
    sciezka = await pobierz_sciezke_wideo(id_wideo, czy_serial)

    if not sciezka or not os.path.exists(sciezka):
        raise HTTPException(status_code=404, detail="Nie znaleziono pliku")

    rozmiar_pliku = os.path.getsize(sciezka)
    naglowek_range = request.headers.get("Range", None)

    if not naglowek_range:
        return FileResponse(sciezka, media_type="video/mp4")

    dopasowanie = re.search(r"bytes=(\d+)-(\d*)", naglowek_range)
    if not dopasowanie:
        raise HTTPException(status_code=400, detail="Zly naglowek Range")

    bajt_start = int(dopasowanie.group(1))
    bajt_koniec = int(dopasowanie.group(2)) if dopasowanie.group(2) else rozmiar_pliku - 1
    bajt_koniec = min(bajt_koniec, rozmiar_pliku - 1)
    rozmiar_chunku = bajt_koniec - bajt_start + 1

    naglowki = {
        "Content-Range": f"bytes {bajt_start}-{bajt_koniec}/{rozmiar_pliku}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(rozmiar_chunku),
        "Content-Type": "video/mp4",
    }

    def generator_wideo():
        with open(sciezka, "rb") as plik:
            plik.seek(bajt_start)
            przeczytane = 0
            while przeczytane < rozmiar_chunku:
                do_odczytu = min(1024 * 1024, rozmiar_chunku - przeczytane)
                chunk = plik.read(do_odczytu)
                if not chunk:
                    break
                przeczytane += len(chunk)
                yield chunk

    return StreamingResponse(generator_wideo(), status_code=206, headers=naglowki)

@router.get("/ostatnio_ogladane", response_model=List[I_Ostatnio_Ogladane])
async def ostatnio_ogladane(dane_uzytkownika: dict = Depends(sprawdz_token)):
    id_uzytkownika = int(dane_uzytkownika.get("sub"))
    wynik = await pobierz_ostatnio_ogladane(id_uzytkownika)

    return wynik
@router.get("/filmy_list")
async def filmy_list(limit: int, kategoria: Optional[str] = None, dane_uzytkownika: dict = Depends(sprawdz_token)):
    if kategoria is None:
        return await pobierz_filmy(limit)
    else:
        return await pobierz_filmy(limit, kategoria)
@router.get("/seriale_list")
async def seriale_list(limit: int, dane_uzytkownika: dict = Depends(sprawdz_token)):
    return await pobierz_seriale(limit)


@router.get("/kategoria_list")
async def kategoria_list(dane_uzytkownika: dict = Depends(sprawdz_token)):
    klucz_cache = "kategorie_list"
    dane_cache = await redis_db.get(klucz_cache)

    if dane_cache:
        return json.loads(dane_cache)

    wynik = await pobierz_kategorie()
    await redis_db.setex(klucz_cache, 3600, json.dumps(jsonable_encoder(wynik)))
    return wynik