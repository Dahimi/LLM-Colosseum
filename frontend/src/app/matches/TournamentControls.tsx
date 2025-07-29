'use client';

import { startTournament } from '@/lib/api';
import { useState } from 'react';

interface TournamentControlsProps {
  onTournamentComplete?: () => void;
}

export function TournamentControls({ onTournamentComplete }: TournamentControlsProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartTournament = async () => {
    try {
      setIsLoading(true);
      setError(null);
      await startTournament(1);
      onTournamentComplete?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start tournament');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleStartTournament}
        disabled={isLoading}
        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Running Tournament...' : 'Start New Round'}
      </button>
      
      {error && (
        <p className="text-red-600 text-sm mt-2">{error}</p>
      )}
    </div>
  );
} 