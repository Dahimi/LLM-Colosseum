'use client';

import { useState } from 'react';
import { Match } from '@/types/matches';
import { Agent } from '@/types/arena';
import { MatchCard } from '@/components/MatchCard';
import { useEventSource } from '@/lib/hooks/useEventSource';
import { API_BASE_URL, transformMatch } from '@/lib/api';

interface MatchesContentProps {
  agentsMap: { [key: string]: Agent };
}

interface MatchUpdate {
  matches: Match[];
  liveMatches: Match[];
}

export function MatchesContent({ agentsMap }: MatchesContentProps) {
  const [matches, setMatches] = useState<Match[]>([]);
  const [liveMatches, setLiveMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Use SSE for real-time updates
  useEventSource<MatchUpdate>(`${API_BASE_URL}/matches/stream`, {
    onMessage: (data) => {
      setMatches(data.matches);
      setLiveMatches(data.liveMatches);
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