# PowerUp API Development Setup Scripts

This directory contains scripts to help set up the PowerUp API development environment.

## 🚀 Quick Start

### For Windows Users (PowerShell)
```powershell
.\scripts\setup_dev_env.ps1
```

### For Linux/Mac Users (Bash)
```bash
./scripts/setup_dev_env.sh
```

## 📋 What the Setup Script Does

1. **Environment Configuration**
   - Copies `.env.example` to `.env` if it doesn't exist
   - Sets up default development settings

2. **Dependencies Installation**
   - Runs `uv sync` to install Python dependencies
   - Ensures all required packages are available

3. **Database Setup**
   - Runs Alembic migrations: `uv run alembic upgrade head`
   - Applies all pending database migrations

4. **Data Seeding**
   - Runs pre-assessment data seeding: `uv run python scripts/seed_assessments.py`
   - Populates database with initial assessment data

## 📝 Prerequisites

Before running the setup script, ensure you have:

1. **Python 3.12+** installed
2. **uv** (Python package manager) installed
3. **PostgreSQL** database running locally
4. **Git** for version control

## 🔧 Database Configuration

The setup script expects a PostgreSQL database. Update your `.env` file with your database credentials:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/powerup_db
DATABASE_URL_SYNC=postgresql+psycopg2://username:password@localhost:5432/powerup_db
```

## 🌱 Assessment Seeding

The `seed_assessments.py` script is maintained by Vishvaa and seeds:
- Pre-assessment set 1
- Pre-assessment set 2

If the seeding script is missing or fails, please contact Vishvaa to complete the implementation.

## 🚀 Starting the Server

After setup completes, start the development server:

```bash
./run.sh
```

Or on Windows:
```powershell
.\run.sh
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in `.env` file
- Verify database exists and is accessible

### Dependency Issues
- Ensure `uv` is installed and up to date
- Try running `uv sync --dev` manually

### Permission Issues (Linux/Mac)
- Make sure setup script is executable: `chmod +x scripts/setup_dev_env.sh`

## 📞 Support

For issues with:
- **Setup scripts**: Contact Lokesh Y
- **Assessment seeding**: Contact Vishvaa
- **Database migrations**: Contact Vaaheesan
