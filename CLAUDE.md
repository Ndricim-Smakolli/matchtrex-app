# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MatchTrex is a React-based web application for managing candidate search campaigns. It uses Supabase for backend services and features a master password authentication system.

## Development Commands

### Frontend Development (run from `/frontend` directory)

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview
```

## Architecture

### Tech Stack
- **Frontend**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Backend**: Supabase (PostgreSQL + Auth)
- **Icons**: Lucide React

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