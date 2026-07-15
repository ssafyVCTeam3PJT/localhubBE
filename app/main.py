import json
import sqlite3
from pathlib import Path
from typing import Any

import bcrypt
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "localhub.db"
DATA_JSON_PATH = ROOT / "서울_레포츠.json"

def classify_place_category(name: str, address: str = "") -> tuple[str, str]:
    text = f"{name} {address}".lower()

    if any(keyword in text for keyword in ["수영", "풋살", "배구", "농구", "배드민턴", "체육관", "체육센터", "운동장", "스포츠센터"]):
        return "스포츠/체육", "🏀"
    if any(keyword in text for keyword in ["공원", "산책", "둘레길", "숲길", "길", "하천", "한강", "강", "호수", "정원"]):
        return "산책/러닝", "🏃"
    if any(keyword in text for keyword in ["수영장", "워터", "풀", "물놀이"]):
        return "수영", "🏊"
    if any(keyword in text for keyword in ["자전거", "자전거길", "bike"]):
        return "자전거", "🚲"
    if any(keyword in text for keyword in ["캠핑", "야영", "카라반"]):
        return "캠핑", "🏕️"
    if any(keyword in text for keyword in ["테니스", "골프", "클라이밍", "볼링", "헬스", "피트니스"]):
        return "실내운동", "💪"
    return "기타", "📍"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return True
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def load_public_data_places() -> None:
    if not DATA_JSON_PATH.exists():
        return

    with DATA_JSON_PATH.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    items = payload.get("items", [])
    if not items:
        return

    conn = get_connection()
    for item in items:
        place_id = f"place_{item.get('contentid', '') or len(items)}"
        existing = conn.execute("SELECT id FROM places WHERE id = ?", (place_id,)).fetchone()
        if existing:
            continue

        category, emoji = classify_place_category(item.get("title", ""), item.get("addr1", ""))
        conn.execute(
            """
            INSERT INTO places (id, name, address, lat, lng, category, emoji, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                place_id,
                item.get("title", ""),
                item.get("addr1", ""),
                float(item["mapy"]) if item.get("mapy") else None,
                float(item["mapx"]) if item.get("mapx") else None,
                category,
                emoji,
                item.get("modifiedtime", "2026-07-14T00:00:00Z"),
            ),
        )
    conn.commit()
    conn.close()


def seed_initial_data() -> None:
    conn = get_connection()
    rows = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    if rows == 0:
        sample_posts = [
            {
                "id": "post_1",
                "title": "보라매공원 저녁 러닝",
                "description": "오늘 저녁 6시",
                "location": "보라매공원",
                "address": "서울특별시 동작구 뚝섬로",
                "sport": "러닝",
                "status": "모집중",
                "author_id": "user_1",
                "author_name": "익명",
                "views": 128,
                "joined_count": 3,
                "max_count": 10,
                "lat": 37.4928,
                "lng": 126.9243,
                "tags": json.dumps(["러닝", "초보환영"]),
                "created_at": "2026-07-14T14:00:00Z",
            },
            {
                "id": "post_2",
                "title": "한강 자전거 모임",
                "description": "주말 함께 타요",
                "location": "여의도공원",
                "address": "서울특별시 영등포구 여의동로",
                "sport": "자전거",
                "status": "모집중",
                "author_id": "user_2",
                "author_name": "익명 2",
                "views": 40,
                "joined_count": 2,
                "max_count": 8,
                "lat": 37.5266,
                "lng": 126.9352,
                "tags": json.dumps(["자전거", "주말"]),
                "created_at": "2026-07-14T15:00:00Z",
            },
        ]
        conn.executemany(
            """
            INSERT INTO posts (
                id, title, description, location, address, sport, status, author_id, author_name,
                views, joined_count, max_count, lat, lng, tags, created_at
            ) VALUES (:id, :title, :description, :location, :address, :sport, :status, :author_id, :author_name,
            :views, :joined_count, :max_count, :lat, :lng, :tags, :created_at)
            """,
            sample_posts,
        )

    place_rows = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    if place_rows == 0:
        conn.execute(
            """
            INSERT INTO places (id, name, address, lat, lng, category, emoji, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "place_1",
                "보라매공원",
                "서울특별시 동작구",
                37.4928,
                126.9243,
                "산책/러닝",
                "🏃",
                "2026-07-14T14:00:00Z",
            ),
        )
        conn.execute(
            """
            INSERT INTO places (id, name, address, lat, lng, category, emoji, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "place_2",
                "여의도공원",
                "서울특별시 영등포구",
                37.5266,
                126.9352,
                "산책/러닝",
                "🏃",
                "2026-07-14T14:00:00Z",
            ),
        )

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_initial_data()
    load_public_data_places()
    yield


app = FastAPI(title="LocalHub Backend", version="0.1.0", lifespan=lifespan)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            address TEXT,
            sport TEXT,
            status TEXT DEFAULT '모집중',
            author_id TEXT DEFAULT 'user_1',
            author_name TEXT DEFAULT '익명',
            views INTEGER DEFAULT 0,
            joined_count INTEGER DEFAULT 0,
            max_count INTEGER DEFAULT 10,
            lat REAL,
            lng REAL,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            edit_password_hash TEXT
        );

        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            author_name TEXT DEFAULT '익명',
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS places (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lng REAL,
            category TEXT,
            emoji TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS post_members (
            id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            joined_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS post_recommendations (
            id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()

    post_info = conn.execute("PRAGMA table_info(posts)").fetchall()
    post_columns = {row[1] for row in post_info}
    if "updated_at" not in post_columns:
        conn.execute("ALTER TABLE posts ADD COLUMN updated_at TEXT")
    if "edit_password_hash" not in post_columns:
        conn.execute("ALTER TABLE posts ADD COLUMN edit_password_hash TEXT")

    place_info = conn.execute("PRAGMA table_info(places)").fetchall()
    columns = {row[1] for row in place_info}
    if "category" not in columns:
        conn.execute("ALTER TABLE places ADD COLUMN category TEXT")
    if "emoji" not in columns:
        conn.execute("ALTER TABLE places ADD COLUMN emoji TEXT")

    rows = conn.execute("SELECT id, name, address FROM places").fetchall()
    for row in rows:
        category, emoji = classify_place_category(row["name"], row["address"])
        conn.execute(
            "UPDATE places SET category = ?, emoji = ? WHERE id = ?",
            (category, emoji, row["id"]),
        )

    conn.commit()
    conn.close()


init_db()


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    location: str | None = None
    address: str | None = None
    sport: str | None = None
    maxCount: int | None = None
    lat: float | None = None
    lng: float | None = None
    tags: list[str] | None = None
    editPassword: str | None = None


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)


class PostUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    address: str | None = None
    sport: str | None = None
    status: str | None = None
    maxCount: int | None = None
    lat: float | None = None
    lng: float | None = None
    tags: list[str] | None = None
    password: str | None = None


class PostDeleteRequest(BaseModel):
    password: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {"success": True, "data": {"status": "ok"}}


@app.get("/api/posts")
def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sport: str | None = None,
    location: str | None = None,
    status: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    conn = get_connection()
    query = "SELECT * FROM posts"
    filters: list[str] = []
    params: list[Any] = []

    if sport:
        filters.append("sport = ?")
        params.append(sport)
    if location:
        filters.append("location = ?")
        params.append(location)
    if status:
        filters.append("status = ?")
        params.append(status)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    if sort == "latest":
        query += " ORDER BY created_at DESC"
    elif sort == "popular":
        query += " ORDER BY views DESC"
    else:
        query += " ORDER BY created_at DESC"

    rows = conn.execute(query, params).fetchall()
    total = len(rows)
    posts = []
    for row in rows[(page - 1) * limit: page * limit]:
        posts.append(
            {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "location": row["location"],
                "address": row["address"],
                "sport": row["sport"],
                "status": row["status"],
                "createdAt": row["created_at"],
                "authorId": row["author_id"],
                "authorName": row["author_name"],
                "views": row["views"],
                "joinedCount": row["joined_count"],
                "maxCount": row["max_count"],
                "lat": row["lat"],
                "lng": row["lng"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "commentCount": 0,
                "isJoined": False,
            }
        )

    conn.close()
    return {
        "success": True,
        "data": {
            "posts": posts,
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@app.post("/api/posts", status_code=201)
def create_post(payload: PostCreateRequest) -> dict[str, Any]:
    conn = get_connection()
    post_id = f"post_{int(conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]) + 1}"
    created_at = "2026-07-14T14:00:00Z"
    edit_password_hash = hash_password(payload.editPassword) if payload.editPassword else None
    conn.execute(
        """
        INSERT INTO posts (
            id, title, description, location, address, sport, status, author_id, author_name,
            views, joined_count, max_count, lat, lng, tags, created_at, updated_at, edit_password_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            post_id,
            payload.title,
            payload.description,
            payload.location,
            payload.address,
            payload.sport,
            "모집중",
            "user_1",
            "익명",
            0,
            0,
            payload.maxCount or 10,
            payload.lat,
            payload.lng,
            json.dumps(payload.tags or []),
            created_at,
            created_at,
            edit_password_hash,
        ),
    )
    conn.commit()
    conn.close()
    return {"success": True, "data": {"id": post_id}}


