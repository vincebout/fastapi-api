from pydantic import BaseModel

class Users(BaseModel):
    email: str
    password: str