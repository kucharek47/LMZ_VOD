from pydantic import BaseModel, Field

class I_Log(BaseModel):
    login: str = Field(..., min_length=3, max_length=32)
class I_Reg(BaseModel):
    login: str = Field(..., min_length=3, max_length=32)
    avatar: str = Field(..., min_length=3, max_length=32)
class I_konta(BaseModel):
    id: int = Field(..., ge=1, le=10)
    path_avatar: str = Field(..., min_length=10, max_length=64)
    name: str = Field(..., min_length=3, max_length=32)
