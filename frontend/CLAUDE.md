# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MatchTrex Frontend is a React + TypeScript application for a recruiting search system. The application allows users to create and manage candidate search requests, which are processed asynchronously by a backend service. Users can view search history, create new searches with various filters, and copy search configurations.

## Development Commands

```bash
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

## Environment Setup

**Required Environment Variables** (create `.env` file):
```
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**How to get Supabase credentials:**
1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to Settings > API in your Supabase dashboard
3. Copy the "Project URL" as `VITE_SUPABASE_URL`
4. Copy the "anon public" key as `VITE_SUPABASE_ANON_KEY`

## Tech Stack

- **Framework**: Vite + React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Database**: Supabase
- **Linting**: ESLint with TypeScript support

## Architecture

### Core Components Structure

- `App.tsx` - Main application with view routing logic (list/form/detail views)
- `Auth.tsx` - Master password authentication using SHA-256 hashing
- `SearchForm.tsx` - Form for creating new candidate searches
- `SearchList.tsx` - List view with search history and email filtering
- `SearchDetail.tsx` - Detail view for individual searches with results

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

## API Integration

The frontend expects a backend API that handles:
- Asynchronous job processing for candidate searches
- Search result storage and retrieval
- Status updates during processing

Backend communication happens through Supabase, with real-time updates supported by Supabase's real-time features.