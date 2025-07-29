'use client';

import { startTournament } from '@/lib/api';
import { useState } from 'react';

interface TournamentControlsProps {
  onTournamentComplete?: () => void;
}

export function TournamentControls({ onTournamentComplete }: TournamentControlsProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [numRounds, setNumRounds] = useState(1);

  const handleStartTournament = async () => {
    try {
      setIsLoading(true);
      setError(null);
      await startTournament(numRounds);
      onTournamentComplete?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start tournament');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <div>
          <label htmlFor="numRounds" className="block text-sm font-medium text-gray-700 mb-1">
            Number of Rounds
          </label>
          <input
            type="number"
            id="numRounds"
            min={1}
            max={10}
            value={numRounds}
            onChange={(e) => setNumRounds(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
            className="block w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
        
        <button
          onClick={handleStartTournament}
          disabled={isLoading}
          className="mt-6 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Running Tournament...' : 'Start Tournament'}
        </button>
      </div>
      
      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}
    </div>
  );
} 