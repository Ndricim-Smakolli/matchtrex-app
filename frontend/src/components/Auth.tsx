import React, { useState } from 'react';
import { Lock, Shield } from 'lucide-react';
import { supabase } from '../lib/supabase';

interface AuthProps {
  onAuthSuccess: (user: { id: string; username: string }) => void;
}

export default function Auth({ onAuthSuccess }: AuthProps) {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Simple hash function to match the stored master password hash
  const hashPassword = async (password: string): Promise<string> => {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const passwordHash = await hashPassword(password);

      // Check if master_auth table has any records
      const { data: existingRecords, error: checkError } = await supabase
        .from('master_auth')
        .select('password_hash')
        .limit(1);

      if (checkError) {
        throw new Error('Database connection failed');
      }

      // If no records exist, insert the master password hash
      if (!existingRecords || existingRecords.length === 0) {
        const { error: insertError } = await supabase
          .from('master_auth')
          .insert([{ password_hash: passwordHash }]);

        if (insertError) {
          throw new Error('Failed to initialize authentication');
        }
      } else {
        // Verify against existing master password in database
        const { data, error } = await supabase
          .from('master_auth')
          .select('password_hash')
          .eq('password_hash', passwordHash)
          .single();

        if (error || !data) {
          throw new Error('Invalid password');
        }
      }

      // Create a session with a default user
      const defaultUser = {
        id: '00000000-0000-0000-0000-000000000001',
        username: 'Admin'
      };

      onAuthSuccess(defaultUser);
    } catch (error: any) {
      if (error.message.includes('No rows')) {
        setError('Invalid password');
      } else {
        setError(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <img 
            src="../../public/matchtrex_logo.png" 
            alt="MatchTrex"
            className="mx-auto mt-8 mb-20 h-16 w-auto"
            style={{ transform: 'scale(1.4)' }}
          />
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <Shield className="text-blue-500" size={32} />
          </div>
          <h2 className="text-3xl font-light text-slate-800">
            Sicherer Zugang
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Geben Sie das Master-Passwort ein, um fortzufahren
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Master-Passwort"
              required
              className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-xl 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !password}
            className="w-full py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
              {loading ? 'Überprüfung...' : 'System betreten'}
          </button>

          <div className="text-center">
            <p className="text-xs text-slate-400">
              Nur für autorisiertes Personal
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}