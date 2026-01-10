def test_club_crud(client):
    create_payload = {"name": "Waffle Studio"}
    create_response = client.post("/api/clubs", json=create_payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == create_payload["name"]
    assert "id" in created

    list_response = client.get("/api/clubs")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert isinstance(list_data, list)
    assert any(club["id"] == created["id"] for club in list_data)

    get_response = client.get(f"/api/clubs/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == create_payload["name"]

    update_payload = {"name": "Updated Club"}
    update_response = client.put(f"/api/clubs/{created['id']}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_payload["name"]

    delete_response = client.delete(f"/api/clubs/{created['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/clubs/{created['id']}")
    assert missing_response.status_code == 404
