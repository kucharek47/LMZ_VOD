import requests
from typing import List, Dict, Any, Optional, Union
import json
import os
import re
import zipfile
import asyncio
from datetime import datetime, timedelta
from rapidfuzz import fuzz
import redis.asyncio as redis
from sqlalchemy import select

from model_DB import tworca_sesji, Film, Serial, Gatunek


class tmdb:
    def __init__(self, api_key: str = None, access_token: str = None, language: str = "pl-PL",
                 base_url: str = "https://api.themoviedb.org/3"):
        self.api_key = api_key
        self.access_token = access_token
        self.language = language
        self.base_url = base_url
        self.use_api_key = bool(api_key and not access_token)

    def _get_headers(self) -> dict:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Python-TMDB-Client/1.0'
        }
        if not self.use_api_key and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _request(self, path: str, **params) -> dict:
        headers = self._get_headers()
        params.update({"language": self.language})
        if self.use_api_key and self.api_key:
            params.update({"api_key": self.api_key})

        try:
            resp = requests.get(f"{self.base_url}{path}", params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                raise Exception(f"Błąd autentykacji (401): {resp.text}")
            elif resp.status_code == 404:
                raise Exception(f"Nie znaleziono zasobu (404): {path}")
            else:
                raise Exception(f"Błąd HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Błąd połączenia z TMDB API: {str(e)}")

    def _get_trailer(self, media_type: str, item_id: int) -> Optional[str]:
        try:
            headers = self._get_headers()
            params = {"language": self.language}
            if self.use_api_key and self.api_key:
                params["api_key"] = self.api_key

            res = requests.get(f"{self.base_url}/{media_type}/{item_id}/videos", params=params, headers=headers,
                               timeout=10)
            res.raise_for_status()
            videos = res.json().get("results", [])

            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("official"):
                    return f"https://www.youtube.com/watch?v={v['key']}"

            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                    return f"https://www.youtube.com/watch?v={v['key']}"

            for v in videos:
                if v.get("site") == "YouTube":
                    return f"https://www.youtube.com/watch?v={v['key']}"

            return None
        except Exception as e:
            print(f"Błąd podczas pobierania trailera dla {media_type} {item_id}: {str(e)}")
            return None

    def wyszukaj(self, title: str, media_type: str = "movie", oczekiwany_czas: Optional[int] = None,
                 czas_prog_bledu: int = 10, min_glosow: Optional[int] = None, min_ocena: Optional[float] = None,
                 gatunki: Optional[Union[str, List[str]]] = None, rok: Optional[str] = None, sortuj: bool = True) -> \
    Optional[Dict[str, Any]]:
        try:
            data = self._request(f"/search/{media_type}", query=title)

            if sortuj:
                def key_fun(hit):
                    name = hit.get("title") or hit.get("name") or ""
                    return -fuzz.token_set_ratio(title.lower(), name.lower())

                data["results"] = sorted(data.get("results", []), key=key_fun)

            for hit in data.get("results", []):
                try:
                    details = self._request(f"/{media_type}/{hit['id']}")
                    rt = None
                    if media_type == "movie":
                        rt = details.get("runtime")
                    else:
                        episode_times = details.get("episode_run_time", [])
                        rt = episode_times[0] if episode_times else None

                    if oczekiwany_czas is not None and (rt is None or abs(rt - oczekiwany_czas) > czas_prog_bledu):
                        continue
                    if min_glosow is not None and details.get("vote_count", 0) < min_glosow:
                        continue
                    if min_ocena is not None and details.get("vote_average", 0.0) < min_ocena:
                        continue
                    if gatunki is not None:
                        avail = {g["name"] for g in details.get("genres", [])}
                        want = {gatunki} if isinstance(gatunki, str) else set(gatunki)
                        if not (avail & want):
                            continue
                    if rok is not None:
                        release_date = details.get("release_date") or details.get("first_air_date", "0000-00-00")
                        if release_date[:4] != rok:
                            continue

                    typ_wyjsciowy = "film" if media_type == "movie" else "serial"

                    return {
                        "typ": typ_wyjsciowy,
                        "tytul": details.get("title") or details.get("name"),
                        "opis": details.get("overview"),
                        "premiera": details.get("release_date") or details.get("first_air_date"),
                        "gatunki": [g["name"] for g in details.get("genres", [])],
                        "ocena": details.get("vote_average"),
                        "glosy": details.get("vote_count"),
                        "czas_trwania": rt,
                        "plakat": f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get(
                            "poster_path") else None,
                        "trailer": self._get_trailer(media_type, details["id"])
                    }
                except Exception as e:
                    print(f"Błąd podczas przetwarzania wyników dla '{title}': {str(e)}")
                    continue

            return None
        except Exception as e:
            print(f"Błąd podczas wyszukiwania '{title}': {str(e)}")
            return None

    def wyszukaj_wiele(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        output = []
        known = {'typ', 'tytul', 'czas', 'czas_prog_bledu', 'glosy', 'ocena', 'gatunek', "rok", "path"}

        for i, q in enumerate(queries):
            print(f"Przetwarzanie {i + 1}/{len(queries)}: {q.get('tytul', 'Brak tytułu')}")
            tytul = re.sub(r"\(\d{4}\)", "", q["tytul"]).strip()
            extra = {k: v for k, v in q.items() if k not in known}

            media_tmdb = "movie" if q.get('typ') == 'film' else "tv"

            film_data = self.wyszukaj(
                title=tytul,
                media_type=media_tmdb,
                oczekiwany_czas=q.get('czas'),
                czas_prog_bledu=q.get('czas_prog_bledu', 10),
                min_glosow=q.get('glosy'),
                min_ocena=q.get('ocena'),
                gatunki=q.get('gatunek'),
                rok=q.get('rok'),
            )

            if film_data:
                film_data["path"] = q["path"]
                film_data.update(extra)
                output.append(film_data)
            else:
                print(f"Nie znaleziono: {q.get('tytul', 'Brak tytułu')}")

        return output


def struktura(katalog_docelowy):
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("struktura", exist_ok=True)
    zip_name = f"struktura/struktura-{today}.zip"

    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(katalog_docelowy):
                rel_path = os.path.relpath(root, katalog_docelowy)
                if rel_path != ".":
                    zipf.write(root, rel_path + '/')

                for file in files:
                    file_path_in_zip = os.path.join(rel_path, file)
                    if rel_path == ".":
                        file_path_in_zip = file
                    zipf.writestr(file_path_in_zip, "")
        print(f"Utworzono archiwum: {zip_name}")
    except Exception as e:
        print(f"Błąd podczas tworzenia archiwum: {str(e)}")


async def zrestartuj_redis():
    try:
        klient = redis.Redis(host='localhost', port=6379, db=0)
        await klient.flushdb()
        await klient.aclose()
        print("Pomyślnie wyczyszczono pamięć podręczną Redis.")
    except Exception as e:
        print(f"Błąd podczas czyszczenia Redis: {str(e)}")


async def auto_aktualizacja(seriali_path, filmow_path, access_token=None, api_key=None,
                            potwierdzenie=True):
    async with tworca_sesji() as sesja:
        try:
            wynik_filmy = await sesja.execute(select(Film.sciezka_pliku))
            posiadane_filmy = set(wynik_filmy.scalars().all())

            wynik_seriale = await sesja.execute(select(Serial.tytul))
            posiadane_seriale = set(wynik_seriale.scalars().all())

            lista = []

            if os.path.exists(seriali_path):
                for name in os.listdir(seriali_path):
                    if os.path.isdir(os.path.join(seriali_path, name)):
                        lista.append({"tytul": name, "typ": "serial", "path": name})
            else:
                print(f"Ostrzeżenie: Katalog seriali '{seriali_path}' nie istnieje")

            if os.path.exists(filmow_path):
                for fn in os.listdir(filmow_path):
                    if not fn.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".m4v")):
                        continue

                    path_filmu = fn
                    name = os.path.splitext(fn)[0]

                    year_match = re.search(r'\((\d{4})\)', name)
                    if year_match:
                        clean_name = re.sub(r'\(\d{4}\)', '', name).strip()
                        lista.append({
                            "tytul": clean_name,
                            "typ": "film",
                            "path": path_filmu,
                            "rok": year_match.group(1)
                        })
                    else:
                        lista.append({
                            "tytul": name,
                            "typ": "film",
                            "path": path_filmu
                        })
            else:
                print(f"Ostrzeżenie: Katalog filmów '{filmow_path}' nie istnieje")

            brakujace = []
            for x in lista:
                if x["typ"] == "film" and x["path"] not in posiadane_filmy:
                    brakujace.append(x)
                elif x["typ"] == "serial" and x["tytul"] not in posiadane_seriale:
                    brakujace.append(x)

            print(f"Znaleziono {len(brakujace)} nowych pozycji do dodania.")

            if not brakujace:
                print("Baza jest aktualna - brak nowych pozycji do dodania.")
                return

            odpowiedz = "t"
            if potwierdzenie:
                odpowiedz = await asyncio.to_thread(input,
                                                    f"Pobrać dane dla {len(brakujace)} brakujących pozycji? [t/n]: ")
                odpowiedz = odpowiedz.lower().strip()
            if odpowiedz == "t":
                instancja_tmdb = tmdb(access_token=access_token, api_key=api_key)

                print("Pobieranie danych z TMDB...")
                wyniki = instancja_tmdb.wyszukaj_wiele(brakujace)
                print(f"Znaleziono dane dla {len(wyniki)} pozycji")

                dodane = 0
                for x in wyniki:
                    try:
                        data_prem = None
                        if x.get("premiera"):
                            try:
                                data_prem = datetime.strptime(x["premiera"], "%Y-%m-%d")
                            except ValueError:
                                pass

                        lista_gatunkow = []
                        for g_nazwa in x.get("gatunki", []):
                            zapytanie_g = select(Gatunek).where(Gatunek.nazwa == g_nazwa)
                            wynik_g = await sesja.execute(zapytanie_g)
                            gatunek_db = wynik_g.scalar_one_or_none()

                            if not gatunek_db:
                                gatunek_db = Gatunek(nazwa=g_nazwa)
                                sesja.add(gatunek_db)
                                await sesja.commit()
                                await sesja.refresh(gatunek_db)

                            lista_gatunkow.append(gatunek_db)

                        if x["typ"] == "serial":
                            nowy_wpis = Serial(
                                typ_media="serial",
                                tytul=x["tytul"],
                                opis=x["opis"],
                                data_premiery=data_prem,
                                plakat_url=x["plakat"],
                                trailer_url=x["trailer"],
                                ocena_srednia=x["ocena"],
                                ocena_glosy=x["glosy"],
                                czas_trwania=x["czas_trwania"],
                                gatunki=lista_gatunkow
                            )
                        else:
                            nowy_wpis = Film(
                                typ_media="film",
                                tytul=x["tytul"],
                                opis=x["opis"],
                                data_premiery=data_prem,
                                plakat_url=x["plakat"],
                                trailer_url=x["trailer"],
                                ocena_srednia=x["ocena"],
                                ocena_glosy=x["glosy"],
                                czas_trwania=x["czas_trwania"],
                                sciezka_pliku=x["path"],
                                gatunki=lista_gatunkow
                            )

                        sesja.add(nowy_wpis)
                        dodane += 1
                    except Exception as e:
                        print(f"Błąd podczas dodawania {x.get('tytul', 'Nieznany')}: {str(e)}")

                await sesja.commit()
                print(f"Dodano {dodane} pozycji do bazy danych")

                print("Tworzenie archiwum struktury...")
                katalog_glowny = os.path.dirname(seriali_path) if seriali_path else "/mnt/dysk_VOD/filmy i seriale"
                struktura(katalog_glowny)

                await zrestartuj_redis()

        except Exception as e:
            print(f"Błąd podczas aktualizacji bazy: {str(e)}")
            await sesja.rollback()


if __name__ == "__main__":
    ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")
    API_KEY = os.getenv("TMDB_API_KEY")

    asyncio.run(auto_aktualizacja(
        os.getenv("PATH_SERIALS"),
        os.getenv("PATH_FILMS"),
        access_token=ACCESS_TOKEN,
        api_key=API_KEY,
        potwierdzenie=True
    ))