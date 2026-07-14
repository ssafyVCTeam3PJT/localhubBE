# LocalHub API Spec (Draft)

## 0. 주요 기준
- 백엔드는 FastAPI로 구현한다.
- 프론트는 현재 Vue 기반이며, `fetch` 또는 `axios`로 API를 호출한다.
- 우선순위는 다음 순서로 정한다.
  1. 게시글 CRUD
  2. 참여/댓글/조회수/추천
  3. 지도 장소 조회
  4. 채팅 기능

## 1. 공통 규칙
- Base URL: `/api`
- 응답 형식:
  - 성공: `{ "success": true, "data": ... }`
  - 실패: `{ "success": false, "error": "message" }`
- 인증: 현재는 임시로 비로그인/익명 사용자 기준으로 구현한다. 이후 JWT 확장 가능.
- 시간 포맷: ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`)

## 2. 프론트 우선순위 API

### P1. 게시글 CRUD

#### 2.1 게시글 목록 조회
- Method: `GET /api/posts`
- Purpose: 홈 화면, 리스트 화면에서 게시글 목록 표시
- Query Params:
  - `page` (default: 1)
  - `limit` (default: 20)
  - `sport` (optional)
  - `location` (optional)
  - `status` (optional)
  - `sort` (optional: `latest`, `popular`, `nearby`)
- Response:
```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "post_1",
        "title": "보라매공원 저녁 러닝",
        "description": "오늘 저녁 6시",
        "location": "보라매공원",
        "address": "서울특별시 동작구 ...",
        "sport": "러닝",
        "status": "모집중",
        "createdAt": "2026-07-14T14:00:00Z",
        "authorId": "user_1",
        "authorName": "익명",
        "views": 128,
        "joinedCount": 3,
        "maxCount": 10,
        "lat": 37.4928,
        "lng": 126.9243,
        "tags": ["러닝", "초보환영"],
        "commentCount": 2,
        "isJoined": false
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```

#### 2.2 게시글 상세 조회
- Method: `GET /api/posts/{post_id}`
- Purpose: 상세 카드/상세 페이지 표시
- Response:
```json
{
  "success": true,
  "data": {
    "id": "post_1",
    "title": "보라매공원 저녁 러닝",
    "description": "오늘 저녁 6시",
    "location": "보라매공원",
    "address": "서울특별시 동작구 ...",
    "sport": "러닝",
    "status": "모집중",
    "createdAt": "2026-07-14T14:00:00Z",
    "authorId": "user_1",
    "authorName": "익명",
    "views": 129,
    "joinedCount": 3,
    "maxCount": 10,
    "lat": 37.4928,
    "lng": 126.9243,
    "tags": ["러닝", "초보환영"],
    "comments": [
      {
        "id": "comment_1",
        "authorName": "익명 1",
        "content": "참여하고 싶어요",
        "createdAt": "2026-07-14T14:10:00Z"
      }
    ],
    "isJoined": false
  }
}
```

#### 2.3 게시글 생성
- Method: `POST /api/posts`
- Purpose: 모집글 작성 모달/폼 제출
- Request Body:
```json
{
  "title": "새 모임",
  "description": "설명",
  "location": "보라매공원",
  "address": "서울특별시 동작구 ...",
  "sport": "러닝",
  "maxCount": 6,
  "lat": 37.4928,
  "lng": 126.9243,
  "tags": ["러닝", "초보환영"]
}
```
- Response: 생성된 post 객체

#### 2.4 게시글 수정
- Method: `PUT /api/posts/{post_id}`
- Request Body: 생성과 동일한 필드들 중 변경할 값만 가능

#### 2.5 게시글 삭제
- Method: `DELETE /api/posts/{post_id}`
- Response:
```json
{
  "success": true,
  "data": {
    "deleted": true
  }
}
```

### P2. 참여/댓글/조회수/추천

#### 2.6 댓글 작성
- Method: `POST /api/posts/{post_id}/comments`
- Purpose: 상세 페이지에서 댓글 등록
- Request Body:
```json
{
  "content": "참여하고 싶어요"
}
```
- Response:
```json
{
  "success": true,
  "data": {
    "comment": {
      "id": "comment_1",
      "authorName": "익명 1",
      "content": "참여하고 싶어요",
      "createdAt": "2026-07-14T14:10:00Z"
    }
  }
}
```

#### 2.7 참여하기
- Method: `POST /api/posts/{post_id}/join`
- Purpose: 모집글 참여 버튼
- Response:
```json
{
  "success": true,
  "data": {
    "joined": true,
    "joinedCount": 4,
    "isJoined": true
  }
}
```

#### 2.8 참여 취소
- Method: `DELETE /api/posts/{post_id}/join`
- Response:
```json
{
  "success": true,
  "data": {
    "joined": false,
    "joinedCount": 3,
    "isJoined": false
  }
}
```

#### 2.9 조회수 증가
- Method: `POST /api/posts/{post_id}/view`
- Purpose: 상세 진입 시 1회 증가
- Response:
```json
{
  "success": true,
  "data": {
    "views": 130
  }
}
```

#### 2.10 추천(좋아요) 토글
- Method: `POST /api/posts/{post_id}/recommend`
- Purpose: 추천 수/좋아요 수 반영
- Response:
```json
{
  "success": true,
  "data": {
    "recommended": true,
    "recommendCount": 12
  }
}
```

### P3. 지도/장소

#### 2.11 지도용 장소 목록 조회
- Method: `GET /api/places`
- Purpose: 메인 홈 지도 상단 마커 렌더링
- Response:
```json
{
  "success": true,
  "data": {
    "places": [
      {
        "id": "place_1",
        "name": "보라매공원",
        "address": "서울특별시 동작구 ...",
        "lat": 37.4928,
        "lng": 126.9243,
        "postCount": 3
      }
    ]
  }
}
```

#### 2.12 특정 장소의 모집글 조회
- Method: `GET /api/places/{place_id}/posts`
- Purpose: 지도에서 마커 클릭 시 해당 위치의 모집글 카드 표시
- Response:
```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "post_1",
        "title": "보라매공원 저녁 러닝",
        "status": "모집중",
        "createdAt": "2026-07-14T14:00:00Z"
      }
    ]
  }
}
```

### P4. 채팅 기능 (후순위)

#### 2.13 채팅방 목록 조회
- Method: `GET /api/chats`
- Purpose: 채팅 탭 진입

#### 2.14 채팅방 생성/연결
- Method: `POST /api/chats`
- Request Body:
```json
{
  "postId": "post_1"
}
```

#### 2.15 메시지 전송
- Method: `POST /api/chats/{chat_id}/messages`
- Request Body:
```json
{
  "text": "안녕하세요"
}
```

## 3. 데이터 모델(권장)

### users
- id
- name
- email
- createdAt

### posts
- id
- title
- description
- location
- address
- sport
- status
- authorId
- views
- joinedCount
- maxCount
- lat
- lng
- tags
- createdAt

### comments
- id
- postId
- authorId
- content
- createdAt

### post_members
- id
- postId
- userId
- joinedAt

### post_recommendations
- id
- postId
- userId
- createdAt

### places
- id
- name
- address
- lat
- lng
- createdAt

### chats
- id
- postId
- title
- createdAt

### chat_messages
- id
- chatId
- senderId
- text
- createdAt

## 4. 프론트에서의 사용 예시
- 홈 화면: `GET /api/posts` + `GET /api/places`
- 상세 화면: `GET /api/posts/{id}` + `POST /api/posts/{id}/view`
- 모집글 작성: `POST /api/posts`
- 댓글 작성: `POST /api/posts/{id}/comments`
- 참여하기: `POST /api/posts/{id}/join`
- 지도 클릭: `GET /api/places/{place_id}/posts`

## 5. 구현 순서
1. 게시글 목록/상세/생성 API
2. 댓글/참여/조회수/추천 API
3. 지도 장소 조회 API
4. 채팅 API
5. 프론트에서 `fetch` 기반으로 상태 로직 전환
