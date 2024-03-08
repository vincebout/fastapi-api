""" Database related functions """
import psycopg2
from psycopg2 import pool
from ..config.config import Settings
from ..internal.log_config import logger

try:
    logger.info("Connecting to database")
    postgreSQL_pool = pool.SimpleConnectionPool(
        Settings.POSTGRES_MIN_CONNECTIONS,
        Settings.POSTGRES_MAX_CONNECTIONS,
        database = Settings.POSTGRES_DB,
        user = Settings.POSTGRES_USER,
        host = Settings.POSTGRES_HOST,
        password = Settings.POSTGRES_PASSWORD,
        port = Settings.POSTGRES_PORT
    )
except (psycopg2.DatabaseError) as connect_error:
    logger.error(connect_error)
finally:
    logger.info("Connected to database")

def init_tables(conn):
    """ Init tables if they do not exist """
    try:
        with conn.cursor() as curs:
            logger.info("Initializing tables")
            curs.execute("""
                CREATE TABLE IF NOT EXISTS public.users
                (id serial PRIMARY KEY, email varchar(50) NOT NULL, password varchar(100) NOT NULL,
                code varchar(4) NOT NULL, is_activated boolean DEFAULT false NOT NULL, created_at timestamp DEFAULT now() NOT NULL,
                UNIQUE(email),
                CONSTRAINT correct_email CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'),
                CONSTRAINT email_min_size_check CHECK (char_length(email) > 6),
                CONSTRAINT code_size_check CHECK (char_length(code) = 4))
            """)
            curs.execute("CREATE INDEX IF NOT EXISTS id_idx ON public.users (id)")
            curs.execute("CREATE INDEX IF NOT EXISTS email_idx ON public.users (email)")
        conn.commit()
    except (psycopg2.DatabaseError) as error:
        logger.error(error)
