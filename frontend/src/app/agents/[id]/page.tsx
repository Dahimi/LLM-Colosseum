'use client';

import { fetchAgent } from '@/lib/api';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Agent } from '@/types/arena';
import { notFound } from 'next/navigation';

export default function AgentPage({ params }: { params: { id: string } }) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const newAgent = await fetchAgent(params.id);
      setAgent(newAgent);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      setError('Failed to fetch agent');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh agent data every 2 seconds
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [params.id]);

  if (isLoading) {
    return <div className="min-h-screen p-8">Loading agent details...</div>;
  }

  if (error || !agent) {
    return notFound();
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <Link 
          href="/" 
          className="text-blue-600 hover:text-blue-800 mb-6 inline-flex items-center"
        >
          ← Back to Arena
        </Link>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{agent.profile.name}</h1>
            <p className="text-gray-700">{agent.profile.description}</p>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Division</h2>
              <p className="text-gray-800 bg-gray-100 rounded-lg px-3 py-2 inline-block">
                {agent.division}
              </p>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">ELO Rating</h2>
              <p className="text-gray-800 bg-gray-100 rounded-lg px-3 py-2 inline-block">
                {Math.round(agent.stats.elo_rating)}
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Performance</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-sm text-gray-600 mb-1">Win Rate</p>
                <p className="text-gray-900 font-medium">
                  {agent.stats.total_matches > 0
                    ? ((agent.stats.wins / agent.stats.total_matches) * 100).toFixed(1)
                    : '0.0'}%
                </p>
              </div>
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-sm text-gray-600 mb-1">Record</p>
                <p className="text-gray-900 font-medium">
                  {agent.stats.wins}W - {agent.stats.losses}L - {agent.stats.draws}D
                </p>
              </div>
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-sm text-gray-600 mb-1">Current Streak</p>
                <p className="text-gray-900 font-medium">
                  {agent.stats.current_streak > 0 
                    ? `🔥 ${agent.stats.current_streak}W`
                    : agent.stats.current_streak < 0
                      ? `❄️ ${Math.abs(agent.stats.current_streak)}L`
                      : '-'}
                </p>
              </div>
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-sm text-gray-600 mb-1">Best Streak</p>
                <p className="text-gray-900 font-medium">{agent.stats.best_streak}W</p>
              </div>
            </div>
          </div>

          {agent.profile.specializations.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Specializations</h2>
              <div className="flex flex-wrap gap-2">
                {agent.profile.specializations.map((spec) => (
                  <span 
                    key={spec}
                    className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                  >
                    {spec}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Match History */}
          {agent.match_history && agent.match_history.length > 0 && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Matches</h2>
              <div className="space-y-4">
                {agent.match_history.map((match) => (
                  <div key={match.match_id} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-medium text-gray-900">{match.challenge.title}</h3>
                        <p className="text-sm text-gray-700">{match.challenge.type}</p>
                      </div>
                      <div className="text-right">
                        <span className={`text-sm px-2 py-1 rounded ${
                          match.winner_id === agent.profile.agent_id
                            ? 'bg-green-100 text-green-800'
                            : match.winner_id
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {match.winner_id === agent.profile.agent_id
                            ? 'Won'
                            : match.winner_id
                            ? 'Lost'
                            : 'Draw'}
                        </span>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600">
                      vs {match.agent1_id === agent.profile.agent_id ? match.agent2_id : match.agent1_id}
                    </div>
                    {match.final_scores && (
                      <div className="mt-2 text-sm text-gray-700">
                        Score: {match.final_scores[agent.profile.agent_id]?.toFixed(1)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Division Changes */}
          {agent.division_changes && agent.division_changes.length > 0 && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Division History</h2>
              <div className="space-y-3">
                {agent.division_changes.map((change, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <span className={`${
                      change.type === 'promotion' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {change.type === 'promotion' ? '↗️' : '↘️'}
                    </span>
                    <span className="text-gray-700">
                      {change.from_division} → {change.to_division}
                    </span>
                    <span className="text-gray-500">
                      ({new Date(change.timestamp).toLocaleDateString()})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
} 