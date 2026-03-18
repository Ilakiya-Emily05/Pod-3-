# Registration & Login Setup Guide

## 1) Clone and enter project

```bash
git clone https://github.com/PowerUp-by-KV/api-powerup.git
cd api-powerup
```

## 2) Create and activate virtual environment (UV)

```bash
uv venv .venv
source .venv/bin/activate
```

## 3) Install dependencies

```bash
uv pip install -r requirements.txt
```

## 4) Configure environment

```bash
cp .env.example .env
```

Update these values in `.env`:

- `DATABASE_URL=postgresql+asyncpg://vaaheesan:password@localhost:5432/powerup_db`
- `DATABASE_URL_SYNC=postgresql+psycopg2://vaaheesan:password@localhost:5432/powerup_db`
- `SECRET_KEY=<your-strong-random-secret>`
- `API_V1_PREFIX=/api/v1`

Google OAuth fields (if using Google signup/login):

- `GOOGLE_CLIENT_ID=<google-client-id>`
- `GOOGLE_CLIENT_SECRET=<google-client-secret>`

Optional (CORS for frontend):

- `CORS_ORIGINS=http://localhost:3000,http://localhost:8081,exp://localhost:8081`

## 5) Start API server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 6) Test endpoints

Swagger:

- `http://127.0.0.1:8000/docs`

Auth endpoints:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`

## 7) Signup/Login payload examples

### Normal signup

```json
{
  "email": "vaahee21@gmail.com",
  "password": "Password123",
  "confirm_password": "Password123",
  "remember_me": true
}
```

### Normal login

```json
{
  "email": "vaahee21@gmail.com",
  "password": "Password123",
  "remember_me": true
}
```

### Google OAuth signup/login (code flow)

```json
{
  "email": "vaahee21@gmail.com",
  "oauth_code": "<google-oauth-code>",
  "oauth_redirect_uri": "<redirect-uri>",
  "oauth_code_verifier": "<pkce-code-verifier>"
}
```

### Google OAuth signup/login (id token)

```json
{
  "email": "vaahee21@gmail.com",
  "oauth_id_token": "<google-id-token>"
}
```
