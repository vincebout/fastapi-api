""" App settings """

import os


class Settings:
    """ app settings """
    POSTGRES_USER: str = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD: str = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_DB: str = os.environ.get('POSTGRES_DB')
    POSTGRES_PORT: int = os.environ.get('POSTGRES_PORT')
    POSTGRES_HOST: str = os.environ.get('POSTGRES_HOST')
    POSTGRES_MAX_CONNECTIONS: int = os.environ.get('POSTGRES_MAX_CONNECTIONS')
    POSTGRES_MIN_CONNECTIONS: int = os.environ.get('POSTGRES_MIN_CONNECTIONS')

    CODE_VALIDITY_PERIOD_SECS: int = 60
