## 🚀 Quick Start Guide

### Prerequisites

- **Docker & Docker Compose** installed
- Or **Python 3.12+** with **MongoDB 7.0+** running locally

---

### Option 1: Docker (Recommended - One Command)

```
cd /home/user/hospital-app

# 1. Copy environment template
cp .env.example .env

# 2. Generate secure secrets (REQUIRED for production)
openssl rand -hex 32  # Run twice - for SECRET_KEY and JWT_SECRET

# 3. Edit .env and replace the placeholder values:
#    SECRET_KEY=your-generated-secret-1
#    JWT_SECRET=your-generated-secret-2
#    MONGO_ROOT_PASSWORD=secure-password-here
nano .env

# 4. Start all services (app + MongoDB + Mongo Express)
docker compose up -d

# 5. Seed database with demo data
docker compose exec app python scripts/seed_database.py

# 6. Verify it's running
docker compose ps
```

**Access Points:**
\| Service \| URL \| \|---------\|-----\| \| **OpenCareOS App** \| http://anurag-home-lab.local:8000 \| \| **API Docs (Swagger)** \| http://anurag-home-lab.local:8000/docs \| \| **ReDoc** \| http://anurag-home-lab.local:8000/redoc \| \| **Mongo Express** \| http://anurag-home-lab.local:8081 \|

---

### Option 2: Manual (Development)

```
cd /home/user/hospital-app

# 1. Create venv & install
python -m venv venv
source venv/bin/activate
pip install -e .

# 2. Ensure MongoDB is running
#    mongod --dbpath /data/db

# 3. Set environment variables
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB_NAME="opencareos"
export SECRET_KEY="dev-secret-key-change-in-production"
export JWT_SECRET="dev-jwt-secret-change-in-production"
export DEBUG=true

# 4. Initialize DB & seed
python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"
python scripts/seed_database.py

# 5. Run app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🔐 Demo Credentials (after seeding)

| Role | Email | Password |
| :---: | :---: | :---: |
| **Admin** | admin@demo.com | demo123 |
| **Doctor** | doctor@demo.com | demo123 |
| **Patient** | patient@demo.com | demo123 |

---

### 🛠 Common Commands

```
# View logs
docker compose logs -f app

# Restart app
docker compose restart app

# Stop everything
docker compose down

# Stop + remove volumes (fresh start)
docker compose down -v

# Run tests
docker compose exec app pytest app/tests/ -v

# Access MongoDB shell
docker compose exec mongodb mongosh -u admin -p
```

---

### ⚠️ Important Notes

1. **Change default passwords** in production
2. **Use strong secrets** - generate with `openssl rand -hex 32`
3. **Configure CORS** in `.env` for your domain: `FRONTEND\_URL=https://yourdomain.com`
4. **Enable HTTPS** in production (reverse proxy with nginx/traefik)
5. **Backup MongoDB** regularly: `docker compose exec mongodb mongodump --out /backup`

---

### 🔧 Troubleshooting

| Issue | Fix |
| :---: | :---: |
| Port 8000 in use | Change `PORT` in `.env` or stop conflicting service |
| MongoDB connection failed | Check `MONGO\_URI` in `.env`, ensure MongoDB is healthy |
| Permission denied on uploads | `sudo chown -R 1000:1000 uploads/` |
| Secrets not loading | Restart container: `docker compose restart app` |
