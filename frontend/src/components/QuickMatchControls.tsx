'use client';

import { useState } from 'react';
import { Division } from '@/types/arena';

interface QuickMatchControlsProps {
  onMatchStart?: () => void;
}

export function QuickMatchControls({ onMatchStart }: QuickMatchControlsProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchLimitInfo, setMatchLimitInfo] = useState<{
    current: number;
    max: number;
  } | null>(null);
  const [selectedDivision, setSelectedDivision] = useState<string>(Division.NOVICE);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleStartMatch = async () => {
    try {
      setIsStarting(true);
      setError(null);
      setMatchLimitInfo(null);
      
      const response = await fetch(`/api/matches/quick?division=${selectedDivision}`, {
        method: 'POST',
      });
      
      const responseData = await response.json();
      
      if (!response.ok) {
        // Check if this is a match limit error (429 Too Many Requests)
        if (response.status === 429 && responseData.error === 'too_many_matches') {
          setMatchLimitInfo({
            current: responseData.live_match_count,
            max: responseData.max_live_matches
          });
          throw new Error(responseData.message || 'Maximum number of matches reached');
        } else {
          // Handle other errors
          throw new Error(responseData.detail || responseData.message || 'Failed to start match');
        }
      }
      
      // Match started successfully, trigger refresh of matches list
      onMatchStart?.();
      
      // Show success message
      const agents = [responseData.agent1_id, responseData.agent2_id];
      setSuccessMessage(`Match started between ${agents.join(' and ')}!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (e) {
      console.error('Error starting match:', e);
      setError(e instanceof Error ? e.message : 'Failed to start match');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-lg font-medium mb-4 text-gray-900">Quick Match</h3>
        <div className="flex items-center gap-4">
          <div>
            <label htmlFor="division" className="block text-sm font-medium text-gray-900 mb-1">
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
      
      {/* Fixed height notification container to prevent layout shifts */}
      <div className="min-h-[80px] mt-2">
        {matchLimitInfo && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-amber-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-amber-800">Match Limit Reached</h3>
                <div className="mt-1 text-sm text-amber-700">
                  <p>Currently {matchLimitInfo.current} of {matchLimitInfo.max} allowed matches are active.</p>
                  <p className="mt-1">Please wait for some matches to complete before starting a new one.</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {error && !matchLimitInfo && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        
        {successMessage && (
          <p className="text-green-600 text-sm">{successMessage}</p>
        )}
      </div>
    </div>
  );
} 