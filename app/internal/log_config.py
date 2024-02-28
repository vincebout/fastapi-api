""" Loging config file """
import logging
import uvicorn

FORMAT: str = "%(levelprefix)s %(asctime)s | %(message)s"

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = uvicorn.logging.DefaultFormatter(FORMAT)

ch.setFormatter(formatter)

logger.addHandler(ch)
