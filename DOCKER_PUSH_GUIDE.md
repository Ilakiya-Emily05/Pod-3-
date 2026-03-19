# Docker Image Push Guide

## ✅ Docker Image Built Successfully!

Your optimized Docker image has been created:
- **Image Name**: `powerup-api:latest`
- **Size**: 367MB (optimized with multi-stage build)
- **Tagged for GHCR**: `ghcr.io/powerup-by-kv/api-powerup:qa`

## 🔐 To Push to GitHub Container Registry

### Step 1: Create a GitHub Personal Access Token (PAT)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select these scopes:
   - `read:packages`
   - `write:packages`
   - `delete:packages` (optional, for cleanup)
4. Copy the generated token

### Step 2: Login to GitHub Container Registry

**Option A: Using PowerShell (Recommended)**
```powershell
# Replace YOUR_TOKEN with your actual GitHub PAT
$env:GITHUB_TOKEN = "YOUR_TOKEN"
echo $env:GITHUB_TOKEN | docker login ghcr.io -u PowerUp-by-KV --password-stdin
```

**Option B: Direct login**
```powershell
docker login ghcr.io -u PowerUp-by-KV
# When prompted, paste your GitHub PAT as password
```

### Step 3: Push the Image

```powershell
# Push the qa branch tag
docker push ghcr.io/powerup-by-kv/api-powerup:qa

# Optionally, also push latest tag
docker tag powerup-api:latest ghcr.io/powerup-by-kv/api-powerup:latest
docker push ghcr.io/powerup-by-kv/api-powerup:latest
```

### Step 4: Verify the Package

Visit: https://github.com/PowerUp-by-KV/api-powerup/pkgs/container/api-powerup

## 📦 Image Details

**Optimizations Applied:**
- ✅ Multi-stage build (reduces final image size)
- ✅ Python 3.12-slim base image
- ✅ uv package manager for faster builds
- ✅ Non-root user for security
- ✅ Minimal dependencies copied to production
- ✅ Resource limits configured (512MB max memory)
- ✅ Health check included
- ✅ .dockerignore to exclude unnecessary files

**Resource Configuration:**
- Memory Limit: 512M (max), 128M (reserved)
- CPU Limit: 1.0 (max), 0.25 (reserved)

## 🚀 Usage Examples

**Run with Docker:**
```bash
docker run -d -p 8000:8000 --name powerup-api ghcr.io/powerup-by-kv/api-powerup:qa
```

**Run with Docker Compose:**
```bash
# Create .env file from .env.example first
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```
