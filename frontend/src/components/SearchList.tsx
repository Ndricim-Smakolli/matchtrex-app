import React, { useState, useEffect } from 'react';
import { Plus, Search, Calendar, MapPin, Users, Filter, X } from 'lucide-react';
import { supabase } from '../lib/supabase';

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

interface SearchListProps {
  onViewSearch: (search: Search) => void;
  onNewSearch: () => void;
}

export default function SearchList({ onViewSearch, onNewSearch }: SearchListProps) {
  const [searches, setSearches] = useState<Search[]>([]);
  const [emailInput, setEmailInput] = useState('');
  const [appliedEmailFilter, setAppliedEmailFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSearches();
  }, []);

  const fetchSearches = async () => {
    try {
      const { data, error } = await supabase
        .from('searches')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setSearches(data || []);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    
    // Set both dates to midnight to compare calendar days
    const dateAtMidnight = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const todayAtMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const diffInMs = todayAtMidnight.getTime() - dateAtMidnight.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    const timeFormat = date.toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
    });
    
    if (diffInDays === 0) {
      return `Heute, ${timeFormat} Uhr`;
    } else if (diffInDays === 1) {
      return `Gestern, ${timeFormat} Uhr`;
    } else if (diffInDays < 7) {
      const dayName = date.toLocaleDateString('de-DE', { weekday: 'long' });
      return `${dayName}, ${timeFormat} Uhr`;
    } else {
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).replace(',', ', ') + ' Uhr';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const handleEmailSearch = () => {
    setAppliedEmailFilter(emailInput);
  };

  const handleClearFilter = () => {
    setEmailInput('');
    setAppliedEmailFilter('');
  };


  const handleEmailInputKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleEmailSearch();
    }
  };

  // Filter searches based on email filter
  const filteredSearches = searches.filter(search => {
    if (!appliedEmailFilter) return true;
    if (!search.recipient_email) return false;
    return search.recipient_email.toLowerCase().includes(appliedEmailFilter.toLowerCase());
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-light text-slate-800">Suchverlauf</h1>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={onNewSearch}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg
                     hover:bg-blue-600 transition-colors duration-200"
          >
            <Plus size={20} />
            <span>Neue Suche</span>
          </button>
        </div>
      </div>

      {/* Email Filter */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 lg:max-w-5xl lg:mx-auto">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyPress={handleEmailInputKeyPress}
              placeholder="Nach E-Mail filtern..."
              className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          {appliedEmailFilter && (
            <button
              onClick={handleClearFilter}
              className="px-3 py-3 border border-slate-200 text-slate-600 rounded-lg 
                       hover:bg-slate-50 transition-colors duration-200 flex items-center"
            >
              <X size={16} />
            </button>
          )}
          <button
            onClick={handleEmailSearch}
            disabled={!emailInput.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200
                     flex items-center space-x-2"
          >
            <Search size={16} />
            <span>Suchen</span>
          </button>
        </div>
        {appliedEmailFilter && (
          <p className="text-sm text-slate-500 mt-2">
            Zeige {filteredSearches.length} von {searches.length} Suchen für "{appliedEmailFilter}"
          </p>
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          Fehler beim Laden der Suchen: {error}
        </div>
      )}

      {/* Search List */}
      {searches.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <Search className="mx-auto w-12 h-12 text-slate-400 mb-4" />
          <h2 className="text-xl font-medium text-slate-600 mb-2">Noch keine Suchen</h2>
          <p className="text-slate-500 mb-6">Erstellen Sie Ihre erste Recruiting-Suche, um zu beginnen</p>
          <button
            onClick={onNewSearch}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200"
          >
            Erste Suche erstellen
          </button>
        </div>
      ) : filteredSearches.length === 0 && emailFilter ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <Mail className="mx-auto w-12 h-12 text-slate-400 mb-4" />
          <h2 className="text-xl font-medium text-slate-600 mb-2">Keine passenden Suchen</h2>
          <p className="text-slate-500 mb-6">Keine Suchen mit Empfänger-E-Mail "{appliedEmailFilter}" gefunden</p>
          <button
            onClick={handleClearFilter}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200"
          >
            Filter löschen
          </button>
        </div>
      ) : (
        <div className="grid gap-4 lg:max-w-5xl lg:mx-auto">
          {filteredSearches.map((search) => (
            <div
              key={search.id}
              onClick={() => onViewSearch(search)}
              className="bg-white p-6 rounded-xl border border-slate-200 hover:border-blue-300 
                       hover:shadow-md transition-all duration-200 cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-slate-800 mb-2">
                    {search.name || search.search_keywords}
                  </h3>
                  {search.name && (
                    <p className="text-sm text-slate-500 mb-2">{search.search_keywords}</p>
                  )}
                  <div className="flex flex-wrap gap-3 text-sm text-slate-600">
                    {search.location && (
                      <div className="flex items-center space-x-1">
                        <MapPin size={14} />
                        <span>{search.location}</span>
                      </div>
                    )}
                    {search.target_candidates && (
                      <div className="flex items-center space-x-1">
                        <Users size={14} />
                        <span>{search.target_candidates} candidates</span>
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <Calendar size={14} />
                      <span>{formatDate(search.created_at)}</span>
                    </div>
                    {search.recipient_email && (
                      <div className="flex items-center space-x-1">
                        <Mail size={14} />
                        <span>{search.recipient_email}</span>
                      </div>
                    )}
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(search.status)}`}>
                  {search.status === 'pending' ? 'ausstehend' : 
                   search.status === 'processing' ? 'verarbeitung' :
                   search.status === 'completed' ? 'abgeschlossen' : 'fehlgeschlagen'}
                </span>
              </div>

              {search.results && search.status === 'completed' && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-sm text-slate-600">
                    {search.results.candidates?.length || search.results.profile_urls?.length || 0} Kandidaten gefunden
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}