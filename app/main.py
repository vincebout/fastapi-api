""" Main file of the API """
from fastapi import FastAPI
from .routers import users

app = FastAPI()
app.include_router(users.router)


@app.get("/")
async def root():
    """ root route """
    return {"message": "ok"}
