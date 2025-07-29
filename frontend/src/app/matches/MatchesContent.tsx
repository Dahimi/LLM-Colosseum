'use client';

import { useEffect, useState } from 'react';
import { fetchMatches, fetchLiveMatches } from '@/lib/api';
import { Match } from '@/types/matches';
import { Agent } from '@/types/arena';
import { MatchCard } from '@/components/MatchCard';

interface MatchesContentProps {
  agentsMap: { [key: string]: Agent };
}

export function MatchesContent({ agentsMap }: MatchesContentProps) {
  const [matches, setMatches] = useState<Match[]>([]);
  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      console.log('Fetching matches data...');
      setIsRefreshing(true);
      const [newMatches, newLiveMatches] = await Promise.all([
        fetchMatches(),
        fetchLiveMatches(),
      ]);
      console.log('Received matches:', newMatches);
      console.log('Received live matches:', newLiveMatches);
      setMatches(newMatches);
      setLiveMatches(newLiveMatches);
      setError(null);
    } catch (e) {
      console.error('Error fetching matches:', e);
      setError(e instanceof Error ? e.message : 'Failed to fetch matches');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Set up polling for live matches
    const interval = setInterval(fetchData, 2000); // Refresh every 2 seconds
    return () => clearInterval(interval);
  }, []);

  // Debug render
  console.log('Rendering with:', { matches, liveMatches, isLoading, error });

  if (isLoading) {
    return <div>Loading matches...</div>;
  }

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  return (
    <div>
      {/* Live Matches */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold flex items-center">
            Live Matches
            {liveMatches.length > 0 && (
              <span className="ml-2 px-2 py-1 bg-red-100 text-red-600 text-sm rounded-full animate-pulse">
                LIVE
              </span>
            )}
          </h2>
          {isRefreshing && (
            <span className="text-sm text-gray-500 animate-pulse">
              Refreshing...
            </span>
          )}
        </div>
        
        {liveMatches.length > 0 ? (
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
            {liveMatches.map((match) => (
              <MatchCard 
                key={match.match_id} 
                match={match}
                agents={agentsMap}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <p className="text-gray-700 italic">No matches currently in progress</p>
          </div>
        )}
      </section>

      {/* Recent Matches */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Recent Matches</h2>
        {matches.length > 0 ? (
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
            {matches.map((match) => (
              <MatchCard 
                key={match.match_id} 
                match={match}
                agents={agentsMap}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <p className="text-gray-700 italic">No matches completed yet</p>
          </div>
        )}
      </section>
    </div>
  );
} 