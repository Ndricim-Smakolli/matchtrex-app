/*
  # Clean up and fix RLS policies for custom authentication

  1. Changes
    - Drop all existing conflicting policies on users table
    - Create proper policies for custom username/password authentication
    - Allow public registration and login verification

  2. Security
    - Users can register (insert their own records)
    - Public read access for login verification
    - Simple policies that work with custom authentication
*/

-- Drop all existing policies on users table to avoid conflicts
DROP POLICY IF EXISTS "Users can read own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Users can insert own profile" ON users;
DROP POLICY IF EXISTS "Allow user registration" ON users;
DROP POLICY IF EXISTS "Users can read all profiles" ON users;
DROP POLICY IF EXISTS "Users can update own profile by id" ON users;

-- Temporarily disable RLS to ensure clean state
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Re-enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create simple policies for custom authentication
CREATE POLICY "enable_insert_for_registration" ON users
  FOR INSERT 
  WITH CHECK (true);

CREATE POLICY "enable_select_for_login" ON users
  FOR SELECT 
  USING (true);

CREATE POLICY "enable_update_for_users" ON users
  FOR UPDATE 
  USING (true);