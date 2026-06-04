# LMZ VOD Platform

Zaawansowana platforma Video on Demand (VOD) zbudowana w architekturze mikroserwisowej, nastawiona na wysoką wydajność, modularność i nowoczesny stack technologiczny. Projekt łączy backend asynchroniczny, osobny mikroserwis rekomendacyjny, frontend SPA oraz pełną konteneryzację środowiska.

## Najważniejsze cechy

- architektura mikroserwisowa
- backend oparty o FastAPI i Python
- frontend oparty o Angular
- osobny mikroserwis rekomendacji w Clojure
- asynchroniczny dostęp do danych
- PostgreSQL jako główna baza danych
- Redis jako warstwa cache
- migracje bazy przez Alembic
- pełne uruchamianie przez Docker i Docker Compose
- interaktywny instalator `setup.py`
- gotowe środowisko developerskie w DevContainer
- demo materiał wideo do natychmiastowych testów

## Stack technologiczny

### Backend
- Python
- FastAPI
- Uvicorn
- SQLAlchemy 2.0
- asyncpg
- Alembic

### Frontend
- Angular
- TypeScript

### Usługi i infrastruktura
- PostgreSQL
- Redis
- Docker
- Docker Compose

### Mikroserwis analityczny
- Clojure
- deps.edn
- Jetty
- clj-kondo
- LSP

### Bezpieczeństwo
- JWT
- bcrypt
- Argon2

## Architektura projektu

Projekt został podzielony na kilka niezależnych warstw:

### Główny backend
Backend odpowiada za:
- logikę biznesową
- autoryzację i obsługę użytkowników
- streamowanie materiałów wideo
- upload nowych plików
- zapis postępu oglądania
- telemetrię odtwarzacza
- komunikację z Redis i PostgreSQL
- serwowanie zbudowanego frontendu Angular

### Mikroserwis rekomendacji
Osobny mikroserwis napisany w Clojure analizuje historię oglądania i tagi, a następnie wylicza rekomendacje dla użytkownika. Komunikacja odbywa się przez API, niezależnie od głównego backendu.

### Frontend
Interfejs użytkownika został zbudowany jako SPA w Angularze. Projekt jest przygotowany pod prerendering / SSR / SSG, co wspiera lepszy czas pierwszego renderu i lepszą indeksację.

### Warstwa danych
- PostgreSQL przechowuje główne dane aplikacji
- Redis obsługuje cache i operacje wymagające szybkiego dostępu
- Alembic zarządza wersjonowaniem schematu bazy

## Struktura backendu

Backend jest podzielony modularnie, a logika została rozdzielona na osobne routery i moduły.

Najważniejsze elementy:
- `API_Router/wideo.py` — streaming wideo i pobieranie metadanych
- `API_Router/user.py` — rejestracja, logowanie i profile
- `API_Router/progres.py` — zapisywanie postępu oglądania
- `API_Router/upload.py` — upload materiałów
- `API_Router/check.py` — healthchecki i testy dostępności
- `API_Router/admin.py` — moduł administracyjny w rozwoju
- `API_Router/redis_DB.py` — operacje na Redis
- `API_Router/request_DB.py` — zapytania do głównej bazy danych

## Najciekawsze rozwiązania techniczne

### Asynchroniczny backend
Projekt wykorzystuje asynchroniczny model pracy, co pozwala na lepszą obsługę wielu równoległych zapytań i mniejsze blokowanie aplikacji.

### Polimorficzne modele danych
Model `Media` dziedziczy po bardziej szczegółowych encjach, takich jak `Film` i `Serial`, co pozwala trzymać różne typy treści w jednym, spójnym modelu relacyjnym.

### Rozbudowane relacje ORM
W projekcie zastosowano relacje z kaskadowym usuwaniem, dzięki czemu powiązane dane, takie jak napisy, role wideo, historia oglądania i telemetryczne zdarzenia, są spójnie zarządzane.

### Telemetria
System rejestruje zdarzenia odtwarzacza, takie jak:
- `PLAY`
- `PAUSE`
- `SEEK`
- `HOVER_HERO`

### Integracja z Redis
Redis wspiera szybkie operacje na danych tymczasowych oraz cache, co pomaga odciążyć główną bazę danych.

### Automatyzacja konfiguracji
Skrypt `setup.py` prowadzi przez konfigurację projektu, zbiera dane do połączenia z PostgreSQL, generuje plik `.env`, zabezpiecza dane administratora i uruchamia migracje Alembic.

### Healthchecki w Dockerze
Kontenery są uruchamiane z kontrolą gotowości usług. Backend czeka na Redis, zanim wystartuje aplikacja główna.

## Środowisko developerskie

Projekt ma przygotowane środowisko developerskie w `.devcontainer/`, co umożliwia uruchomienie go w VS Code Remote Containers bez ręcznej instalacji większości zależności lokalnie.

W środowisku znajdują się:
- `devcontainer.json`
- dedykowany `Dockerfile`
- `docker-compose.yml`

## Wymagania

Do uruchomienia projektu potrzebne są:

- Python
- Docker
- Docker Compose
- działająca baza PostgreSQL

## Szybki start

### 1. Konfiguracja projektu
Uruchom skrypt instalacyjny:

```bash
python setup.py
```

Skrypt:
- poprosi o dane połączenia z PostgreSQL
- wygeneruje plik `.env`
- przygotuje konfigurację projektu
- wykona migracje bazy danych przez Alembic

### 2. Uruchomienie kontenerów
Po zakończeniu konfiguracji uruchom środowisko:

```bash
docker-compose up --build
```

### 3. Dostęp do aplikacji
Domyślnie aplikacja działa na porcie:

```text
13008
```

Przykładowy adres:
- `http://localhost:13008`

## Migracje bazy danych

Projekt korzysta z Alembic do wersjonowania schematu bazy danych. Dodatkowo istnieje skrypt wspierający automatyczne aktualizacje migracji.

W projekcie pojawiają się także migracje rozwijające funkcje takie jak:
- obsługa JWT
- wsparcie trailerów wideo

## Dane demonstracyjne

W projekcie znajduje się materiał demo, który pozwala szybko przetestować odtwarzanie i streaming bez konieczności wcześniejszego przygotowywania własnych plików.

## Co wyróżnia projekt

- przemyślana modularna struktura backendu
- asynchroniczny stack w Pythonie
- osobny mikroserwis w Clojure
- pełna konteneryzacja
- nacisk na automatyzację konfiguracji
- przygotowanie pod rozwój i dalsze rozszerzanie funkcji
- gotowość pod użycie w portfolio rekrutacyjnym

## Plan dalszego rozwoju

- rozwój panelu administracyjnego
- dalsze rozszerzanie telemetrii
- rozbudowa systemu rekomendacji
- kolejne typy materiałów i metadanych
- dodatkowe optymalizacje frontendu i renderowania

---