'use client';

import { useState, useEffect } from 'react';
import { startKingChallenge, fetchLiveMatches } from '@/lib/api';
import { Match } from '@/types/matches';

interface KingChallengeButtonProps {
  currentKing: string | null;
  eligibleChallengers: Array<{
    name: string;
    elo_rating: number;
    win_rate: number;
    current_streak: number;
  }>;
  onChallengeStart?: () => void;
}

export function KingChallengeButton({ 
  currentKing, 
  eligibleChallengers, 
  onChallengeStart 
}: KingChallengeButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeChallenge, setActiveChallenge] = useState<Match | null>(null);

  const hasKing = !!currentKing;
  const hasChallengers = eligibleChallengers.length > 0;
  const canChallenge = hasKing && hasChallengers;

  // Check for active king challenges
  useEffect(() => {
    const checkActiveChallenge = async () => {
      try {
        const liveMatches = await fetchLiveMatches();
        const kingChallenge = liveMatches.find(m => m.match_type === 'KING_CHALLENGE');
        const previousActiveChallenge = activeChallenge;
        setActiveChallenge(kingChallenge || null);
        
        // Clear success message when challenge completes
        if (previousActiveChallenge && !kingChallenge) {
          setSuccessMessage(null);
        }
      } catch (e) {
        console.error('Error checking for active king challenges:', e);
      }
    };

    checkActiveChallenge();
    const interval = setInterval(checkActiveChallenge, 2000); // Check every 2 seconds instead of 5
    return () => clearInterval(interval);
  }, []);

  const handleStartChallenge = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      
      const match = await startKingChallenge();
      setActiveChallenge(match);
      
      // Show success message
      setSuccessMessage(`King challenge started between ${match.agent1_id} and ${match.agent2_id}!`);
      
      // Notify parent component
      onChallengeStart?.();
      
      // Reset loading state after successful challenge start
      setIsLoading(false);
      
    } catch (e) {
      console.error('Error starting king challenge:', e);
      setError(e instanceof Error ? e.message : 'Failed to start king challenge');
      // Reset loading state on error
      setIsLoading(false);
    }
  };

  // If there's an active king challenge, show that instead
  if (activeChallenge) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
        <h3 className="text-lg font-medium text-amber-900 mb-2">👑 King Challenge In Progress</h3>
        
        <div className="mb-3">
          <p className="text-amber-800">
            <span className="font-medium">{activeChallenge.agent2_id}</span> is challenging King <span className="font-medium">{activeChallenge.agent1_id}</span>!
          </p>
          <p className="text-sm text-amber-700 mt-1">
            Challenge: {activeChallenge.challenge.title}
          </p>
        </div>
        
        <div className="flex items-center justify-center">
          <div className="animate-pulse flex items-center space-x-2 bg-amber-100 text-amber-800 px-3 py-2 rounded-lg">
            <div className="w-2 h-2 bg-amber-600 rounded-full"></div>
            <span>Challenge in progress...</span>
          </div>
        </div>
      </div>
    );
  }

  // If there's no king or no challengers, show an informative message
  if (!canChallenge) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-2">King Challenge</h3>
        {!hasKing ? (
          <p className="text-gray-600">No King has been crowned yet. The best Master will be promoted to King after winning enough matches.</p>
        ) : !hasChallengers ? (
          <div>
            <p className="text-gray-600 mb-2">No eligible Master challengers available.</p>
            <p className="text-sm text-gray-500">Masters need ≥75% win rate or ≥5 win streak to challenge the King.</p>
          </div>
        ) : (
          <p className="text-gray-600">Something went wrong. Please check the tournament status.</p>
        )}
      </div>
    );
  }

  // There is a king and there are challengers
  const topChallenger = eligibleChallengers[0];

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
      <h3 className="text-lg font-medium text-amber-900 mb-2">👑 King Challenge</h3>
      
      <div className="mb-3">
        <p className="text-amber-800">
          <span className="font-medium">{topChallenger.name}</span> is ready to challenge King <span className="font-medium">{currentKing}</span>!
        </p>
        <p className="text-sm text-amber-700 mt-1">
          Challenger stats: {topChallenger.elo_rating.toFixed(0)} ELO, {topChallenger.win_rate.toFixed(1)}% win rate
          {topChallenger.current_streak > 0 && `, ${topChallenger.current_streak} win streak`}
        </p>
        <p className="text-xs text-amber-600 mt-2 italic">
          💡 Defeating the King earns prestige and ELO, but the crown is only lost through sustained poor performance.
        </p>
      </div>
      
      <div className="flex flex-col gap-2">
        <button
          onClick={handleStartChallenge}
          disabled={isLoading}
          className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (successMessage ? 'Challenge In Progress...' : 'Starting Challenge...') : 'Start King Challenge'}
        </button>
        
        {error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        
        {successMessage && (
          <p className="text-green-600 text-sm">{successMessage}</p>
        )}
      </div>
    </div>
  );
} 