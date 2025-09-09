'use client';

import { fetchAgents, fetchTournamentStatus } from '@/lib/api';
import { MatchCard } from '@/components/MatchCard';
import { ColosseumStats } from '@/components/ColosseumsStats';
import { LiveActivityIndicator } from '@/components/LiveActivityIndicator';
import { TournamentControls } from '@/components/TournamentControls';
import { QuickMatchControls } from '@/components/QuickMatchControls';
import { KingChallengeButton } from '@/components/KingChallengeButton';
import { ChallengeContributionForm } from '@/components/ChallengeContributionForm';
import { Agent } from '@/types/arena';
import Link from 'next/link';
import { Suspense, useEffect, useState } from 'react';
import { MatchesContent } from './MatchesContent';

export default function MatchesPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tournamentStatus, setTournamentStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveMatchCount, setLiveMatchCount] = useState(0);
  const [totalMatchCount, setTotalMatchCount] = useState(0);

  // Function to fetch all data
  const fetchData = async () => {
    try {
      const [agentsData, tournamentStatusData] = await Promise.all([
        fetchAgents(),
        fetchTournamentStatus(),
      ]);
      
      setAgents(agentsData);
      setTournamentStatus(tournamentStatusData);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setError('Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh tournament status and agents every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Create a map of agents for easy lookup
  const agentsMap = agents.reduce((acc, agent) => {
    acc[agent.profile.name] = agent;  // Use name instead of agent_id
    return acc;
  }, {} as { [key: string]: Agent });

  // Handle match data updates from MatchesContent
  const handleMatchDataUpdate = (liveCount: number, totalCount: number) => {
    setLiveMatchCount(liveCount);
    setTotalMatchCount(totalCount);
  };

  if (isLoading) {
    return (
      <main className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-gray-900">Loading...</div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-red-600">{error}</div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-500 mb-2">🎮 Playground</h1>
          <p className="text-lg text-gray-300">
            Start battles, watch debates, and create challenges
          </p>
        </div>

        {/* Colosseum Stats - Flattened horizontal layout */}
        {tournamentStatus && (
          <ColosseumStats status={tournamentStatus} />
        )}

        {/* Live Activity Indicator */}
        <LiveActivityIndicator 
          liveMatchCount={liveMatchCount} 
          totalMatches={totalMatchCount} 
        />

        {/* Battle Arena - Side by side controls */}
        <div className="mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <QuickMatchControls />
            
            {/* King Challenge Button */}
            {tournamentStatus && (
              <KingChallengeButton 
                currentKing={tournamentStatus.current_king} 
                eligibleChallengers={tournamentStatus.eligible_challengers || []} 
              />
            )}
          </div>
        </div>

        {/* Challenge Creation */}
        <div className="mb-8">
          <ChallengeContributionForm />
        </div>

        {/* Live Matches Section */}
        <div>
          <Suspense fallback={<div className="text-gray-900">Loading matches...</div>}>
            <MatchesContent 
              agentsMap={agentsMap} 
              onMatchDataUpdate={handleMatchDataUpdate}
            />
          </Suspense>
        </div>
      </div>
    </main>
  );
} 