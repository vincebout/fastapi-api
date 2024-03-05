""" Test user routes """
import json
from fastapi.testclient import TestClient
import psycopg2
from psycopg2.extras import RealDictCursor
import pytest
from ..database.database import postgreSQL_pool

from ..main import app

client = TestClient(app)

class TestUsers:
    """ Tests for User routes """

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(self):
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
    def insert_test_user(self):
        """ Insert test user before tests """
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor() as curs:
                curs.execute("""
                    INSERT INTO public.users (id, email, password, code, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *;
                    """,
                    ("1", "test@test.fr", "test-password", "0000", "2024-01-13 10:00:00.430322"))
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

    @pytest.mark.usefixtures('insert_test_user')
    def test_get_users(self):
        """ Test GET users/ """
        response = client.get("/users")
        assert response.status_code == 200
        expected = {'data': [{
            'created_at': "2024-01-13T10:00:00.430322",
            'email': 'test@test.fr',
            'id': 1
            }
        ]}
        assert response.json() == expected

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

    def test_put_activate_user(self):
        """ Test PUT users/ to activate a user"""
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    SELECT code FROM public.users
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                user = curs.fetchone()
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.put(f"/users/activate?code={user['code']}",
                              auth=("test@test.com", "testuser"))
        assert response.status_code == 200
        assert response.json() == {"message": "User activated"}

    def test_put_activate_user_wrong_code(self):
        """ Test activate a user with wrong code"""
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        response = client.put("/users/activate?code=0000", auth=("test@test.com", "testuser"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The code provided is incorrect"}

    def test_put_activate_already_activated_user(self):
        """ Test activate an already activated user"""
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    UPDATE public.users
                    SET is_activated = true
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                curs.execute("""
                    SELECT code FROM public.users
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                user = curs.fetchone()
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.put(f"/users/activate?code={user['code']}",
                              auth=("test@test.com", "testuser"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The user is already activated"}

    def test_put_activate_user_expired_code(self):
        """ Test activate a user with expired code"""
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        assert response.status_code == 201
        try:
            conn = postgreSQL_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as curs:
                curs.execute("""
                    UPDATE public.users
                    SET created_at = '2024-01-13 10:00:00.430322'
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                curs.execute("""
                    SELECT code FROM public.users
                    WHERE email = %s;
                    """,
                    ("test@test.com",))
                user = curs.fetchone()
            conn.commit()
        except (psycopg2.DatabaseError) as error:
            print(error)
        finally:
            postgreSQL_pool.putconn(conn)

        response = client.put(f"/users/activate?code={user['code']}",
                              auth=("test@test.com", "testuser"))
        assert response.status_code == 400
        assert response.json() == {"detail": "The code is no longer available"}

    @pytest.mark.usefixtures('insert_test_user')
    def test_put_activate_user_wrong_login(self):
        """ Test activate a user with wrong login """
        data = {"email":"test@test.com", "password":"testuser"}
        response = client.post("/users", data=json.dumps(data))
        response = client.put("/users/activate?code=0000", auth=("wrong@test.com", "wrongpassword"))
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect email or password"}
