# 🚀 Deployment Guide

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Netlify   │───▶│   Render    │───▶│  Supabase   │
│  (Frontend) │    │  (Backend)  │    │ (PostgreSQL)│
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Step 1: Supabase (Database)

1. Go to [supabase.com](https://supabase.com) → Create project
2. Note your:
   - **Project URL**: `https://xxx.supabase.co`
   - **Connection string**: Settings → Database → URI

---

## Step 2: Render (Backend)

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -e .`
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   SECRET_KEY=[generate-random-string]
   CORS_ORIGINS=https://[your-netlify-app].netlify.app
   ```
5. Deploy → Note your URL: `https://predictr-api.onrender.com`

---

## Step 3: Netlify (Frontend)

1. Go to [netlify.com](https://netlify.com) → Import from Git
2. Connect GitHub repo
3. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/.next`
4. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://predictr-api.onrender.com/api/v1
   ```
5. Deploy!

---

## Step 4: UptimeRobot (Keep Alive)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add Monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://predictr-api.onrender.com/health`
   - **Interval**: 5 minutes

---

## Test Your Deployment

1. **Frontend**: `https://[your-app].netlify.app`
2. **API Docs**: `https://predictr-api.onrender.com/docs`
3. **Health Check**: `https://predictr-api.onrender.com/health`

---

## Environment Variables Summary

### Render (Backend)
| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Supabase connection string |
| `SECRET_KEY` | Random 32+ char string |
| `CORS_ORIGINS` | Your Netlify URL |

### Netlify (Frontend)
| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your Render URL + `/api/v1` |
