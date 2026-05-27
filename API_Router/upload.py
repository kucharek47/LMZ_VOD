import os
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse

router = APIRouter(
    prefix="/upload",
    tags=["Pobieranie zdjec, wideo i streaming"]
)

sciezka_img = "img"
sciezka_video = "video"

os.makedirs(sciezka_img, exist_ok=True)
os.makedirs(sciezka_video, exist_ok=True)

#admin
@router.post("/")
async def wgraj_plik(plik: UploadFile = File(...)):
    return
    sciezka_zapisu = os.path.join(sciezka_img, plik.filename)

    zawartosc = await plik.read()
    with open(sciezka_zapisu, "wb") as f:
        f.write(zawartosc)

    return {
        "nazwa": plik.filename,
        "url": f"/img/{plik.filename}"
    }


@router.get("/video/pobierz/{nazwa_pliku}")
async def pobierz_video(nazwa_pliku: str):
    bezpieczna_nazwa = os.path.basename(nazwa_pliku)
    sciezka_pliku = os.path.join(sciezka_video, bezpieczna_nazwa)

    return FileResponse(
        sciezka_pliku,
        media_type="application/octet-stream",
        filename=bezpieczna_nazwa
    )


@router.get("/video/plik/{nazwa_pliku}")
async def ogladaj_video(nazwa_pliku: str):
    bezpieczna_nazwa = os.path.basename(nazwa_pliku)
    sciezka_pliku = os.path.join(sciezka_video, bezpieczna_nazwa)

    return FileResponse(sciezka_pliku, media_type="video/mp4")


@router.get("/video/strumien/{nazwa_pliku}")
async def strumien_video(nazwa_pliku: str, request: Request):
    bezpieczna_nazwa = os.path.basename(nazwa_pliku)
    sciezka_pliku = os.path.join(sciezka_video, bezpieczna_nazwa)

    rozmiar_pliku = os.path.getsize(sciezka_pliku)
    naglowek_zakresu = request.headers.get("Range")

    if not naglowek_zakresu:
        return FileResponse(sciezka_pliku, media_type="video/mp4")

    start_str, koniec_str = naglowek_zakresu.replace("bytes=", "").split("-")
    start = int(start_str)
    koniec = min(int(koniec_str), rozmiar_pliku - 1) if koniec_str else rozmiar_pliku - 1
    dlugosc_paczki = koniec - start + 1

    def generator_zakresu():
        with open(sciezka_pliku, "rb") as f:
            f.seek(start)
            yield f.read(dlugosc_paczki)

    naglowki = {
        "Content-Range": f"bytes {start}-{koniec}/{rozmiar_pliku}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(dlugosc_paczki),
    }

    return StreamingResponse(
        generator_zakresu(),
        status_code=206,
        headers=naglowki,
        media_type="video/mp4"
    )