/*
  # Update master password hash
  
  1. Changes
    - Update the existing master password hash to match the correct SHA-256 hash
    - The hash corresponds to the master password: 86oWotrXq9WBJn7TCc8X
  
  2. Security
    - Password is properly hashed using SHA-256
*/

UPDATE master_auth 
SET password_hash = 'bc20e0f5e040d00391e96dd6ca7200d6382f0dd9f51d74188ae48f82b6ff7196',
    last_updated = now()
WHERE id = 'f9a49d50-161a-424a-a73a-ced5ca7fdfb5';