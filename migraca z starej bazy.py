import sqlite3
import json
import asyncio
from datetime import datetime
from sqlalchemy import select
from model_DB import tworca_sesji, Film, Serial, Odcinek, Gatunek

async def migracja_bazy():
    polaczenie_sqlite = sqlite3.connect('baza.db')
    kursor_sqlite = polaczenie_sqlite.cursor()
    kursor_sqlite.execute(
        "SELECT typ, tytul, opis, premiera, gatunki, ocena, glosy, czas_trwania, plakat, trailer FROM filmy_i_seriale")
    stare_dane = kursor_sqlite.fetchall()
    polaczenie_sqlite.close()

    przetworzone_media = set()

    async with tworca_sesji() as sesja:
        wynik_gatunki = await sesja.execute(select(Gatunek))
        slownik_gatunkow = {g.nazwa: g for g in wynik_gatunki.scalars().all()}

        for wiersz in stare_dane:
            typ_media, tytul, opis, premiera, gatunki_json, ocena, glosy, czas_trwania, plakat, trailer = wiersz

            rok = None
            if premiera and len(premiera) >= 4:
                rok = premiera[:4]

            klucz_unikalnosci = (typ_media, tytul, rok)
            if klucz_unikalnosci in przetworzone_media:
                continue

            przetworzone_media.add(klucz_unikalnosci)

            data_premiery_dt = None
            if premiera:
                try:
                    data_premiery_dt = datetime.strptime(premiera, "%Y-%m-%d")
                except ValueError:
                    pass

            przypisane_gatunki = []
            if gatunki_json:
                lista_gatunkow = json.loads(gatunki_json)
                for nazwa_gatunku in lista_gatunkow:
                    if nazwa_gatunku not in slownik_gatunkow:
                        nowy_gatunek = Gatunek(nazwa=nazwa_gatunku)
                        sesja.add(nowy_gatunek)
                        slownik_gatunkow[nazwa_gatunku] = nowy_gatunek
                    przypisane_gatunki.append(slownik_gatunkow[nazwa_gatunku])

            if typ_media == 'movie':
                nowy_film = Film(
                    typ_media="film",
                    tytul=tytul,
                    opis=opis,
                    data_premiery=data_premiery_dt,
                    ocena_srednia=ocena,
                    ocena_glosy=glosy,
                    czas_trwania=czas_trwania,
                    plakat_url=plakat,
                    trailer_url=trailer,
                    sciezka_pliku="demo/f/demo.mp4"
                )
                nowy_film.gatunki = przypisane_gatunki
                sesja.add(nowy_film)

            elif typ_media == 'tv':
                nowy_serial = Serial(
                    typ_media="serial",
                    tytul=tytul,
                    opis=opis,
                    data_premiery=data_premiery_dt,
                    ocena_srednia=ocena,
                    ocena_glosy=glosy,
                    czas_trwania=czas_trwania,
                    plakat_url=plakat,
                    trailer_url=trailer
                )
                nowy_serial.gatunki = przypisane_gatunki
                sesja.add(nowy_serial)

                await sesja.flush()

                nowy_odcinek = Odcinek(
                    serial_id=nowy_serial.id,
                    numer_sezonu=1,
                    numer_odcinka=1,
                    tytul="Odcinek Pokazowy",
                    sciezka_pliku="demo/s/demo/demo s01e01.mp4"
                )
                sesja.add(nowy_odcinek)

        await sesja.commit()

if __name__ == "__main__":
    asyncio.run(migracja_bazy())