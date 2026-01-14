def test_club_crud_via_admin_signup(client):
    admin_payload = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "strongpassword",
        "club_name": "Waffle Studio",
        "club_description": "Test club",
    }
    signup_response = client.post("/api/admin/signup", json=admin_payload)
    assert signup_response.status_code == 201
    admin_data = signup_response.json()
    club_id = admin_data["club_id"]

    create_response = client.post("/api/clubs", json={"name": "Direct Club"})
    assert create_response.status_code == 405

    list_response = client.get("/api/clubs")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert isinstance(list_data, list)
    assert any(club["id"] == club_id for club in list_data)

    get_response = client.get(f"/api/clubs/{club_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == admin_payload["club_name"]

    update_payload = {"name": "Updated Club"}
    update_response = client.put(f"/api/clubs/{club_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_payload["name"]

    delete_response = client.delete(f"/api/clubs/{club_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/clubs/{club_id}")
    assert missing_response.status_code == 404
