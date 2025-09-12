/*
  # Create searches table for existing user system

  1. New Tables
    - `searches`
      - `id` (uuid, primary key)
      - `user_id` (references existing users table)
      - `title` (text)
      - `filters` (jsonb) - search criteria
      - `results` (jsonb) - search results
      - `status` (text) - pending, completed, failed
      - `created_at` (timestamp)
      - `completed_at` (timestamp)

  2. Security
    - Enable RLS on searches table
    - Users can only access their own searches
*/

-- Create searches table that references existing users table
CREATE TABLE IF NOT EXISTS searches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  filters jsonb NOT NULL DEFAULT '{}',
  results jsonb DEFAULT '{}',
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  created_at timestamptz DEFAULT now(),
  completed_at timestamptz
);

ALTER TABLE searches ENABLE ROW LEVEL SECURITY;

-- Index for performance
CREATE INDEX IF NOT EXISTS searches_user_id_created_at_idx ON searches(user_id, created_at DESC);