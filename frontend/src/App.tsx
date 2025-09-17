import React, { useState } from 'react';
import Auth from './components/Auth';
import SearchForm from './components/SearchForm';
import SearchList from './components/SearchList';
import SearchDetail from './components/SearchDetail';

interface User {
  id: string;
  username: string;
}

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

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [currentView, setCurrentView] = useState<'list' | 'form' | 'detail'>('list');
  const [selectedSearch, setSelectedSearch] = useState<Search | null>(null);
  const [copiedFilters, setCopiedFilters] = useState<any>(null);

  const handleAuthSuccess = (authenticatedUser: User) => {
    setUser(authenticatedUser);
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentView('list');
    setSelectedSearch(null);
  };

  const handleViewSearch = (search: Search) => {
    setSelectedSearch(search);
    setCurrentView('detail');
  };

  const handleCopyFilters = (filters: any) => {
    // Add " - Copy" to the name
    const filtersWithCopyName = {
      ...filters,
      name: filters.name ? `Kopie von ${filters.name}` : 'Kopie'
    };
    setCopiedFilters(filtersWithCopyName);
    setCurrentView('form');
  };

  if (!user) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <img 
              src="https://matchtrex.concludis.de/download/design/NTE=/logo_matchtrex.jpg" 
              alt="MatchTrex"
              className="h-8"
            />
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 transition-colors duration-200"
              >
                Abmelden
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'list' && (
          <SearchList 
            onViewSearch={handleViewSearch}
            onNewSearch={() => setCurrentView('form')}
          />
        )}
        
        {currentView === 'form' && (
          <SearchForm 
            onBack={() => setCurrentView('list')}
            onSearchCreated={() => {
              setCopiedFilters(null);
              setCurrentView('list');
            }}
            initialData={copiedFilters}
          />
        )}
        
        {currentView === 'detail' && selectedSearch && (
          <SearchDetail 
            search={selectedSearch}
            onBack={() => setCurrentView('list')}
            onCopyFilters={handleCopyFilters}
          />
        )}
      </main>
    </div>
  );
}