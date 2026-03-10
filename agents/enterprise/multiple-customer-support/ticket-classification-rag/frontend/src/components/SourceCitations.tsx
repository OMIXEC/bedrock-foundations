interface Source {
  content: string;
  source: string;
}

interface SourceCitationsProps {
  sources: Source[];
}

export default function SourceCitations({ sources }: SourceCitationsProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <h4 className="font-semibold text-gray-900 mb-3">Sources:</h4>
      <div className="space-y-3">
        {sources.map((source, index) => (
          <div key={index} className="bg-white p-3 rounded border border-gray-200">
            <p className="text-sm text-gray-600 mb-1">
              <span className="font-medium">Source:</span> {source.source}
            </p>
            <p className="text-sm text-gray-700">{source.content.substring(0, 200)}...</p>
          </div>
        ))}
      </div>
    </div>
  );
}
