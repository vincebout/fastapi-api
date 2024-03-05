""" App settings """

class Settings:
    """ app settings """
    POSTGRES_USER: str = 'fastapi_db'
    POSTGRES_PASSWORD: str = 'fastapi_db'
    POSTGRES_DB: str = 'fastapi_db'
    POSTGRES_PORT: int = 5432
    POSTGRES_MAX_CONNECTIONS: int = 20
    POSTGRES_MIN_CONNECTIONS: int = 1

    CODE_VALIDITY_PERIOD_SECS: int = 60
