import QueryInterface from '../components/QueryInterface';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 text-center">
            CloudSync Pro Support Assistant
          </h1>
          <p className="text-gray-600 text-center mb-8">
            Get instant answers about CloudSync Pro. Our AI assistant can help with billing, technical issues, account management, and product questions.
          </p>
          <QueryInterface />
        </div>
      </div>
    </main>
  );
}
