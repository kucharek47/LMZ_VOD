from pydantic import BaseModel, Field

class I_Log_A(BaseModel):
    login: str = Field(..., min_length=3, max_length=32)
    haslo: str = Field(..., min_length=12, max_length=128)
class I_Log(BaseModel):
    login: str = Field(..., min_length=3, max_length=32)
