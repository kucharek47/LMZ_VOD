from typing import List, Optional
from datetime import date
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class I_Log(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    haslo: Optional[str] = None

class I_Reg(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    path_avatar: Optional[str] = Field(default="default.png", max_length=255)

class I_Konta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., ge=1)
    path_avatar: str = Field(..., max_length=255)
    nazwa: str = Field(..., min_length=3, max_length=50)

class I_Film(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    release_date: Optional[date] = None
    poster_path: Optional[str] = None
    trailer_url: Optional[str] = None
    file_path: Optional[str] = None
    ocena: Optional[float] = None
    liczba_glosow: Optional[int] = None
    czas_trwania: Optional[int] = None
    genres: List[str]

class I_Serial(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    release_date: Optional[date] = None
    poster_path: Optional[str] = None
    trailer_url: Optional[str] = None
    ocena: Optional[float] = None
    liczba_glosow: Optional[int] = None
    czas_trwania: Optional[int] = None
    genres: List[str]
    seasons_count: int

class I_Szukane_Media(BaseModel):
    id: int
    media_type: str
    title: str
    description: Optional[str] = None
    poster_path: Optional[str] = None
    file_path: Optional[str] = None
    genres: List[str]

class I_Refresh(BaseModel):
    refresh_token: str

class I_JWT(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    id: str

class I_Ostatnio_Ogladane(BaseModel):
    media_id: int
    tytul: str
    plakat_url: Optional[str] = None
    typ_media: str
    obejrzany_czas: float
    data_aktualizacji: datetime
    numer_sezonu: Optional[int] = None
    numer_odcinka: Optional[int] = None
    odcinek_id: Optional[int] = None
class I_Postep(BaseModel):
    media_id: int
    odcinek_id: Optional[int] = None
    aktualny_czas: float
    calkowity_czas: float

class I_Zmiana_Statusu(BaseModel):
    media_id: int
    numer_sezonu: Optional[int] = None
    numer_odcinka: Optional[int] = None
    czy_obejrzane: bool

class I_Nastepny_Wideo(BaseModel):
    id: int
    sciezka_pliku: str
    odcinek_id: Optional[int] = None
    numer_sezonu: Optional[int] = None
    numer_odcinka: Optional[int] = None
    zapisany_czas: float

class I_WideoCzas(BaseModel):
    obejrzany_czas: float