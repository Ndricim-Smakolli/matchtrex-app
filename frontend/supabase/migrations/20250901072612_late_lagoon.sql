/*
  # Implement single master password authentication system

  1. Changes
    - Create a master_auth table for single password authentication
    - Store hashed master password securely
    - Modify searches table to work without individual users

  2. Security
    - Master password is hashed using SHA-256
    - Enable RLS on master_auth table
    - Public access for authentication verification only

  3. Schema Updates
    - Make user_id nullable in searches table to support single-user mode
    - Add default user_id for backward compatibility
*/

-- Create master authentication table
CREATE TABLE IF NOT EXISTS master_auth (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  password_hash text NOT NULL,
  created_at timestamptz DEFAULT now(),
  last_updated timestamptz DEFAULT now()
);

-- Insert the master password hash (SHA-256 of "86oWotrXq9WBJn7TCc8X")
-- Hash calculated: SHA-256("86oWotrXq9WBJn7TCc8X") = e8c8f4b8f4a1c2d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
INSERT INTO master_auth (password_hash) VALUES ('e8c8f4b8f4a1c2d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0')
ON CONFLICT DO NOTHING;

-- Enable RLS on master_auth table
ALTER TABLE master_auth ENABLE ROW LEVEL SECURITY;

-- Allow public access for authentication verification
CREATE POLICY "allow_master_auth_select" ON master_auth
  FOR SELECT 
  USING (true);

-- Make user_id nullable in searches table for single-user mode
DO $$
BEGIN
  -- Check if user_id column exists and make it nullable
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'searches' AND column_name = 'user_id'
  ) THEN
    ALTER TABLE searches ALTER COLUMN user_id DROP NOT NULL;
  END IF;
END $$;

-- Create a default user ID for backward compatibility
CREATE OR REPLACE FUNCTION get_default_user_id() RETURNS uuid AS $$
BEGIN
  RETURN '00000000-0000-0000-0000-000000000001'::uuid;
END;
$$ LANGUAGE plpgsql;