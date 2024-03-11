""" Test user routes """
from datetime import datetime
import json
from fastapi.testclient import TestClient
import psycopg2
from psycopg2.extras import RealDictCursor
import pytest
from ..database.database import postgreSQL_pool
from ..utils.helpers import hash_password

from ..main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """ Delete data before tests """
    try:
        conn = postgreSQL_pool.getconn()
        with conn.cursor() as curs:
            curs.execute("DELETE FROM public.users")
        conn.commit()
    except (psycopg2.DatabaseError) as error:
        print(error)
    finally:
        postgreSQL_pool.putconn(conn)


@pytest.fixture()
def insert_test_user():
    """ Insert test user before tests """
    hashed_password = hash_password('testpassword')
    now = datetime.now()
    try:
        conn = postgreSQL_pool.getconn()
        with conn.cursor() as curs:
            curs.execute("""
                INSERT INTO public.users (id, email, password, code, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
                """,
                ("100", "test@test.fr", hashed_password, "0000", now))
        conn.commit()
    except (psycopg2.DatabaseError) as error:
        print(error)
    finally:
        postgreSQL_pool.putconn(conn)

class TestGetUsers:
    """ Tests for User GET routes """
    @pytest.mark.usefixtures('insert_test_user')
    def test_get_user(self):
        """ Test GET user/ """
        response = client.get("/user/100", auth=("test@test.fr", "testpassword"))
        assert response.status_code == 200
        json_response = response.json()
        assert json_response['id'] == 100
        assert json_response['is_activated'] is False
        assert json_response['email'] == "test@test.fr"

    @pytest.mark.usefixtures('insert_test_user')
    def test_get_user_wrong_login(self):
        """ Test GET user with wrong login """
        response = client.get("/user/100", auth=("wrong@test.fr", "testpassword"))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "Incorrect email or password"

    @pytest.mark.usefixtures('insert_test_user')
    def test_get_user_without_login(self):
        """ Test GET user without login """
        response = client.get("/user/100")
        assert response.status_code == 401
        json_response = response.json()
        assert json_response['detail'] == "Not authenticated"

    @pytest.mark.usefixtures('insert_test_user')
    def test_get_other_user(self):
        """ Test GET other user """
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        json_response = response.json()
        response = client.get(f"/user/{json_response['id']}", auth=("test@test.fr", "testpassword"))
        assert response.status_code == 404
        json_response = response.json()
        assert json_response['detail'] == "User not found"

class TestPostUsers:
    """ Tests for User POST routes """
    def test_post_create_user(self):
        """ Test POST users/ to create a user """
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        json_response = response.json()
        assert json_response['email'] == "test@test.com"
        assert json_response['id'] is not None
        assert json_response['created_at'] is not None

    @pytest.mark.usefixtures('insert_test_user')
    def test_post_create_user_existing_email(self):
        """ Test POST users/ to create a user with existing email """
        data = {"email":"test@test.fr", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The email already exists"

    def test_post_create_user_wrong_email(self):
        """ Test POST users/ to create a user with incorrect email """
        data = {"email":"testtest.fr", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The email is incorrect"

    def test_post_create_user_empty_email(self):
        """ Test POST users/ to create a user with empty email """
        data = {"email":"", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The email is incorrect"

    def test_post_create_user_email_too_long(self):
        """ Test POST users/ to create a user with a too long email """
        data = {
            "email":"uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu@test.fr",
            "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The email is over 50 characters"

    def test_post_create_user_email_too_short(self):
        """ Test POST users/ to create a user with a too short email """
        data = {
            "email":"u@u.fr",
            "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The email is incorrect"

    def test_post_create_user_empty_password(self):
        """ Test POST users/ to create a user with empty password """
        data = {"email":"test@email.com", "password":""}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The password is empty"

    def test_post_create_user_password_too_short(self):
        """ Test POST users/ to create a user with a too short password """
        data = {
            "email":"test@email.com", 
            "password":"uu"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 400
        json_response = response.json()
        assert json_response['detail'] == "The password must be at least 8 characters. Consider having a shorter one"

class TestPatchUsers:
    """ Tests for User PATCH routes """
    def test_patch_activate_user(self):
        """ Test PATCH users/ to activate a user"""
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    SELECT id, code FROM public.users
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                user = curs.fetchone()
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.patch(f"/users/activate/{user['id']}?code={user['code']}",
                              auth=("test@test.com", "testuser"))
        assert response.status_code == 200
        assert response.json() == {"message": "User activated"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_user_wrong_code(self):
        """ Test activate a user with wrong code"""
        response = client.patch("/users/activate/100?code=9999",
                                auth=("test@test.fr", "testpassword"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The code provided is incorrect"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_already_activated_user(self):
        """ Test activate an already activated user"""
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    UPDATE public.users
                    SET is_activated = true
                    WHERE id = %s;
                    """,
                    ("100",))
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.patch("/users/activate/100?code=0000",
                              auth=("test@test.fr", "testpassword"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The user is already activated"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_user_expired_code(self):
        """ Test activate a user with expired code"""
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    UPDATE public.users
                    SET created_at = '2024-01-13 10:00:00.430322'
                    WHERE id = %s;
                    """,
                    ("100",))
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.patch("/users/activate/100?code=0000",
                              auth=("test@test.fr", "testpassword"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The code is no longer available"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_user_wrong_login(self):
        """ Test activate a user with wrong login """
        response = client.patch("/users/activate/100?code=0000",
                                auth=("wrong@test.com", "wrongpassword"))
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect email or password"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_user_wrong_id(self):
        """ Test activate a user with wrong login """
        response = client.patch("/users/activate/0?code=0000",
                                auth=("test@test.fr", "testpassword"))
        assert response.status_code == 404
        assert response.json() == {"detail": "The user was not found"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_user_not_authenticated(self):
        """ Test activate a user not authenticated """
        response = client.patch("/users/activate/100?code=0000")
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_patch_activate_other_user(self):
        """ Test activate an other user with authentification """
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        json_response = response.json()
        response = client.patch(f"/users/activate/{json_response['id']}?code=0000",
                                auth=("test@test.fr", "testpassword"))
        assert response.status_code == 404
        assert response.json() == {"detail": "The user was not found"}
