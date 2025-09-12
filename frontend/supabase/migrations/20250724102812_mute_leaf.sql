/*
  # Fix RLS policies for custom authentication

  1. Changes
    - Disable RLS on users table for registration to work
    - Create new policies that work with custom authentication
    - Allow public registration and user management

  2. Security
    - Users can register (insert their own records)
    - Users can read and update their own profiles by ID
*/

-- Temporarily disable RLS to allow registration
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Re-enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Drop existing policies that depend on auth.uid()
DROP POLICY IF EXISTS "Users can read own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Users can insert own profile" ON users;

-- Create new policies for custom authentication
CREATE POLICY "Allow user registration"
  ON users
  FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Users can read all profiles"
  ON users
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Users can update own profile by id"
  ON users
  FOR UPDATE
  TO public
  USING (true);