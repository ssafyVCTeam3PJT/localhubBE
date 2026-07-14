from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_posts_endpoint_returns_data():
    response = client.get("/api/posts")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "posts" in body["data"]
    assert isinstance(body["data"]["posts"], list)


def test_post_update_delete_join_and_recommend_flow():
    create_response = client.post(
        "/api/posts",
        json={
            "title": "테스트 모임",
            "description": "테스트 설명",
            "location": "테스트 장소",
            "address": "테스트 주소",
            "sport": "러닝",
            "maxCount": 5,
            "lat": 1.1,
            "lng": 2.2,
            "tags": ["테스트"],
        },
    )
    assert create_response.status_code == 201
    post_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/posts/{post_id}",
        json={"title": "수정된 제목", "status": "모집마감"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "수정된 제목"

    join_response = client.post(f"/api/posts/{post_id}/join")
    assert join_response.status_code == 200
    assert join_response.json()["data"]["joined"] is True

    recommend_response = client.post(f"/api/posts/{post_id}/recommend")
    assert recommend_response.status_code == 200
    assert recommend_response.json()["data"]["recommended"] is True

    delete_response = client.delete(f"/api/posts/{post_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True


def test_places_detail_endpoint():
    response = client.get("/api/places/place_1/posts")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "posts" in body["data"]


def test_places_endpoint_returns_category_and_emoji():
    response = client.get("/api/places")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    place = next((item for item in body["data"]["places"] if item["id"] == "place_1"), None)
    assert place is not None
    assert place["category"] == "산책/러닝"
    assert place["emoji"] == "🏃"
