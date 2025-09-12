import React, { useState } from 'react';
import { ArrowLeft, Search, MapPin, Users, Clock, Mail, FileText, Briefcase } from 'lucide-react';
import { supabase } from '../lib/supabase';

interface SearchFormProps {
  onBack: () => void;
  onSearchCreated: () => void;
  initialData?: any;
}

export default function SearchForm({ onBack, onSearchCreated, initialData }: SearchFormProps) {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    search_keywords: initialData?.search_keywords || '',
    location: initialData?.location || '',
    resume_last_updated_days: initialData?.resume_last_updated_days || '30',
    target_candidates: initialData?.target_candidates || '100',
    max_radius: initialData?.max_radius || '25',
    recipient_email: initialData?.recipient_email || '',
    system_prompt: initialData?.system_prompt || '',
    user_prompt: initialData?.user_prompt || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const searchData = {
        name: formData.name || null,
        search_keywords: formData.search_keywords,
        location: formData.location || null,
        resume_last_updated_days: formData.resume_last_updated_days ? parseInt(formData.resume_last_updated_days) : null,
        target_candidates: formData.target_candidates ? parseInt(formData.target_candidates) : null,
        max_radius: formData.max_radius ? parseInt(formData.max_radius) : null,
        recipient_email: formData.recipient_email || null,
        user_prompt: formData.user_prompt || null,
        system_prompt: formData.system_prompt || null,
        status: 'pending' as const,
        filters: {
          name: formData.name,
          search_keywords: formData.search_keywords,
          location: formData.location,
          resume_last_updated_days: formData.resume_last_updated_days,
          target_candidates: formData.target_candidates,
          max_radius: formData.max_radius,
        }
      };

      const { error } = await supabase
        .from('searches')
        .insert([searchData]);

      if (error) throw error;

      onSearchCreated();
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-slate-600 hover:text-slate-800 transition-colors duration-200"
        >
          <ArrowLeft size={20} />
          <span>Zurück</span>
        </button>
        <h1 className="text-3xl font-light text-slate-800">Neue Suche erstellen</h1>
      </div>

      {/* Form */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Search Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Such-Name
              </label>
              <div className="relative">
                <FileText className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="z.B. Q1 Frontend Einstellung, Senior Data Scientists Berlin"
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           placeholder:text-slate-300 placeholder:font-light"
                />
              </div>
            </div>

            {/* Search Keywords */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Suchbegriffe *
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  type="text"
                  name="search_keywords"
                  value={formData.search_keywords}
                  onChange={handleInputChange}
                  placeholder="z.B. React Entwickler, Data Scientist"
                  required
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           placeholder:text-slate-300 placeholder:font-light"
                />
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Standort
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="z.B. Berlin, Deutschland"
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           placeholder:text-slate-300 placeholder:font-light"
                />
              </div>
            </div>

            {/* Max Radius */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Max. Radius (km)
              </label>
              <input
                type="number"
                name="max_radius"
                value={formData.max_radius}
                onChange={handleInputChange}
                placeholder="50"
                placeholder="25"
                min="1"
                className="w-full px-4 py-3 border border-slate-200 rounded-lg 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         placeholder:text-slate-300 placeholder:font-light"
              />
            </div>

            {/* Resume Last Updated */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Lebenslauf aktualisiert
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <select
                  name="resume_last_updated_days"
                  value={formData.resume_last_updated_days}
                  onChange={handleInputChange}
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           appearance-none bg-white"
                >
                  <option value="1">Gestern</option>
                  <option value="3">Innerhalb der letzten 3 Tage</option>
                  <option value="7">In der letzten Woche</option>
                  <option value="30">Im letzten Monat</option>
                  <option value="180">In den letzten 6 Monaten</option>
                </select>
              </div>
            </div>

            {/* Target Candidates */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Ziel-Kandidaten
              </label>
              <div className="relative">
                <Users className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  type="number"
                  name="target_candidates"
                  value={formData.target_candidates}
                  onChange={handleInputChange}
                  placeholder="100"
                  min="1"
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           placeholder:text-slate-300 placeholder:font-light"
                />
              </div>
            </div>

            {/* Recipient Email */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Empfänger E-Mail
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  type="email"
                  name="recipient_email"
                  value={formData.recipient_email}
                  onChange={handleInputChange}
                  placeholder="recruiter@firma.com"
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           placeholder:text-slate-300 placeholder:font-light"
                />
              </div>
            </div>
            
            {/* System Prompt */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                System-Prompt
              </label>
              <textarea
                name="system_prompt"
                value={formData.system_prompt}
                onChange={handleInputChange}
                placeholder="Anweisungen für das KI-System..."
                rows={3}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         placeholder:text-slate-300 placeholder:font-light"
              />
            </div>

            {/* User Prompt */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                User-Prompt
              </label>
              <textarea
                name="user_prompt"
                value={formData.user_prompt}
                onChange={handleInputChange}
                placeholder="Beschreiben Sie, nach welcher Art von Kandidat Sie suchen..."
                rows={3}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         placeholder:text-slate-300 placeholder:font-light"
              />
            </div>

          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onBack}
              className="px-6 py-3 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 
                       transition-colors duration-200"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {loading ? 'Erstelle...' : 'Suche erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}