""" Routes for User model """
from random import randint
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.encoders import jsonable_encoder
from ..models.users import CreateUsers, UserResponse, UsersResponse
from ..database.database import postgreSQL_pool
from ..internal.log_config import logger
from ..config.config import Settings

router = APIRouter()

security = HTTPBasic()

def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """ Check crendtials """
    username = credentials.username
    password = credentials.password

    try:
        conn = postgreSQL_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute("SELECT email, password FROM public.users WHERE email = %s",
                            (username,))
            result = curs.fetchone()
    except (psycopg2.DatabaseError) as error:
        logger.error(error)
        raise HTTPException(status_code=500, detail="An error has occured") from error
    finally:
        postgreSQL_pool.putconn(conn)
    json_result = jsonable_encoder(result)
    if json_result is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    password_check = bcrypt.checkpw(password.encode('utf-8'),
                            json_result['password'].encode('utf-8'))
    if password_check is not True:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    return username

@router.get("/users", tags=["users"], status_code=200, response_model=UsersResponse)
async def get_users():
    """ Get all users """
    try:
        conn = postgreSQL_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            # Fetch from db
            curs.execute('SELECT id, email, created_at FROM public.users')
            results = curs.fetchall()
    except (psycopg2.DatabaseError) as error:
        logger.error(error)
        raise HTTPException(status_code=500, detail="An error has occured") from error
    finally:
        postgreSQL_pool.putconn(conn)

    return UsersResponse(data=jsonable_encoder(results))

@router.post("/users", tags=["users"], status_code=201, response_model=UserResponse)
async def create_user(user: CreateUsers):
    """ Create a user """
    # Check if password is empty
    if user.password in [None, '']:
        raise HTTPException(status_code=400, detail="The password is empty")
    # Check if password is too short (< 8 chars)
    if len(user.password) < 8:
        raise HTTPException(status_code=400,
                detail="The password must be at least 8 characters. Consider having a shorter one")
    try:
        conn = postgreSQL_pool.getconn()
        # Generate a random 4 digits code
        code = str(randint(1, 9999)).zfill(4)
        # Hash password
        password_bytes = user.password.encode('utf-8')
        salt = bcrypt.gensalt(12)
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            # Insert in db
            curs.execute("""
                INSERT INTO public.users (email, password, code)
                VALUES (%s, %s, %s)
                RETURNING *;
                """,
                (user.email, hashed_password, code))
            new_user = curs.fetchone()
        conn.commit()
    except (psycopg2.DatabaseError) as error:
        logger.error(error)
        if "duplicate" in error.pgerror:
            raise HTTPException(status_code=400, detail="The email already exists") from error
        if "correct_email" in error.pgerror or "email_min_size_check" in error.pgerror:
            raise HTTPException(status_code=400, detail="The email is incorrect") from error
        if "value too long" in error.pgerror:
            raise HTTPException(status_code=400,
                                detail="The email is over 50 characters") from error

        raise HTTPException(status_code=500, detail="An error has occured") from error
    finally:
        postgreSQL_pool.putconn(conn)

    # Send the email
    # send_email()
    logger.info("An email with the activation code '%s' has been sent to %s",
                new_user['code'], new_user['email'])
    return jsonable_encoder(new_user)

@router.put("/users/activate", tags=["users"], status_code=200)
async def activate_user(code: str, username: str = Depends(check_credentials)):
    """ Activate a user """
    try:
        conn = postgreSQL_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute("""
                         SELECT is_activated, extract(epoch from (now() - created_at)) as delay
                         FROM public.users
                         WHERE email = %s AND code = %s
                         """,
                         (username, code))
            result = curs.fetchone()
        if result is None:
            raise HTTPException(status_code=400, detail="The code provided is incorrect")
        if result['is_activated']:
            raise HTTPException(status_code=400, detail="The user is already activated")
        if result['delay'] >= Settings.CODE_VALIDITY_PERIOD_SECS:
            raise HTTPException(status_code=400, detail="The code is no longer available")
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            # Set the user as activated
            curs.execute("UPDATE public.users SET is_activated = true WHERE email = %s",
                         (username,))
            conn.commit()
    except (psycopg2.DatabaseError) as error:
        logger.error(error)
        raise HTTPException(status_code=500, detail="An error has occured") from error
    finally:
        postgreSQL_pool.putconn(conn)

    return {"message": "User activated"}
