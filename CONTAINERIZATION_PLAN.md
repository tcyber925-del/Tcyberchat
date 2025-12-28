# TcyberChatbot Containerization Plan

> **Comprehensive guide for containerizing the TcyberChatbot application**  
> *Created: December 27, 2024*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Service Definitions](#service-definitions)
4. [Docker Configuration](#docker-configuration)
5. [Networking Strategy](#networking-strategy)
6. [Volume & Persistence Strategy](#volume--persistence-strategy)
7. [Environment Variables](#environment-variables)
8. [Build Instructions](#build-instructions)
9. [Deployment Instructions](#deployment-instructions)
10. [Health Checks & Monitoring](#health-checks--monitoring)
11. [Security Considerations](#security-considerations)
12. [Offline/Air-Gapped Deployment](#offlineair-gapped-deployment)

---

## Project Overview

TcyberChatbot is a full-stack AI chatbot application consisting of:

- **Frontend**: Next.js 15 application with React 19, TypeScript, and Tailwind CSS
- **Backend**: FastAPI Python application with AI/ML capabilities (LangChain, Transformers)
- **Reverse Proxy**: Nginx for routing and load balancing
- **Cache**: Redis for session management and caching
- **Database**: PostgreSQL for persistent data storage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Docker Network                              │
│                            (tcyber_network)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        ┌──────────────────┐                         │ │
│  │                        │   Nginx (8080)   │                         │ │
│  │                        │  Reverse Proxy   │                         │ │
│  │                        └────────┬─────────┘                         │ │
│  │                  ┌──────────────┼──────────────┐                    │ │
│  │                  │              │              │                    │ │
│  │                  ▼              ▼              ▼                    │ │
│  │     ┌────────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │     │ Frontend       │  │  Backend    │  │ Redis       │           │ │
│  │     │ (Next.js)      │  │  (FastAPI)  │  │ (Cache)     │           │ │
│  │     │ Port: 3000     │  │  Port: 8000 │  │ Port: 6379  │           │ │
│  │     └────────────────┘  └──────┬──────┘  └─────────────┘           │ │
│  │                                │                                    │ │
│  │                                ▼                                    │ │
│  │                        ┌─────────────┐                              │ │
│  │                        │ PostgreSQL  │                              │ │
│  │                        │ Port: 5432  │                              │ │
│  │                        └─────────────┘                              │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Service Definitions

### 1. Nginx (Reverse Proxy)

| Property | Value |
|----------|-------|
| **Image** | `nginx:alpine` |
| **External Port** | `8080` |
| **Internal Port** | `80` |
| **Purpose** | Route traffic, serve static assets, handle SSL termination |

**Key Features:**
- Routes `/api/*` to backend
- Routes `/` to frontend
- Handles WebSocket upgrades
- SSE (Server-Sent Events) support for streaming
- Gzip compression enabled
- Security headers configured

---

### 2. Frontend (Next.js)

| Property | Value |
|----------|-------|
| **Base Image** | `node:20-alpine` |
| **Port** | `3000` |
| **Build Type** | Multi-stage (deps → builder → production) |
| **Package Manager** | pnpm 8.12.1 |
| **Output Mode** | Standalone |

**Key Features:**
- Uses standalone Next.js output for minimal image size
- Non-root user (`nextjs`) for security
- Health check via wget
- Turbopack enabled for builds

**Dependencies:**
- React 19.1.0
- Next.js 15.5.4
- Tailwind CSS v4
- Radix UI components
- Framer Motion

---

### 3. Backend (FastAPI)

| Property | Value |
|----------|-------|
| **Base Image** | `python:3.11-slim` |
| **Port** | `8000` |
| **Build Type** | Multi-stage (base → deps → production) |
| **Package Manager** | uv (fast pip alternative) |

**Key Features:**
- Multi-stage build for optimized image size
- System dependencies: tesseract-ocr, ffmpeg, libpq-dev
- Non-root user (`appuser`) for security
- Health check via curl
- Uvicorn with single worker

**Core Dependencies:**
- FastAPI + Uvicorn
- LangChain 0.3.27 ecosystem
- ChromaDB for vector storage
- Redis client
- PostgreSQL (psycopg2-binary)
- ML: transformers, torch, sentence-transformers

**System Packages Required:**
- `tesseract-ocr`, `tesseract-ocr-eng` (OCR)
- `ffmpeg` (audio/video processing)
- `libpq-dev` (PostgreSQL)
- `libffi-dev`, `build-essential` (compilation)
- `libsm6`, `libxext6`, `libgl1` (OpenCV)

---

### 4. Redis (Cache)

| Property | Value |
|----------|-------|
| **Image** | `redis:7-alpine` |
| **Internal Port** | `6379` |
| **Persistence** | Disabled (ephemeral cache) |

**Configuration:**
- No data persistence (`--save "" --appendonly no`)
- Memory-only operation for performance
- Health check via `redis-cli ping`

---

### 5. PostgreSQL (Database)

| Property | Value |
|----------|-------|
| **Image** | `postgres:15-alpine` |
| **Internal Port** | `5432` |
| **Persistence** | Named volume |

**Default Credentials (override in production):**
- `POSTGRES_USER`: tcyber
- `POSTGRES_PASSWORD`: secure_password
- `POSTGRES_DB`: tcyber_db

---

## Docker Configuration

### Recommended `docker-compose.yml` Structure

```yaml
services:
  nginx:
    image: nginx:alpine
    container_name: tcyber_nginx
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - tcyber_network

  frontend:
    image: tcyber_frontend:latest
    build:
      context: .
      dockerfile: frontend/Dockerfile
      args:
        PNPM_VERSION: "8.12.1"
        NEXT_PUBLIC_API_URL: "http://localhost:8000"
    container_name: tcyber_frontend
    environment:
      - NODE_ENV=production
      - BACKEND_INTERNAL_URL=http://backend:8000
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://127.0.0.1:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    restart: unless-stopped
    networks:
      - tcyber_network

  backend:
    image: tcyber_backend:latest
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tcyber_backend
    env_file:
      - ./backend/.env
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000
    ports:
      - "8000:8000"
    volumes:
      - backend_data:/app/data
      - backend_uploads:/app/uploads
      - backend_logs:/app/logs
    depends_on:
      redis:
        condition: service_started
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - tcyber_network

  redis:
    image: redis:7-alpine
    container_name: tcyber_redis
    command: ["redis-server", "--save", "", "--appendonly", "no"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - tcyber_network

  postgres:
    image: postgres:15-alpine
    container_name: tcyber_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-tcyber}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_password}
      POSTGRES_DB: ${POSTGRES_DB:-tcyber_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tcyber -d tcyber_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - tcyber_network

networks:
  tcyber_network:
    driver: bridge

volumes:
  backend_data:
    driver: local
  backend_uploads:
    driver: local
  backend_logs:
    driver: local
  postgres_data:
    driver: local
```

---

### Backend Dockerfile Template

```dockerfile
# Stage 1: Base image with system dependencies
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --default-timeout=1000 uv

WORKDIR /app

# Stage 2: Install Python dependencies
FROM base AS deps

COPY requirements.txt requirements.docker.txt ./

ENV UV_SYSTEM_PYTHON=1
RUN if [ -s requirements.docker.txt ]; then \
        uv pip install --retries 10 --no-cache-dir -r requirements.docker.txt ; \
    else \
        uv pip install --retries 10 --no-cache-dir -r requirements.txt ; \
    fi

# Stage 3: Production image
FROM base AS production

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

WORKDIR /app
COPY . .

RUN mkdir -p logs uploads data

RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

---

### Frontend Dockerfile Template

```dockerfile
# Stage 1: Install dependencies
FROM node:20-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

RUN pnpm config set fetch-retries 5 && \
    pnpm config set fetch-retry-maxtimeout 60000 && \
    pnpm config set fetch-timeout 60000

COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY frontend/package.json ./frontend/

RUN pnpm install --no-frozen-lockfile --filter frontend...

# Stage 2: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

COPY --from=deps /app ./
COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

WORKDIR /app/frontend
RUN pnpm run build
WORKDIR /app

# Stage 3: Production image
FROM node:20-alpine AS production

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --chown=nextjs:nodejs --from=builder /app/frontend/.next/standalone ./
COPY --chown=nextjs:nodejs --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --chown=nextjs:nodejs --from=builder /app/frontend/public ./frontend/public

USER nextjs

WORKDIR /app/frontend
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
```

---

### Recommended `.dockerignore`

```
# Git
.git
.gitignore
.github

# IDE/Editor
.vscode
.cursor
.roo
.kilocode
.specify
.gittools

# Python
__pycache__
*.pyc
.venv
.pytest_cache
.ruff_cache

# Node
node_modules
.next
.swc

# Documentation (not needed in image)
*.md
docs/

# Logs & temp
logs/
*.log
tmp/
uploads/

# Large files
*.bundle

# Test files
tests/
test-results/
playwright-report/

# Environment files (will be mounted or passed as env)
.env
.env.*

# Build artifacts
TcyberChatbot-cleaned/
repo-mirror.git/

# Keep Next.js build output for prebuilt scenarios
!frontend/.next
!frontend/.next/**
```

---

## Networking Strategy

### Internal Network
- All services communicate on `tcyber_network` (bridge driver)
- Service discovery via container names (e.g., `backend:8000`, `redis:6379`)

### External Access
| Service | External Port | Purpose |
|---------|---------------|---------|
| Nginx | 8080 | Main entry point |
| Backend | 8000 | Direct API access (dev/debug) |

### Firewall Recommendations
```bash
# Production: Only expose nginx
-p 8080:80

# Development: Also expose backend for debugging
-p 8000:8000
```

---

## Volume & Persistence Strategy

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `backend_data` | `/app/data` | Application data, ChromaDB vectors |
| `backend_uploads` | `/app/uploads` | User uploaded files |
| `backend_logs` | `/app/logs` | Application logs |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database |

### Backup Strategy
```bash
# Backup PostgreSQL
docker exec tcyber_postgres pg_dump -U tcyber tcyber_db > backup.sql

# Backup volumes
docker run --rm -v backend_data:/data -v $(pwd):/backup alpine tar czf /backup/data_backup.tar.gz /data
```

---

## Environment Variables

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_HOST` | Redis hostname | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:8080` |
| `POSTGRES_USER` | Database user | `tcyber` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTGRES_DB` | Database name | `tcyber_db` |

### AI Provider Keys (in `.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google AI API key |
| `TAVILY_API_KEY` | Tavily search API key |
| `GROQ_API_KEY` | Groq API key |

### Frontend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `BACKEND_INTERNAL_URL` | Internal backend URL | `http://backend:8000` |

---

## Build Instructions

### Full Build
```bash
# Build all images
docker compose build

# Build with no cache (fresh build)
docker compose build --no-cache

# Build specific service
docker compose build backend
docker compose build frontend
```

### Optimized Build
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker compose build

# Parallel builds
docker compose build --parallel
```

---

## Deployment Instructions

### Development
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Production
```bash
# Pull latest images (if using registry)
docker compose pull

# Deploy with specific configuration
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Rolling update
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend
```

### Useful Commands
```bash
# Restart a service
docker compose restart backend

# Scale service (if supported)
docker compose up -d --scale backend=2

# Remove volumes on shutdown
docker compose down -v

# View service status
docker compose ps
```

---

## Health Checks & Monitoring

### Endpoints

| Service | Health Check | Endpoint |
|---------|--------------|----------|
| Backend | HTTP | `GET /health` |
| Frontend | HTTP | `GET /` (200 response) |
| Redis | CLI | `redis-cli ping` |
| PostgreSQL | CLI | `pg_isready` |

### Monitoring Integration
```yaml
# Add to backend for Prometheus metrics
environment:
  - PROMETHEUS_ENABLED=true
ports:
  - "9090:9090"  # Prometheus metrics
```

### Log Aggregation
```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# Follow with timestamps
docker compose logs -f --timestamps
```

---

## Security Considerations

### 1. Non-Root Users
- Backend runs as `appuser` (UID 1000)
- Frontend runs as `nextjs` (UID 1001)

### 2. Secrets Management
```yaml
# Use Docker secrets for production
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  backend:
    secrets:
      - db_password
```

### 3. Network Isolation
- Internal services only accessible within `tcyber_network`
- Only nginx exposed to host

### 4. Image Security
```bash
# Scan images for vulnerabilities
docker scout cves tcyber_backend:latest
docker scout cves tcyber_frontend:latest
```

### 5. Read-Only Filesystems
```yaml
services:
  nginx:
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
```

---

## Offline/Air-Gapped Deployment

### Prerequisites (with network access)
```bash
# 1. Build images
docker compose build

# 2. Save images
docker save tcyber_backend:latest | gzip > tcyber_backend.tar.gz
docker save tcyber_frontend:latest | gzip > tcyber_frontend.tar.gz
docker save nginx:alpine | gzip > nginx.tar.gz
docker save redis:7-alpine | gzip > redis.tar.gz
docker save postgres:15-alpine | gzip > postgres.tar.gz

# 3. Pack pnpm for offline frontend builds
npm pack pnpm@8.12.1
mv pnpm-8.12.1.tgz frontend/offline/pnpm.tgz

# 4. Create prebuilt frontend archive
cd frontend
pnpm install && pnpm run build
tar -czf offline/prebuilt.tar.gz .next/standalone .next/static public
```

### Deployment (air-gapped)
```bash
# 1. Load images
docker load < tcyber_backend.tar.gz
docker load < tcyber_frontend.tar.gz
docker load < nginx.tar.gz
docker load < redis.tar.gz
docker load < postgres.tar.gz

# 2. Start services
docker compose up -d
```

### Trimmed Requirements
For offline Docker builds, use `requirements.docker.txt` which contains minimal dependencies without heavy ML packages:
- Core: FastAPI, SQLAlchemy, Redis
- Minimal ML: LangChain, ChromaDB
- Omits: torch, transformers, whisper

---

## Quick Reference

### Common Issues

| Issue | Solution |
|-------|----------|
| Frontend can't connect to backend | Check `BACKEND_INTERNAL_URL` uses internal network name |
| Backend health check fails | Increase `start_period` for ML model loading |
| PostgreSQL connection refused | Wait for `service_healthy` condition |
| Out of disk space | Prune unused images: `docker system prune` |

### Performance Tuning

```yaml
# Increase backend workers for more CPU
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Add Redis memory limit
redis:
  deploy:
    resources:
      limits:
        memory: 512M
```

---

*This plan provides a complete guide for containerizing the TcyberChatbot application. Adjust configurations based on your specific deployment environment and requirements.*
