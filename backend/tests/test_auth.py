import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "password123", "role": "client"},
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == "new@test.com"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "new@test.com", "password": "password123"},
    )
    assert login.status_code == 200
    data = login.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, client_user: dict):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": client_user["email"], "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@test.com", "password": "password123", "role": "developer"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@test.com", "password": "password123"},
    )
    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()
