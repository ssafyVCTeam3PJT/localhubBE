# LocalHub Backend

## 실행 방법

1. Python 3.11 환경 준비
2. 의존성 설치
   ```bash
   C:/Users/SSAFY/AppData/Local/Programs/Python/Python311/python.exe -m pip install -r requirements.txt
   ```
3. 서버 실행
   ```bash
   C:/Users/SSAFY/AppData/Local/Programs/Python/Python311/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. 브라우저 또는 curl로 확인
   - http://127.0.0.1:8000/health
   - http://127.0.0.1:8000/api/posts

## 현재 구현된 API

- GET /health
- GET /api/posts
- POST /api/posts
- GET /api/posts/{post_id}
- POST /api/posts/{post_id}/comments
- POST /api/posts/{post_id}/view
- GET /api/places

## 데이터베이스

- SQLite 파일: localhub.db
- 초기 샘플 데이터가 자동으로 삽입됩니다.
