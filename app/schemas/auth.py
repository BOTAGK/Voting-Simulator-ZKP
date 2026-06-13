from pydantic import BaseModel, Field

class AdminLog(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=255)

class AdminRead(BaseModel):
    username: str