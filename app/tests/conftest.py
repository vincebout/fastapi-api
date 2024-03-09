""" Configuration file for pytest """
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


os.environ["TEST"] = "True"
os.environ["TESTING_DB"] = "fastapi_db_test"

def pytest_configure(config):
    """ Create test database before everything """
    try:
        con = psycopg2.connect(
            dbname=os.environ.get('POSTGRES_DB'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD'),
            port=os.environ.get('POSTGRES_PORT'),
            host=os.environ.get('POSTGRES_HOST'))
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("CREATE DATABASE fastapi_db_test OWNER fastapi_db")
        cur.close()
        con.close()
    except (psycopg2.DatabaseError) as error:
        print(error)

def pytest_unconfigure(config):
    """ Drop test database after tests """
    try:
        con = psycopg2.connect(
            dbname=os.environ.get('POSTGRES_DB'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD'),
            port=os.environ.get('POSTGRES_PORT'),
            host=os.environ.get('POSTGRES_HOST'))
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("DROP DATABASE fastapi_db_test WITH (FORCE)")
        cur.close()
        con.close()
    except (psycopg2.DatabaseError) as error:
        print(error)
