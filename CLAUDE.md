# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MatchTrex is a full-stack recruiting search system consisting of a React frontend and Python backend. The application allows users to create and manage candidate search requests, which are processed asynchronously by a backend service that scrapes Indeed for candidate CVs and uses AI for evaluation. The system supports both direct frontend interaction and Google Sheets integration.

## Development Commands

### Frontend (React + TypeScript)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Start development server (default port 5173)
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Preview production build
npm run preview
```

### Backend (Python FastAPI)

```bash
# Navigate to backend directory
cd backend

# Setup virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Run the main CV scraping pipeline
python mvp.py

# Run the FastAPI server (for API endpoints)
python api.py

# Run webhook server (for Google Sheets integration)
python webhook_server.py
```

## Environment Setup

### Frontend Environment Variables

**Required Environment Variables** (create `frontend/.env` file):
```
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**How to get Supabase credentials:**
1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to Settings > API in your Supabase dashboard
3. Copy the "Project URL" as `VITE_SUPABASE_URL`
4. Copy the "anon public" key as `VITE_SUPABASE_ANON_KEY`

### Backend Environment Variables

**Required Environment Variables** (create `backend/.env` file):
```
# API Keys
MISTRAL_API_KEY=your_mistral_api_key_here
TWOCAPTCHA_KEY=your_2captcha_key_here

# Google Sheets Configuration
GOOGLE_SHEETS_ID=your_google_sheets_id_here
GOOGLE_SHEETS_CREDENTIALS_PATH=./google_credentials.json

# Email Configuration
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Data Source (google_sheets or excel)
DATA_SOURCE=google_sheets
```

**Additional Setup:**
- Place Google Service Account credentials in `backend/google_credentials.json`
- Ensure Gmail app password is configured for email sending
- Configure 2captcha account for CAPTCHA solving

## Tech Stack

### Frontend
- **Framework**: Vite + React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Database**: Supabase
- **Linting**: ESLint with TypeScript support

### Backend
- **Framework**: Python 3 + FastAPI
- **Web Scraping**: Requests, Selenium WebDriver, BeautifulSoup
- **AI/LLM**: Mistral AI API for candidate evaluation
- **CAPTCHA Solving**: 2captcha integration
- **Email**: SMTP with Gmail
- **Data Sources**: Google Sheets API, Excel (openpyxl)
- **Deployment**: VPS with GitHub Actions CI/CD

## Architecture

### Frontend Components Structure

- `App.tsx` - Main application with view routing logic (list/form/detail views)
- `Auth.tsx` - Master password authentication using SHA-256 hashing
- `SearchForm.tsx` - Form for creating new candidate searches
- `SearchList.tsx` - List view with search history and email filtering
- `SearchDetail.tsx` - Detail view for individual searches with results

### Backend Pipeline Structure

- `mvp.py` - Main CV scraping pipeline with Indeed integration, AI evaluation, and email delivery
- `api.py` - FastAPI server providing REST endpoints for the frontend
- `webhook_server.py` - Flask webhook server for Google Sheets button integration
- `config.py` - Configuration management for environment variables
- `header_randomizer.py` - User-agent rotation for web scraping resilience

### State Management

The app uses React's built-in state management with `useState`. Key state:
- `user` - Current authenticated user (Admin with hardcoded ID)
- `currentView` - Navigation state ('list' | 'form' | 'detail')
- `selectedSearch` - Currently viewed search in detail mode
- `copiedFilters` - Filters copied from one search to create a new one

### Database Integration

- **Supabase Client**: Configured in `src/lib/supabase.ts`
- **Environment Variables**: Requires `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- **Tables**: `searches` (main data) and `master_auth` (authentication)

### Search Data Model

```typescript
interface Search {
  id: string;
  name: string;
  search_keywords: string;
  location: string | null;
  resume_last_updated_days: number | null;
  target_candidates: number | null;
  max_radius: number | null;
  recipient_email: string | null;
  user_prompt: string | null;
  system_prompt: string | null;
  results: any;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at: string | null;
}
```

## Development Configuration

### Vite Development Server

- Port: 5173
- API Proxy: `/api` routes proxy to `https://api.beyondleverage.com:9443`
- CORS enabled for local development

### Code Formatting

- ESLint configuration in `eslint.config.js`
- Uses TypeScript ESLint, React Hooks, and React Refresh plugins
- No specific Prettier configuration detected

## Authentication System

Uses a simple master password system:
- Passwords are SHA-256 hashed client-side
- First-time setup creates the master password hash in `master_auth` table
- Subsequent logins verify against stored hash
- Creates a default "Admin" user session upon successful authentication

## Key Features

1. **Search Creation**: Multi-field form with validation for recruiting searches
2. **Search History**: Paginated list with status indicators and email filtering
3. **Search Duplication**: Copy filters from existing searches to create new ones
4. **Real-time Status**: Display search status (pending/processing/completed/failed)
5. **Results Display**: Show candidate count and results when searches complete

## Styling Conventions

- Uses Tailwind CSS utility classes extensively
- Consistent color scheme: slate grays with blue accents
- Responsive design with mobile-first approach
- Lucide React icons throughout the interface
- German language UI text

## Backend Workflow

The backend operates through a multi-step pipeline:

1. **Data Input**: Search parameters from frontend (via Supabase) or Google Sheets
2. **Indeed Scraping**: Uses hardcoded credentials to search for candidate profiles
3. **CV Download**: Downloads candidate CVs using Selenium WebDriver
4. **AI Evaluation**: Processes CVs through Mistral AI for candidate scoring
5. **Result Compilation**: Aggregates results and generates summaries
6. **Email Delivery**: Sends results via SMTP to specified recipients

### Integration Points

- **Frontend ↔ Backend**: Communication via Supabase database
- **Google Sheets ↔ Backend**: Webhook triggers and direct API calls
- **Backend Services**: FastAPI (port 8000), Webhook Server (Flask), Main Pipeline

### Deployment

- **Production**: Deployed to VPS via GitHub Actions on push to main branch
- **Backend Process**: Runs as background service with process management
- **Health Checks**: API endpoint `/health` for monitoring
- **Logging**: Webhook logs to `webhook_logs.txt`

## API Integration

The frontend expects a backend API that handles:
- Asynchronous job processing for candidate searches
- Search result storage and retrieval
- Status updates during processing

Backend communication happens through Supabase, with real-time updates supported by Supabase's real-time features.