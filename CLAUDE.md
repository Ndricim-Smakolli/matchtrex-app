# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MatchTrex is a full-stack application for automated candidate sourcing and evaluation. The system combines a React frontend for campaign management with a Python backend for AI-powered candidate processing.

### Architecture Overview
```
Frontend (React/TS) → Supabase (Database) → VPS Backend (Python/FastAPI)
     ↓                      ↓                        ↓
- Campaign UI          - User Auth              - Indeed Scraping  
- Search Management    - Search Storage         - AI Evaluation
- Results Display      - Master Auth            - Email Results
```

## Development Commands

### Frontend Development (run from `/frontend` directory)

```bash
# Install dependencies
npm install

# Start development server (builds and serves production version)
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview
```

### Backend Development (run from `/backend` directory)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Run development server
python mvp.py --server

# Run direct pipeline (for testing)
python mvp.py
```

## Architecture

### Tech Stack
- **Frontend**: React 18 with TypeScript, Tailwind CSS, Vite
- **Database**: Supabase (PostgreSQL + Auth)
- **Backend API**: Python + FastAPI + Uvicorn
- **AI/ML**: Mistral AI, Selenium WebDriver
- **Services**: Google Sheets API, 2Captcha, SMTP
- **Deployment**: Vercel (Frontend), VPS/Hostinger (Backend)
- **CI/CD**: GitHub Actions

### Component Structure

The application follows a single-page architecture with three main views managed by `App.tsx`:

1. **Authentication Flow** (`components/Auth.tsx`):
   - Master password authentication using SHA-256 hashing
   - Stores password hash in Supabase `master_auth` table
   - Auto-initializes on first use

2. **Search Management** (`components/SearchList.tsx`):
   - Lists all search campaigns
   - Real-time status updates via Supabase subscriptions
   - Displays completion progress and candidate counts

3. **Search Creation** (`components/SearchForm.tsx`):
   - Form for creating new searches with filters
   - Supports copying filters from existing searches
   - Stores data in Supabase `searches` table

4. **Search Details** (`components/SearchDetail.tsx`):
   - Displays full search results and configuration
   - Shows formatted prompts and candidate details
   - Allows copying search filters for reuse

### Database Schema

The app expects these Supabase tables:

- **master_auth**: Stores master password hash
- **searches**: Main table for search campaigns with fields:
  - name, search_keywords, location
  - resume_last_updated_days, target_candidates, max_radius
  - recipient_email, user_prompt, system_prompt
  - status (pending/processing/completed/failed)
  - results (JSONB), filters (JSONB)

### Environment Configuration

Required environment variables (create `.env` in `/frontend`):
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### API Proxy Configuration

The Vite config includes a proxy setup for `/api` requests to `https://api.beyondleverage.com:9443` for potential backend integration.

## Key Implementation Details

- **State Management**: Uses React hooks (useState) for local state
- **Data Fetching**: Direct Supabase client calls with real-time subscriptions
- **Styling**: Utility-first approach with Tailwind CSS
- **Type Safety**: Full TypeScript coverage with interface definitions
- **German UI**: All user-facing text is in German

## Backend API Structure

### Core Endpoints
- `GET /` → Service status and available endpoints
- `POST /search` → Trigger candidate search with parameters
- `POST /run-mvp` → Webhook endpoint for pipeline execution
- `GET /status` → Current pipeline status and recent logs
- `GET /health` → Health check with script validation

### Pipeline Architecture
1. **Search Configuration** → Google Sheets or Excel input
2. **Indeed Scraping** → Selenium-based job search
3. **CV Download** → Automated resume collection
4. **AI Evaluation** → Mistral AI candidate scoring
5. **Results Email** → SMTP delivery to recipients

### Key Dependencies
- `fastapi` + `uvicorn` → API server
- `selenium` → Web scraping
- `requests` → HTTP client
- `openpyxl` + `gspread` → Data handling
- `mistral-ai` → AI evaluation

## Deployment Strategy

### Production Setup
- **Frontend**: Deployed on Vercel with automatic builds from main branch
- **Backend**: Hosted on VPS (Hostinger) with GitHub Actions deployment
- **Database**: Supabase cloud instance

### VPS Deployment
- Backend runs on `https://api.beyondleverage.com:9443`
- Nginx reverse proxy with SSL
- GitHub Actions SSH deployment on push to main
- Process management with nohup/systemd