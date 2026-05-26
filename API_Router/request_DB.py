def pobierz_uzytkownika(id: int):
    return {"id": id, "nazwa": "tester_vod"}

def autoryzuj_uzytkownika(dane_konta: dict):
    return True

def pobierz_wideo_info(id: int):
    return {"id": id, "sciezka": "/dyski/wideo/film.mp4"}