@app.get("/api/posts/{post_id}")
def get_post(post_id: str) -> dict[str, Any]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    comments = conn.execute(
        "SELECT id, author_name, content, created_at FROM comments WHERE post_id = ? ORDER BY created_at DESC",
        (post_id,),
    ).fetchall()
    conn.close()
    return {
        "success": True,
        "data": {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "location": row["location"],
            "address": row["address"],
            "sport": row["sport"],
            "status": row["status"],
            "createdAt": row["created_at"],
            "authorId": row["author_id"],
            "authorName": row["author_name"],
            "views": row["views"],
            "joinedCount": row["joined_count"],
            "maxCount": row["max_count"],
            "lat": row["lat"],
            "lng": row["lng"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "comments": [
                {
                    "id": comment["id"],
                    "authorName": comment["author_name"],
                    "content": comment["content"],
                    "createdAt": comment["created_at"],
                }
                for comment in comments
            ],
            "isJoined": False,
        },
    }


@app.post("/api/posts/{post_id}/comments")
def create_comment(post_id: str, payload: CommentCreateRequest) -> dict[str, Any]:
    conn = get_connection()
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    comment_id = f"comment_{int(conn.execute('SELECT COUNT(*) FROM comments').fetchone()[0]) + 1}"
    conn.execute(
        "INSERT INTO comments (id, post_id, author_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (comment_id, post_id, "익명", payload.content, "2026-07-14T14:10:00Z"),
    )
    conn.commit()
    conn.close()
    return {
        "success": True,
        "data": {
            "comment": {
                "id": comment_id,
                "authorName": "익명",
                "content": payload.content,
                "createdAt": "2026-07-14T14:10:00Z",
            }
        },
    }


@app.post("/api/posts/{post_id}/view")
def increment_view(post_id: str) -> dict[str, Any]:
    conn = get_connection()
    row = conn.execute("SELECT id, views FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")
    new_views = row["views"] + 1
    conn.execute("UPDATE posts SET views = ? WHERE id = ?", (new_views, post_id))
    conn.commit()
    conn.close()
    return {"success": True, "data": {"views": new_views}}


@app.patch("/api/posts/{post_id}")
def update_post(post_id: str, payload: PostUpdateRequest) -> dict[str, Any]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    if row["edit_password_hash"] and not verify_password(payload.password or "", row["edit_password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="invalid password")

    updates: list[str] = []
    values: list[Any] = []

    if payload.title is not None:
        updates.append("title = ?")
        values.append(payload.title)
    if payload.description is not None:
        updates.append("description = ?")
        values.append(payload.description)
    if payload.location is not None:
        updates.append("location = ?")
        values.append(payload.location)
    if payload.address is not None:
        updates.append("address = ?")
        values.append(payload.address)
    if payload.sport is not None:
        updates.append("sport = ?")
        values.append(payload.sport)
    if payload.status is not None:
        updates.append("status = ?")
        values.append(payload.status)
    if payload.maxCount is not None:
        updates.append("max_count = ?")
        values.append(payload.maxCount)
    if payload.lat is not None:
        updates.append("lat = ?")
        values.append(payload.lat)
    if payload.lng is not None:
        updates.append("lng = ?")
        values.append(payload.lng)
    if payload.tags is not None:
        updates.append("tags = ?")
        values.append(json.dumps(payload.tags))

    updates.append("updated_at = ?")
    values.append("2026-07-15T00:00:00Z")

    if updates:
        values.append(post_id)
        conn.execute(f"UPDATE posts SET {', '.join(updates)} WHERE id = ?", values)

    conn.commit()
    updated = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    return {
        "success": True,
        "data": {
            "id": updated["id"],
            "title": updated["title"],
            "description": updated["description"],
            "location": updated["location"],
            "address": updated["address"],
            "sport": updated["sport"],
            "status": updated["status"],
            "createdAt": updated["created_at"],
            "authorId": updated["author_id"],
            "authorName": updated["author_name"],
            "views": updated["views"],
            "joinedCount": updated["joined_count"],
            "maxCount": updated["max_count"],
            "lat": updated["lat"],
            "lng": updated["lng"],
            "tags": json.loads(updated["tags"]) if updated["tags"] else [],
        },
    }


@app.put("/api/posts/{post_id}")
def update_post_put(post_id: str, payload: PostUpdateRequest) -> dict[str, Any]:
    return update_post(post_id, payload)


@app.delete("/api/posts/{post_id}")
def delete_post(post_id: str, payload: PostDeleteRequest | None = None) -> dict[str, Any]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    if row["edit_password_hash"] and not verify_password((payload.password if payload else "") or "", row["edit_password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="invalid password")

    conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM post_members WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM post_recommendations WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return {"success": True, "data": {"deleted": True}}


@app.post("/api/posts/{post_id}/join")
def join_post(post_id: str) -> dict[str, Any]:
    conn = get_connection()
    post = conn.execute("SELECT id, joined_count, max_count FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    if post["joined_count"] >= post["max_count"]:
        conn.close()
        raise HTTPException(status_code=400, detail="모집 인원이 마감되었습니다.")

    new_joined_count = post["joined_count"] + 1
    conn.execute("UPDATE posts SET joined_count = ? WHERE id = ?", (new_joined_count, post_id))
    conn.commit()
    conn.close()
    return {"success": True, "data": {"joined": True, "joinedCount": new_joined_count, "isJoined": True}}


@app.delete("/api/posts/{post_id}/join")
def leave_post(post_id: str) -> dict[str, Any]:
    conn = get_connection()
    post = conn.execute("SELECT id, joined_count FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    new_joined_count = max(0, post["joined_count"] - 1)
    conn.execute("UPDATE posts SET joined_count = ? WHERE id = ?", (new_joined_count, post_id))
    conn.commit()
    conn.close()
    return {"success": True, "data": {"joined": False, "joinedCount": new_joined_count, "isJoined": False}}


@app.post("/api/posts/{post_id}/recommend")
def toggle_recommend(post_id: str) -> dict[str, Any]:
    conn = get_connection()
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="post not found")

    existing = conn.execute(
        "SELECT id FROM post_recommendations WHERE post_id = ? AND user_id = ?",
        (post_id, "user_1"),
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM post_recommendations WHERE post_id = ? AND user_id = ?", (post_id, "user_1"))
        conn.commit()
        conn.close()
        return {"success": True, "data": {"recommended": False, "recommendCount": 0}}

    conn.execute(
        "INSERT INTO post_recommendations (id, post_id, user_id, created_at) VALUES (?, ?, ?, ?)",
        (f"recommend_{post_id}", post_id, "user_1", "2026-07-14T14:10:00Z"),
    )
    conn.commit()
    conn.close()
    return {"success": True, "data": {"recommended": True, "recommendCount": 1}}


@app.get("/api/places")
def list_places() -> dict[str, Any]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM places ORDER BY name").fetchall()
    places = []
    for row in rows:
        post_count = conn.execute(
            "SELECT COUNT(*) AS count FROM posts WHERE location = ?",
            (row["name"],),
        ).fetchone()["count"]
        places.append(
            {
                "id": row["id"],
                "name": row["name"],
                "address": row["address"],
                "lat": row["lat"],
                "lng": row["lng"],
                "postCount": post_count,
                "category": row["category"] or "기타",
                "emoji": row["emoji"] or "📍",
            }
        )
    conn.close()
    return {
        "success": True,
        "data": {"places": places},
    }


@app.get("/api/places/{place_id}/posts")
def get_posts_by_place(place_id: str) -> dict[str, Any]:
    conn = get_connection()
    place = conn.execute("SELECT id FROM places WHERE id = ?", (place_id,)).fetchone()
    if not place:
        conn.close()
        raise HTTPException(status_code=404, detail="place not found")

    rows = conn.execute(
        "SELECT id, title, status, created_at FROM posts WHERE location = (SELECT name FROM places WHERE id = ?)",
        (place_id,),
    ).fetchall()
    conn.close()
    return {
        "success": True,
        "data": {
            "posts": [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "createdAt": row["created_at"],
                }
                for row in rows
            ]
        },
    }
