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
    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="division" className="block text-sm font-medium text-blue-900 mb-2">
              Select Division
            </label>
            <select
              id="division"
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="block w-full rounded-md border-blue-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 sm:text-sm"
              disabled={isStarting}
            >
              {Object.values(Division).map((division) => (
                <option key={division} value={division}>
                  {division === 'king' && '👑 '}
                  {division.charAt(0).toUpperCase() + division.slice(1)} Division
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex-shrink-0">
            <button
              onClick={handleStartMatch}
              disabled={isStarting}
              className="mt-7 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm"
            >
              {isStarting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Starting...</span>
                </div>
              ) : (
                'Start Match'
              )}
            </button>
          </div>
        </div>
        
        {/* Fixed height notification container to prevent layout shifts */}
        <div className="min-h-[60px]">
          {matchLimitInfo && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-amber-400 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-amber-800">Match Limit Reached</h4>
                  <div className="mt-1 text-sm text-amber-700">
                    <p>Currently {matchLimitInfo.current} of {matchLimitInfo.max} allowed matches are active.</p>
                    <p className="mt-1">Please wait for some matches to complete before starting a new one.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {error && !matchLimitInfo && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.236 4.53L7.53 10.53a.75.75 0 00-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-800 font-medium">{successMessage}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 