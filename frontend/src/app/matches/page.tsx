import { fetchAgents, fetchMatches, fetchLiveMatches, fetchTournamentStatus } from '@/lib/api';
import { MatchCard } from '@/components/MatchCard';
import { TournamentStatus } from '@/components/TournamentStatus';
import { TournamentControls } from '@/components/TournamentControls';
import { QuickMatchControls } from '@/components/QuickMatchControls';
import Link from 'next/link';
import { Suspense } from 'react';
import { MatchesContent } from './MatchesContent';

export const revalidate = 0; // Disable static page generation

export default async function MatchesPage() {
  // Fetch initial data
  const [agents, tournamentStatus] = await Promise.all([
    fetchAgents(),
    fetchTournamentStatus(),
  ]);

  // Create a map of agents for easy lookup
  const agentsMap = agents.reduce((acc, agent) => {
    acc[agent.profile.name] = agent;  // Use name instead of agent_id
    return acc;
  }, {} as { [key: string]: typeof agents[0] });

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Navigation */}
        <div className="flex justify-between items-center mb-8">
          <Link 
            href="/" 
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Arena
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Matches</h1>
        </div>

        {/* Tournament Status and Controls */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-start">
              <TournamentStatus status={tournamentStatus} />
              <div className="space-y-6">
                <QuickMatchControls />
                <div className="border-t pt-6">
                  <h3 className="text-lg font-medium mb-4 text-gray-900">Tournament Mode</h3>
                  <TournamentControls />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Content with Auto-refresh */}
        <Suspense fallback={<div className="text-gray-900">Loading matches...</div>}>
          <MatchesContent agentsMap={agentsMap} />
        </Suspense>
      </div>
    </main>
  );
} 