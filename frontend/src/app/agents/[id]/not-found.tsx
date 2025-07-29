import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl font-bold mb-4">Agent Not Found</h2>
        <p className="text-gray-600 mb-8">
          The agent you're looking for doesn't exist or has been retired.
        </p>
        <Link 
          href="/" 
          className="text-blue-600 hover:text-blue-800 underline"
        >
          Return to Arena
        </Link>
      </div>
    </main>
  );
} 