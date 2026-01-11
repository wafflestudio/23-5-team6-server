from fastapi.testclient import TestClient
from pydantic_settings import SettingsConfigDict
import pytest
from datetime import datetime, timedelta
from asset_management.app.auth.settings import AuthSettings
from tests.conftest import SETTINGS
from authlib.jose import jwt, JWTClaims

class TestAuthSettings(AuthSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=SETTINGS.env_file,
        extra='ignore'
    )

AUTH_SETTINGS = TestAuthSettings()

@pytest.fixture(scope="function")
def user_data(client, db_session):
  """Create a test user and return an authentication token"""
  test_user_data = {
    "name": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword",
  }

  response = client.post("/api/users/signup", json=test_user_data)
  assert response.status_code == 201
  data = response.json()
  assert data["name"] == test_user_data['name']
  assert data["email"] == test_user_data['email']
  data['password'] = test_user_data['password']
  return data

@pytest.fixture(scope="function")
def auth_token(client, user_data):
  response = client.post(
    "/api/auth/login",
    json={"email": user_data["email"], "password": user_data["password"]})
  return response.json()['tokens']

def test_get_token(client: TestClient, user_data):
  response = client.post(
    "/api/auth/login",
    json={"email": user_data["email"], "password": user_data["password"]})
  assert response.status_code == 200
  response = response.json()
  assert 'tokens' in response
  assert 'user_name' in response
  assert 'user_type' in response
  assert response['user_name'] == user_data['name']
  # assert response['user_type'] == 0  ## 로그인 시스템 수정 후 변경 필요
  tokens = response['tokens']
  assert "access_token" in tokens
  assert "refresh_token" in tokens
  access_token = jwt.decode(tokens["access_token"], AUTH_SETTINGS.ACCESS_TOKEN_SECRET)
  refresh_token = jwt.decode(tokens["refresh_token"], AUTH_SETTINGS.REFRESH_TOKEN_SECRET)
  assert "sub" in access_token
  assert "sub" in refresh_token
  assert access_token["sub"] == user_data["id"]
  assert access_token["type"] == "access"
  assert access_token["exp"] > datetime.now().timestamp()
  assert refresh_token["sub"] == user_data["id"]
  assert refresh_token["type"] == "refresh"
  assert refresh_token["exp"] > datetime.now().timestamp()

def test_expired_token(client: TestClient, user_data):
  header = {"alg": "HS256"}
  payload_acc = {
    "sub": user_data["id"],
    "type": "refresh",
    "exp": datetime.now() - timedelta(minutes=1),
  }
  access_token = jwt.encode(header, payload_acc, AUTH_SETTINGS.ACCESS_TOKEN_SECRET)

  response = client.get(
    "/api/auth/refresh",
    headers={"Authorization": f"Bearer {access_token}"}
  )
  assert response.status_code == 401

def test_refresh_token(client: TestClient, user_data, auth_token):
  response = client.get(
    "/api/auth/refresh",
    headers={"Authorization": f"Bearer {auth_token['refresh_token']}"}
  )
  assert response.status_code == 200
  tokens = response.json()
  
  assert "access_token" in tokens
  assert "refresh_token" in tokens
  access_token = jwt.decode(tokens["access_token"], AUTH_SETTINGS.ACCESS_TOKEN_SECRET)
  refresh_token = jwt.decode(tokens["refresh_token"], AUTH_SETTINGS.REFRESH_TOKEN_SECRET)
  assert "sub" in access_token
  assert "sub" in refresh_token
  assert access_token["sub"] == user_data["id"]
  assert access_token["type"] == "access"
  assert access_token["exp"] > datetime.now().timestamp()
  assert refresh_token["sub"] == user_data["id"]
  assert refresh_token["type"] == "refresh"
  assert refresh_token["exp"] > datetime.now().timestamp()

def test_logout(client: TestClient, auth_token):
  access_token = auth_token["refresh_token"]

  response = client.delete(
    "/api/auth/logout",
    headers={"Authorization": f"Bearer {access_token}"})
  assert response.status_code == 204
  
  response = client.get(
    "/api/auth/refresh",
    headers={"Authorization": f"Bearer {access_token}"})
  assert response.status_code == 401