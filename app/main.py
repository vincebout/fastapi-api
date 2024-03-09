""" Main file of the API """
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import users
from .database.database import postgreSQL_pool
from .internal.log_config import logger

@asynccontextmanager
async def lifespan(app):
    """ Startup and close methods """
    yield
    # Close connection at shutdown
    if postgreSQL_pool:
        logger.info("Closing connection to database")
        postgreSQL_pool.closeall()
        logger.info("Connection to database closed")

app = FastAPI(
    title="FastAPI API",
    description="""
## Overview

You can **create users**.

## Users

You will be able to:

* **Create users**.
* **Read a user**.
* **Activate a user**.

To read and activate a user you must be logged in.
    """,
    summary="This API is used to create and activate users",
    version="1.0.0",
    lifespan=lifespan)
app.include_router(users.router)


@app.get("/")
async def root():
    """ root route """
    return {"message": "ok"}
