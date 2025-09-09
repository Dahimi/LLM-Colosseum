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
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
          ⚔️
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Quick Battle</h3>
          <p className="text-xs text-gray-600">Random models face off</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label htmlFor="division" className="block text-sm font-medium text-gray-700 mb-1">
              Choose Division
            </label>
            <select
              id="division"
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 text-sm py-2"
              disabled={isStarting}
            >
              {Object.values(Division).filter(division => division !== Division.KING).map((division) => (
                <option key={division} value={division}>
                  {division === Division.NOVICE && '👶 '}
                  {division === Division.EXPERT && '🎓 '}
                  {division === Division.MASTER && '🥇 '}
                  {division.charAt(0).toUpperCase() + division.slice(1)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex-shrink-0">
            <button
              onClick={handleStartMatch}
              disabled={isStarting || !!matchLimitInfo}
              className="bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors disabled:cursor-not-allowed text-sm font-medium flex items-center gap-2"
            >
              {isStarting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Starting...
                </>
              ) : (
                <>⚔️ Start Battle</>
              )}
            </button>
          </div>
        </div>

        {/* Match limit warning */}
        {matchLimitInfo && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
            <div className="flex items-center">
              <div className="text-amber-600 mr-2">⚠️</div>
              <div>
                <p className="text-sm font-medium text-amber-800">Arena Full</p>
                <p className="text-xs text-amber-700">Maximum concurrent battles reached. Please wait for a battle to finish.</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <p className="text-sm text-green-600">{successMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
} 