import React from 'react';
import { ArrowLeft, Copy, ExternalLink, Calendar, MapPin, Briefcase, FileText, Search, Clock, Users, Mail, Navigation } from 'lucide-react';
import { formatPromptText } from '../utils/formatPromptText';

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

interface SearchDetailProps {
  search: Search;
  onBack: () => void;
  onCopyFilters: (filters: any) => void;
}

export default function SearchDetail({ search, onBack, onCopyFilters }: SearchDetailProps) {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-slate-600 hover:text-slate-800 transition-colors duration-200"
        >
          <ArrowLeft size={20} />
          <span>Zurück zu Suchen</span>
        </button>

        <button
          onClick={() => onCopyFilters({
            name: search.name,
            search_keywords: search.search_keywords,
            location: search.location || '',
            resume_last_updated_days: search.resume_last_updated_days?.toString() || '',
            target_candidates: search.target_candidates?.toString() || '',
            max_radius: search.max_radius?.toString() || '',
            recipient_email: search.recipient_email || '',
            user_prompt: search.user_prompt || '',
            system_prompt: search.system_prompt || '',
          })}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg 
                   hover:bg-blue-600 transition-colors duration-200"
        >
          <Copy size={16} />
          <span>Filter kopieren</span>
        </button>
      </div>

      {/* Search Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h1 className="text-2xl font-light text-slate-800 mb-4">
          {search.name || search.search_keywords}
        </h1>
        {search.name && (
          <p className="text-slate-600 mb-4">{search.search_keywords}</p>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center space-x-2 text-slate-600">
            <Calendar size={16} />
            <span>Erstellt: {formatDate(search.created_at)}</span>
          </div>
          {search.completed_at && (
            <div className="flex items-center space-x-2 text-slate-600">
              <Calendar size={16} />
              <span>Abgeschlossen: {formatDate(search.completed_at)}</span>
            </div>
          )}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              search.status === 'completed' ? 'bg-green-500' :
              search.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <span className="text-slate-600">
              {search.status === 'pending' ? 'Ausstehend' : 
               search.status === 'processing' ? 'Verarbeitung' :
               search.status === 'completed' ? 'Abgeschlossen' : 'Fehlgeschlagen'}
            </span>
          </div>
        </div>
      </div>

      {/* Search Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-medium text-slate-800 mb-4">Suchfilter</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {search.name && (
            <div>
              <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
                <FileText size={14} />
                <span>Such-Name</span>
              </label>
              <p className="text-slate-600">{search.name}</p>
            </div>
          )}

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <Search size={14} />
              <span>Position</span>
            </label>
            <p className="text-slate-600">{search.search_keywords || 'Nicht angegeben'}</p>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <MapPin size={14} />
              <span>Standort</span>
            </label>
            <p className="text-slate-600">{search.location || 'Beliebig'}</p>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <Clock size={14} />
              <span>Lebenslauf aktualisiert (Tage)</span>
            </label>
            <p className="text-slate-600">{search.resume_last_updated_days || 'Nicht angegeben'}</p>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <Users size={14} />
              <span>Ziel-Kandidaten</span>
            </label>
            <p className="text-slate-600">{search.target_candidates || 'Nicht angegeben'}</p>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <Navigation size={14} />
              <span>Max. Radius (km)</span>
            </label>
            <p className="text-slate-600">{search.max_radius || 'Nicht angegeben'}</p>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-1">
              <Mail size={14} />
              <span>Empfänger-E-Mail</span>
            </label>
            <p className="text-slate-600">{search.recipient_email || 'Nicht angegeben'}</p>
          </div>
        </div>
      </div>

      {/* Prompts Section */}
      {(search.user_prompt || search.system_prompt) && (
        <div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Prompt - Left Side */}
            {search.system_prompt && (
              <div 
                className="bg-white rounded-xl border border-slate-200 p-6"
                role="region"
                aria-labelledby="system-prompt-title"
              >
                <h3 id="system-prompt-title" className="text-lg font-medium text-slate-800 mb-4">
                  System-Prompt
                </h3>
                <div className="max-w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 
                              rounded-xl p-6 overflow-y-auto text-sm font-mono leading-relaxed 
                              text-slate-800 dark:text-slate-200 break-words
                              focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2
                              sm:p-5 min-[320px]:p-4">
                  <div className="prose prose-slate dark:prose-invert max-w-none 
                                prose-p:mb-3 prose-p:last:mb-0 prose-ul:my-0 prose-li:my-1.5
                                prose-p:text-sm prose-li:text-sm">
                    {formatPromptText(search.system_prompt)}
                  </div>
                </div>
              </div>
            )}

            {/* User Prompt - Right Side */}
            {search.user_prompt && (
              <div 
                className="bg-white rounded-xl border border-slate-200 p-6"
                role="region"
                aria-labelledby="user-prompt-title"
              >
                <h3 id="user-prompt-title" className="text-lg font-medium text-slate-800 mb-4">
                  User-Prompt
                </h3>
                <div className="max-w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 
                              rounded-xl p-6 overflow-y-auto text-sm font-mono leading-relaxed 
                              text-slate-800 dark:text-slate-200 break-words
                              focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2
                              sm:p-5 min-[320px]:p-4">
                  <div className="prose prose-slate dark:prose-invert max-w-none 
                                prose-p:mb-3 prose-p:last:mb-0 prose-ul:my-0 prose-li:my-1.5
                                prose-p:text-sm prose-li:text-sm">
                    {formatPromptText(search.user_prompt)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-medium text-slate-800 mb-4">Ergebnisse</h2>
        
        {search.status === 'pending' || search.status === 'processing' ? (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-500">Suche läuft...</p>
          </div>
        ) : search.status === 'failed' ? (
          <div className="text-center py-8">
            <p className="text-red-600">Suche fehlgeschlagen. Bitte versuchen Sie es erneut.</p>
          </div>
        ) : search.results?.candidates?.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 mb-4">
              {search.results.candidates.length} Kandidaten gefunden
            </p>
            
            {search.results.candidates.map((candidate: any, index: number) => (
              <div key={index} className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors duration-200">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-slate-800">{candidate.name || `Kandidat #${index + 1}`}</h3>
                  {(candidate.cv_url || candidate.profile_url || candidate.url) && (
                    <a
                      href={candidate.cv_url || candidate.profile_url || candidate.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 text-blue-500 hover:text-blue-600 text-sm"
                    >
                      <span>Profil ansehen</span>
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
                
                <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                  {candidate.position && (
                    <div className="flex items-center space-x-1">
                      <Briefcase size={14} />
                      <span>{candidate.position}</span>
                    </div>
                  )}
                  {candidate.location && (
                    <div className="flex items-center space-x-1">
                      <MapPin size={14} />
                      <span>{candidate.location}</span>
                    </div>
                  )}
                </div>
                
                {candidate.summary && (
                  <p className="text-sm text-slate-600 mt-2">{candidate.summary}</p>
                )}
                
                {/* Display profile links if available */}
                {(candidate.profile_links || candidate.links) && (
                  <div className="mt-3 pt-2 border-t border-slate-100">
                    <p className="text-xs font-medium text-slate-700 mb-2">Profil-Links:</p>
                    <div className="flex flex-wrap gap-2">
                      {(candidate.profile_links || candidate.links).map((link: string, linkIndex: number) => (
                        <a
                          key={linkIndex}
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 px-2 py-1 bg-blue-50 text-blue-600 
                                   rounded text-xs hover:bg-blue-100 transition-colors duration-200"
                        >
                          <span>Link {linkIndex + 1}</span>
                          <ExternalLink size={12} />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : search.results?.profile_urls?.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 mb-4">
              {search.results.profile_urls.length} Kandidaten gefunden
            </p>
            
            {search.results.profile_urls.map((profileUrl: string, index: number) => (
              <div key={index} className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors duration-200">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-slate-800">Kandidat #{index + 1}</h3>
                  <a
                    href={profileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-blue-500 hover:text-blue-600 text-sm"
                  >
                    <span>Profil ansehen</span>
                    <ExternalLink size={14} />
                  </a>
                </div>
                
                <div className="text-sm text-slate-600">
                  <p className="break-all">{profileUrl}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-slate-500">Keine Kandidaten für diese Suche gefunden.</p>
          </div>
        )}
      </div>
    </div>
  );
}