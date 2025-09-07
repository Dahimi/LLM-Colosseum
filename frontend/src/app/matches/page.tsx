import { fetchAgents, fetchMatches, fetchLiveMatches, fetchTournamentStatus } from '@/lib/api';
import { MatchCard } from '@/components/MatchCard';
import { TournamentStatus } from '@/components/TournamentStatus';
import { TournamentControls } from '@/components/TournamentControls';
import { QuickMatchControls } from '@/components/QuickMatchControls';
import { KingChallengeButton } from '@/components/KingChallengeButton';
import { ChallengeContributionForm } from '@/components/ChallengeContributionForm';
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
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-gray-500">Matches</h1>
            <Link 
              href="/support" 
              className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white px-4 py-2 rounded-lg transition-all duration-200 font-medium text-sm shadow-sm"
            >
              💝 Support Us
            </Link>
          </div>
        </div>

        {/* Tournament Status and Controls */}
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-lg p-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <TournamentStatus status={tournamentStatus} />
              </div>
              <div className="space-y-4">
                <div className="min-w-[300px]">
                  <h3 className="text-lg font-medium mb-3 text-gray-900">Arena Controls</h3>
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