'use client';

import { useState } from 'react';
import TicketCategory from './TicketCategory';
import SourceCitations from './SourceCitations';

interface QueryResponse {
  answer: string;
  category: string;
  sources: Array<{ content: string; source: string }>;
  suggested_actions?: string[];
}

export default function QueryInterface() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const apiEndpoint = process.env.NEXT_PUBLIC_API_ENDPOINT || 'YOUR_API_ENDPOINT';
      const res = await fetch(`${apiEndpoint}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: 5 })
      });

      if (!res.ok) throw new Error(`API error: ${res.status}`);

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch answer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <form onSubmit={handleSubmit} className="mb-6">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about CloudSync Pro..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={3}
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-3 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          {loading ? 'Searching...' : 'Ask Question'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {response && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">Detected category:</span>
            <TicketCategory category={response.category} />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Answer:</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{response.answer}</p>
          </div>

          {response.suggested_actions && response.suggested_actions.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Suggested Actions:</h4>
              <ul className="list-disc list-inside space-y-1">
                {response.suggested_actions.map((action, i) => (
                  <li key={i} className="text-gray-700">{action}</li>
                ))}
              </ul>
            </div>
          )}

          <SourceCitations sources={response.sources} />
        </div>
      )}
    </div>
  );
}
