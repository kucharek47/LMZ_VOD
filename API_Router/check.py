from fastapi import Header, HTTPException, Depends


#SEC
async def sprawdz_token(token: str = Header(...)):
    if token != "bezpieczny_klucz":
        raise HTTPException(status_code=403, detail="Odmowa dostepu")
    return token
async def sprawdz_token_main(token: str = Depends(sprawdz_token)):
    if token != "bezpieczny_klucz":
        raise HTTPException(status_code=403, detail="Odmowa dostepu")
    return token
#TELEMETRII