""" Routes for Users model """
from fastapi import APIRouter
from ..models.users import Users

router = APIRouter()


@router.get("/users", tags=["users"], status_code=200)
async def get_users():
    """ Get all users """
    return {"message": "users"}

@router.post("/users", tags=["users"], status_code=201)
async def create_user(user: Users):
    """ Create a user """
    print(user.email)
    print(user.password)
    return {"message": "create"}

@router.put("/users/activate/{user_id}", tags=["users"], status_code=200)
async def activate_user(user_id: str, code: int):
    """ Activate a user """
    print(user_id)
    print(code)
    return {"message": "activate"}
