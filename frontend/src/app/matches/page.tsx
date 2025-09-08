'use client';

import { fetchAgents, fetchTournamentStatus } from '@/lib/api';
import { MatchCard } from '@/components/MatchCard';
import { TournamentStatus } from '@/components/TournamentStatus';
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
          <h1 className="text-4xl font-bold text-gray-700 mb-2">🎮 Playground</h1>
          <p className="text-lg text-gray-600">
            Start matches, watch debates, and contribute challenges
          </p>
        </div>

        {/* Tournament Status and Controls */}
        {tournamentStatus && (
          <div className="mb-6">
            <div className="bg-white rounded-lg shadow-lg p-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <TournamentStatus status={tournamentStatus} />
                </div>
                <div className="space-y-4">
                  <div className="min-w-[300px]">
                    <h3 className="text-lg font-medium mb-3 text-gray-900">Platform Controls</h3>
                    <div className="grid grid-cols-1 gap-3">
                      <QuickMatchControls />
                      
                      {/* King Challenge Button */}
                      <KingChallengeButton 
                        currentKing={tournamentStatus.current_king} 
                        eligibleChallengers={tournamentStatus.eligible_challengers || []} 
                      />
                    </div>
                  </div>
                  
                  {/* Tournament controls are hidden for now */}
                  {/* 
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-medium mb-4 text-gray-900">Tournament Mode</h3>
                    <TournamentControls />
                  </div>
                  */}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Challenge Contribution */}
        <div className="mb-6">
          <ChallengeContributionForm />
        </div>

        {/* Dynamic Content with Auto-refresh */}
        <Suspense fallback={<div className="text-gray-900">Loading matches...</div>}>
          <MatchesContent agentsMap={agentsMap} />
        </Suspense>
      </div>
    </main>
  );
} 