// Shared TypeScript interfaces between frontend and backend
// This ensures type consistency across the full stack

export interface User {
  id: string;
  username: string;
}

export interface Search {
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

// Backend API Types
export interface SearchParameters {
  search_keywords: string;
  location?: string;
  max_radius?: number;
  resume_last_updated_days?: number;
  target_candidates?: number;
  recipient_email?: string;
  user_prompt?: string;
  system_prompt?: string;
}

export interface TriggerRequest {
  action: string;
  timestamp?: string;
}

export interface StatusResponse {
  is_running: boolean;
  recent_logs: string[];
  timestamp: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  script_path: string;
  script_exists: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}