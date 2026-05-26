from fastapi import Header, HTTPException


#SEC
async def sprawdz_token(token: str = Header(...)):
    if token != "bezpieczny_klucz":
        raise HTTPException(status_code=403, detail="Odmowa dostepu")
    return token
#TELEMETRII