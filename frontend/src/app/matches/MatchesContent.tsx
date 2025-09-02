'use client';

import { useState, useCallback, useRef } from 'react';
import { Match } from '@/types/matches';
import { Agent } from '@/types/arena';
import { MatchCard } from '@/components/MatchCard';
import { useEventSource } from '@/lib/hooks/useEventSource';
import { API_BASE_URL, transformMatch, fetchAgents } from '@/lib/api';

interface MatchesContentProps {
  agentsMap: { [key: string]: Agent };
}

interface MatchUpdate {
  matches: Match[];
  liveMatches: Match[];
}

export function MatchesContent({ agentsMap: initialAgentsMap }: MatchesContentProps) {
  const [matches, setMatches] = useState<Match[]>([]);
  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [agentsMap, setAgentsMap] = useState(initialAgentsMap);
  const [error, setError] = useState<string | null>(null);
  // Maximum number of live matches allowed (should match the backend setting)
  const MAX_LIVE_MATCHES = parseInt(process.env.NEXT_PUBLIC_MAX_LIVE_MATCHES || '2');
  
  // Keep track of previous matches
  const previousMatchesRef = useRef<Match[]>([]);

  // Function to update agents data
  const refreshAgents = useCallback(async () => {
    try {
      const agents = await fetchAgents();
      const newAgentsMap = agents.reduce((acc, agent) => {
        acc[agent.profile.name] = agent;
        return acc;
      }, {} as { [key: string]: Agent });
      setAgentsMap(newAgentsMap);
    } catch (e) {
      console.error('Failed to refresh agents:', e);
    }
  }, []);

  // Use SSE for real-time updates
  useEventSource<MatchUpdate>(`${API_BASE_URL}/matches/stream`, {
    onMessage: async (data) => {
      console.log("=== SSE Update Received ===");
      
      // Check if any match has just become completed
      const newlyCompletedMatch = data.matches.some(newMatch => {
        // Find this match in our previous matches
        const previousMatch = previousMatchesRef.current.find(m => m.match_id === newMatch.match_id);
        
        // If the match existed before and its status just changed to COMPLETED
        const justCompleted = previousMatch && 
                            previousMatch.status !== 'COMPLETED' && 
                            newMatch.status === 'COMPLETED';
        
        if (justCompleted) {
          console.log(`Match ${newMatch.match_id} just completed. Previous status: ${previousMatch.status}`);
          return true;
        }
        return false;
      });

      if (newlyCompletedMatch) {
        console.log("Match just completed, refreshing agents");
        await refreshAgents();
      }

      // Update state
      setMatches(data.matches);
      setLiveMatches(data.liveMatches);
      // Update our ref of previous matches
      previousMatchesRef.current = data.matches;
      setError(null);
    },
    onError: () => {
      setError('Failed to connect to match updates stream');
    },
    transformer: (data: any) => ({
      matches: data.matches.map(transformMatch),
      liveMatches: data.liveMatches.map(transformMatch),
    }),
  });

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
          <div className="flex items-center">
            <div className="text-sm text-gray-600 mr-2">Match Slots:</div>
            <div className="flex items-center space-x-1">
              {Array.from({ length: MAX_LIVE_MATCHES }).map((_, i) => (
                <div 
                  key={i} 
                  className={`w-3 h-3 rounded-full ${i < liveMatches.length ? 'bg-red-500' : 'bg-gray-200'}`}
                  title={i < liveMatches.length ? 'Active match' : 'Available slot'}
                />
              ))}
            </div>
            <div className="text-sm text-gray-600 ml-2">
              {liveMatches.length}/{MAX_LIVE_MATCHES}
            </div>
          </div>
        </div>

        {liveMatches.length === 0 ? (
          <p className="text-gray-500">No live matches at the moment.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {liveMatches.map((match) => (
              <MatchCard
                key={match.match_id}
                match={match}
                agents={agentsMap}
              />
            ))}
          </div>
        )}
      </section>

      {/* Recent Matches */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Recent Matches</h2>
        {matches.length === 0 ? (
          <p className="text-gray-500">No matches played yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {matches.map((match) => (
              <MatchCard
                key={match.match_id}
                match={match}
                agents={agentsMap}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
} 