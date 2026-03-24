# 🚀 Quick Start Guide - PowerUp API

## Prerequisites

- Docker & Docker Compose
- Git

## 📦 Monday Setup - Complete Environment

### Step 1: Clone and Navigate

```bash
cd api-powerup
```

### Step 2: Environment Configuration

The `.env` file is already configured with development defaults:

```bash
# Database credentials
POSTGRES_USER=vaaheesan
POSTGRES_PASSWORD=password
POSTGRES_DB=powerup_db

# Admin credentials (pgAdmin)
PGADMIN_EMAIL=admin@powerup.local
PGADMIN_PASSWORD=admin
```

### Step 3: Start All Services

```bash
docker-compose up -d
```

This starts:
- ✅ **PowerUp API** on http://localhost:8000
- ✅ **PostgreSQL** on localhost:5432
- ✅ **pgAdmin** on http://localhost:8080

### Step 4: Verify Services

```bash
# Check all containers are running
docker-compose ps

# Test API health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Step 5: Access pgAdmin

1. Open http://localhost:8080
2. Login with: `admin@powerup.local` / `admin`
3. Server is pre-configured: `postgres:5432`

### Step 6: Run Database Migrations

```bash
# Access API container
docker-compose exec api bash

# Inside container, run migrations
alembic upgrade head

# Exit container
exit
```

### Step 7: View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔧 Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f pgadmin
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

### Run Migrations

```bash
# Generate new migration
docker-compose exec api alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Check current version
docker-compose exec api alembic current
```

---

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   pgAdmin   │────▶│  PostgreSQL  │◀────│  FastAPI    │
│  :8080      │     │    :5432     │     │    :8000    │
└─────────────┘     └──────────────┘     └─────────────┘
                         ▲
                    ┌────┴────┐
                    │  Data   │
                    │ Volume  │
                    └─────────┘
```

All services communicate over the `powerup-network` bridge network.

---

## 🎯 What's Working

✅ Docker multi-stage build (367MB image)  
✅ PostgreSQL database with persistent storage  
✅ pgAdmin for database management  
✅ Health checks for all services  
✅ Resource constraints (memory & CPU limits)  
✅ Alembic migrations configured  
✅ CORS configured for frontend  
✅ Swagger/OpenAPI documentation  

---

## 📝 Next Steps

After completing Monday setup, you'll work on:

- **Tuesday**: Progress tracking APIs
- **Wednesday**: Admin dashboard APIs
- **Thursday**: Performance optimization
- **Friday**: Final polish and deployment

---

## 🆘 Troubleshooting

### Port Already in Use

Edit `.env` file:
```
API_PORT=8001
DB_PORT=5433
PGADMIN_PORT=8081
```

Then restart: `docker-compose up -d`

### Database Connection Issues

Check logs:
```bash
docker-compose logs postgres
```

Verify connection:
```bash
docker-compose exec postgres psql -U vaaheesan -d powerup_db -c "SELECT 1"
```

### Migration Errors

Reset and re-run:
```bash
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head
```

---

## 📚 Additional Resources

- [API Endpoints Documentation](API_ENDPOINTS_DOCUMENTATION.md)
- [Database Schema](DATABASE_SCHEMA_DOCUMENTATION.md)
- [Docker Push Guide](DOCKER_PUSH_GUIDE.md)
