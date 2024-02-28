""" Model for Users """
from pydantic import BaseModel

class Users(BaseModel):
    """ Class of Users """
    email: str
    password: str
