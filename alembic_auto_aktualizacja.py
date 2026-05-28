import subprocess
import sys
import os
from datetime import datetime

def uruchom_automatyczna_migracje():
    znacznik_czasu = datetime.now().strftime("%Y%m%d_%H%M%S")
    domyslna_wiadomosc = f"auto_aktualizacja_{znacznik_czasu}"

    print(f"Podaj opis zmian (wcisnij Enter, aby uzyc: {domyslna_wiadomosc}):")
    wpis_uzytkownika = input().strip()

    wiadomosc = wpis_uzytkownika if wpis_uzytkownika else domyslna_wiadomosc

    obecny_katalog = os.path.abspath(os.path.dirname(__file__))

    zmienne_srodowiskowe = os.environ.copy()
    if "PYTHONPATH" in zmienne_srodowiskowe:
        zmienne_srodowiskowe["PYTHONPATH"] = f"{obecny_katalog}{os.pathsep}{zmienne_srodowiskowe['PYTHONPATH']}"
    else:
        zmienne_srodowiskowe["PYTHONPATH"] = obecny_katalog

    try:
        subprocess.run(["alembic", "upgrade", "head"], env=zmienne_srodowiskowe, check=True)
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", wiadomosc], env=zmienne_srodowiskowe, check=True)
        subprocess.run(["alembic", "upgrade", "head"], env=zmienne_srodowiskowe, check=True)
        print("Baza danych zostala pomyslnie zaktualizowana.")
    except subprocess.CalledProcessError as blad:
        print(f"Wystapil blad podczas migracji: {blad}", file=sys.stderr)

if __name__ == "__main__":
    uruchom_automatyczna_migracje()