""" Test user routes """
import json
from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_get_users():
    """ Test GET users/ """
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == {"message": "users"}

def test_post_create_user():
    """ Test POST users/ to create a user """
    data = {"email":"test@test.com", "password":"testuser"}
    response = client.post("/users", data=json.dumps(data))
    assert response.status_code == 201
    assert response.json() == {"message": "create"}

def test_post_activate_user():
    """ Test PUT users/ to activate a user"""
    response = client.put("/users/activate/1?code=0000")
    assert response.status_code == 200
    assert response.json() == {"message": "activate"}
