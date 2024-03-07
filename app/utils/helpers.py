""" Contains helper functions """
import bcrypt


def hash_password(password: str):
    """ Hash a provided password """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(12)
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode()
    return hashed_password
