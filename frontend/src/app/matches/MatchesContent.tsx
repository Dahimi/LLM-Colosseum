'use client';

import { useState, useCallback, useRef } from 'react';
import { Match } from '@/types/matches';
import { Agent } from '@/types/arena';
import { MatchCard } from '@/components/MatchCard';
import { useEventSource } from '@/lib/hooks/useEventSource';
import { API_BASE_URL, transformMatch, fetchAgents } from '@/lib/api';

interface MatchesContentProps {
  agentsMap: { [key: string]: Agent };
  onMatchDataUpdate?: (liveCount: number, totalCount: number) => void;
}

interface MatchUpdate {
  matches: Match[];
  liveMatches: Match[];
}

export function MatchesContent({ agentsMap: initialAgentsMap, onMatchDataUpdate }: MatchesContentProps) {
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
  useEventSource<MatchUpdate>(
    `${API_BASE_URL}/matches/stream`,
    {
      onMessage: useCallback((data: MatchUpdate) => {
        try {
          const transformedMatches = data.matches.map(transformMatch);
          const transformedLiveMatches = data.liveMatches.map(transformMatch);
          
          setMatches(transformedMatches);
          setLiveMatches(transformedLiveMatches);
          
          // Notify parent of match data changes
          onMatchDataUpdate?.(transformedLiveMatches.length, transformedMatches.length);
        
          // Check for new matches
          const currentMatchIds = new Set(transformedMatches.map(m => m.match_id));
          const previousMatchIds = new Set(previousMatchesRef.current.map(m => m.match_id));
          
          const newMatches = transformedMatches.filter(m => !previousMatchIds.has(m.match_id));

          if (newMatches.length > 0) {
            console.log(`🎉 ${newMatches.length} new match(es) detected!`);
            refreshAgents();
          }
          
          previousMatchesRef.current = transformedMatches;
        } catch (error) {
          console.error('Error processing match update:', error);
        }
      }, [onMatchDataUpdate, refreshAgents]),
      onError: useCallback((error: any) => {
        console.error('SSE Error:', error);
        setError('Connection lost. Retrying...');
        setTimeout(() => setError(null), 3000);
      }, [])
    }
  );

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  return (
    <div id="live-matches">
      {/* Live Matches */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold flex items-center">
            🔥 Live Battles
            {liveMatches.length > 0 && (
              <span className="ml-2 px-2 py-1 bg-red-100 text-red-600 text-sm rounded-full animate-pulse">
                LIVE
              </span>
            )}
            <span className="ml-2 text-sm font-normal text-gray-500">(Global arena - visible to all users)</span>
          </h2>
          <div className="flex items-center">
            <div className="text-sm text-gray-600 mr-2">Battle Slots:</div>
            <div className="flex items-center space-x-1">
              {Array.from({ length: MAX_LIVE_MATCHES }).map((_, i) => (
                <div 
                  key={i} 
                  className={`w-3 h-3 rounded-full ${i < liveMatches.length ? 'bg-red-500' : 'bg-gray-200'}`}
                  title={i < liveMatches.length ? 'Active battle' : 'Available slot'}
                />
              ))}
            </div>
            <div className="text-sm text-gray-600 ml-2">
              {liveMatches.length}/{MAX_LIVE_MATCHES}
            </div>
          </div>
        </div>

        {liveMatches.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <div className="text-gray-500 mb-2">⚔️</div>
            <p className="text-gray-600 font-medium">No live battles in the global arena</p>
            <p className="text-gray-500 text-sm">Start a battle to see the action here - all users will see your battles!</p>
          </div>
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
        <h2 className="text-2xl font-semibold mb-4 flex items-center">
          📜 Recent Battles
          <span className="ml-2 text-sm font-normal text-gray-500">(Global history - visible to all users)</span>
        </h2>
        {matches.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-600">No recent battles to display</p>
          </div>
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