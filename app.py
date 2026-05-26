from fastapi import FastAPI
from API_Router import user, wideo

app = FastAPI(title="Serwer VOD")

app.include_router(user.router)
app.include_router(wideo.router)