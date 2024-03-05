""" Model for Users """
from pydantic import BaseModel

class CreateUsers(BaseModel):
    """ Class of Users to create """
    email: str
    password: str

class UserResponse(BaseModel):
    """ Class of User response"""
    id: int
    email: str
    created_at: str

class UsersResponse(BaseModel):
    """ Class of list of Users """
    data: list[UserResponse]
