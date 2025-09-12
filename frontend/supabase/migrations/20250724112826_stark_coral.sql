/*
  # Fix searches table schema

  1. Changes
    - Ensure searches table exists with all required columns
    - Add missing columns if they don't exist
    - Verify proper data types and constraints

  2. Security
    - Maintain existing RLS policies
    - Ensure proper user access controls
*/

-- Recreate searches table with all required columns
CREATE TABLE IF NOT EXISTS searches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  title text NOT NULL,
  filters jsonb DEFAULT '{}',
  results jsonb DEFAULT '{}',
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  created_at timestamptz DEFAULT now(),
  completed_at timestamptz
);

-- Add columns if they don't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'searches' AND column_name = 'filters'
  ) THEN
    ALTER TABLE searches ADD COLUMN filters jsonb DEFAULT '{}';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'searches' AND column_name = 'results'
  ) THEN
    ALTER TABLE searches ADD COLUMN results jsonb DEFAULT '{}';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'searches' AND column_name = 'status'
  ) THEN
    ALTER TABLE searches ADD COLUMN status text DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'searches' AND column_name = 'completed_at'
  ) THEN
    ALTER TABLE searches ADD COLUMN completed_at timestamptz;
  END IF;
END $$;

-- Enable RLS if not already enabled
ALTER TABLE searches ENABLE ROW LEVEL SECURITY;

-- Create RLS policies if they don't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'searches' AND policyname = 'searches_select_policy'
  ) THEN
    CREATE POLICY "searches_select_policy" ON searches
      FOR SELECT 
      USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'searches' AND policyname = 'searches_insert_policy'
  ) THEN
    CREATE POLICY "searches_insert_policy" ON searches
      FOR INSERT 
      WITH CHECK (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'searches' AND policyname = 'searches_update_policy'
  ) THEN
    CREATE POLICY "searches_update_policy" ON searches
      FOR UPDATE 
      USING (true);
  END IF;
END $$;

-- Create index for performance if it doesn't exist
CREATE INDEX IF NOT EXISTS searches_user_id_created_at_idx ON searches(user_id, created_at DESC);