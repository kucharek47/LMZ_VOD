import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from API_Router import user, wideo

path_film = os.getenv("PATH_FILMS", "demo/f")
path_serials = os.getenv("PATH_SERIALS", "demo/s")
app = FastAPI(title="Serwer VOD")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/img", StaticFiles(directory="img"), name="img")
app.include_router(user.router)
app.include_router(wideo.router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)