""" Main file of the API """
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import users
from .database.database import init_tables, postgreSQL_pool
from .internal.log_config import logger

@asynccontextmanager
async def lifespan(app):
    """ Startup and close methods """
    # Init tables if not created
    logger.info("Connecting to database")
    conn = postgreSQL_pool.getconn()
    init_tables(conn)
    postgreSQL_pool.putconn(conn)
    logger.info("Connected to database")
    yield
    # Close connection at shutdown
    if postgreSQL_pool:
        logger.info("Closing connection to database")
        postgreSQL_pool.closeall()
        logger.info("Connection to database closed")

app = FastAPI(lifespan=lifespan)
app.include_router(users.router)


@app.get("/")
async def root():
    """ root route """
    return {"message": "ok"}
