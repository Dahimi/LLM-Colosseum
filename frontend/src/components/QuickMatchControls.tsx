'use client';

import { useState } from 'react';
import { Division } from '@/types/arena';

interface QuickMatchControlsProps {
  onMatchStart?: () => void;
}

export function QuickMatchControls({ onMatchStart }: QuickMatchControlsProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDivision, setSelectedDivision] = useState<string>(Division.NOVICE);

  const handleStartMatch = async () => {
    try {
      setIsStarting(true);
      setError(null);
      
      const response = await fetch(`/api/matches/quick?division=${selectedDivision}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start match');
      }
      
      // Match started successfully, trigger refresh of matches list
      onMatchStart?.();
      
      // Show success message
      const match = await response.json();
      const agents = [match.agent1_id, match.agent2_id];
      setSuccessMessage(`Match started between ${agents.join(' and ')}!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start match');
    } finally {
      setIsStarting(false);
    }
  };

  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-lg font-medium mb-4">Quick Match</h3>
        <div className="flex items-center gap-4">
          <div>
            <label htmlFor="division" className="block text-sm font-medium text-gray-700 mb-1">
              Division
            </label>
            <select
              id="division"
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="block w-40 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              disabled={isStarting}
            >
              {Object.values(Division).map((division) => (
                <option key={division} value={division}>
                  {division.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          
          <button
            onClick={handleStartMatch}
            disabled={isStarting}
            className="mt-6 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStarting ? 'Starting...' : 'Start Match'}
          </button>
        </div>
      </div>
      
      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}
      
      {successMessage && (
        <p className="text-green-600 text-sm">{successMessage}</p>
      )}
    </div>
  );
} 