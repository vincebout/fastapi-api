""" Model for Users """
from pydantic import BaseModel

class CreateUsers(BaseModel):
    """ Class of Users to create """
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "myemail@exemple.com",
                    "password": "Ul8*K4Hni8",
                }
            ]
        }
    }

class UserResponse(BaseModel):
    """ Class of User response"""
    id: int
    email: str
    created_at: str
    is_activated: bool
