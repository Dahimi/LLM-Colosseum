'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Match, MatchStatus } from '@/types/matches';
import { Agent } from '@/types/arena';
import { fetchMatch, fetchAgents, API_BASE_URL, transformMatch } from '@/lib/api';
import { useEventSource } from '@/lib/hooks/useEventSource';
import { use } from 'react';

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function MatchPage({ params }: PageProps) {
  // Unwrap params using React.use()
  const { id } = use(params);
  
  const [match, setMatch] = useState<Match | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [matchData, agentsData] = await Promise.all([
          fetchMatch(id),
          fetchAgents(),
        ]);
        setMatch(matchData);
        setAgents(agentsData);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load match data');
      } finally {
        setIsLoading(false);
      }
    };
    loadInitialData();
  }, [id]);

  // Use SSE for real-time updates
  useEventSource<Match>(`${API_BASE_URL}/matches/${id}/stream`, {
    onMessage: (data) => {
      setMatch(data);
      setError(null);
    },
    onError: () => {
      setError('Failed to connect to match updates stream');
    },
    // Only enable SSE after initial data is loaded
    enabled: !isLoading && !!match,
    transformer: transformMatch,
  });

  if (isLoading) {
    return <div>Loading match details...</div>;
  }

  if (error || !match) {
    return <div className="text-red-600">{error || 'Match not found'}</div>;
  }

  const agent1 = agents.find(a => a.profile.name === match.agent1_id);
  const agent2 = agents.find(a => a.profile.name === match.agent2_id);

  if (!agent1 || !agent2) {
    return <div className="text-red-600">Failed to load agent data</div>;
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link href="/matches" className="text-blue-600 hover:text-blue-800">
            ← Back to Matches
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-2xl font-bold mb-6 text-indigo-900">
            Match Details
            {match.status === MatchStatus.IN_PROGRESS && (
              <span className="ml-2 px-2 py-1 bg-red-100 text-red-600 text-sm rounded-full animate-pulse">
                LIVE
              </span>
            )}
          </h1>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Agent 1 */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-blue-800">{agent1.profile.name}</h2>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-900">Division: {agent1.division}</p>
                <p className="text-blue-900">Rating: {Math.round(agent1.stats.elo_rating)}</p>
              </div>
            </div>

            {/* Agent 2 */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-purple-800">{agent2.profile.name}</h2>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-purple-900">Division: {agent2.division}</p>
                <p className="text-purple-900">Rating: {Math.round(agent2.stats.elo_rating)}</p>
              </div>
            </div>
          </div>

          {/* Match Status */}
          <div className="mt-8 p-4 bg-indigo-50 rounded-lg">
            <h3 className="font-semibold mb-2 text-indigo-900">Match Status</h3>
            <p className="text-indigo-900">Status: <span className="font-medium">{match.status}</span></p>
            <p className="text-indigo-900">
              Started: <span className="font-medium">{match.created_at ? new Date(match.created_at).toLocaleString() : 'Not started'}</span>
            </p>
            {match.completed_at && (
              <p className="text-indigo-900">
                Ended: <span className="font-medium">{new Date(match.completed_at).toLocaleString()}</span>
              </p>
            )}
            {match.status === MatchStatus.COMPLETED && (
              <div className="mt-2">
                {match.winner_id ? (
                  <p className="font-semibold text-emerald-700">
                    Winner: {match.winner_id}
                  </p>
                ) : (
                  <p className="font-semibold text-amber-700">
                    Result: Draw
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Challenge Description */}
          <div className="mt-8 p-4 bg-indigo-50 rounded-lg">
            <h3 className="font-semibold mb-2 text-indigo-900">Challenge</h3>
            <p className="text-lg font-medium text-indigo-900 mb-2">{match.challenge.title}</p>
            <p className="whitespace-pre-wrap text-indigo-900">{match.challenge.description}</p>
          </div>

          {/* Match Responses */}
          {match.match_type === 'DEBATE' ? (
            <div className="mt-8">
              <h3 className="font-semibold mb-4 text-indigo-900">Debate Transcript</h3>
              {match.transcript && match.transcript.length > 0 ? (
                <div className="space-y-4">
                  {match.transcript.map((response, index) => {
                    const isAgent1 = response.agent_id === match.agent1_id;
                    const agent = isAgent1 ? agent1 : agent2;
                    return (
                      <div 
                        key={index}
                        className={`flex ${isAgent1 ? 'justify-start' : 'justify-end'}`}
                      >
                        <div className={`max-w-[80%] ${isAgent1 ? 'bg-blue-50' : 'bg-purple-50'} p-4 rounded-lg`}>
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`font-medium ${isAgent1 ? 'text-blue-800' : 'text-purple-800'}`}>
                              {agent.profile.name}
                            </span>
                            <span className={`text-sm ${isAgent1 ? 'text-blue-700' : 'text-purple-700'}`}>
                              {index === 0 ? '(Opening Statement)' : `(Turn ${Math.floor(index/2 + 1)})`}
                            </span>
                          </div>
                          <p className={`whitespace-pre-wrap ${isAgent1 ? 'text-blue-900' : 'text-purple-900'}`}>
                            {response.response_text}
                          </p>
                          {response.response_time > 0 && (
                            <p className={`text-sm mt-2 ${isAgent1 ? 'text-blue-700' : 'text-purple-700'}`}>
                              Response time: {response.response_time.toFixed(2)}s
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <p className="text-indigo-900">
                    {match.status === MatchStatus.COMPLETED 
                      ? 'This debate has concluded.'
                      : 'Waiting for agents to begin the debate...'}
                  </p>
                </div>
              )}

              {/* Show final scores for completed debates */}
              {match.status === MatchStatus.COMPLETED && match.final_scores && (
                <div className="mt-6 bg-indigo-50 p-4 rounded-lg">
                  <h4 className="font-medium text-indigo-900 mb-2">Final Scores</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-blue-800">{agent1.profile.name}</p>
                      <p className="text-blue-900 font-medium">
                        {match.final_scores[match.agent1_id]?.toFixed(1) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-purple-800">{agent2.profile.name}</p>
                      <p className="text-purple-900 font-medium">
                        {match.final_scores[match.agent2_id]?.toFixed(1) || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-8">
              <h3 className="font-semibold mb-4 text-indigo-900">Agent Responses</h3>
              {/* Agent 1 Response */}
              {match.agent1_response && (
                <div className="mb-6">
                  <h4 className="font-medium text-blue-800 mb-2">{agent1.profile.name}'s Response</h4>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-blue-900">{match.agent1_response.response_text}</p>
                    <p className="text-sm text-blue-700 mt-2">
                      Response time: {match.agent1_response.response_time.toFixed(2)}s
                      {match.agent1_response.score !== undefined && (
                        <span className="ml-4">Score: {match.agent1_response.score.toFixed(1)}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Agent 2 Response */}
              {match.agent2_response && (
                <div>
                  <h4 className="font-medium text-purple-800 mb-2">{agent2.profile.name}'s Response</h4>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-purple-900">{match.agent2_response.response_text}</p>
                    <p className="text-sm text-purple-700 mt-2">
                      Response time: {match.agent2_response.response_time.toFixed(2)}s
                      {match.agent2_response.score !== undefined && (
                        <span className="ml-4">Score: {match.agent2_response.score.toFixed(1)}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* No responses yet */}
              {!match.agent1_response && !match.agent2_response && (
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <p className="text-indigo-900">Waiting for agent responses...</p>
                </div>
              )}

              {/* Show final scores for completed regular matches */}
              {match.status === MatchStatus.COMPLETED && match.final_scores && (
                <div className="mt-6 bg-indigo-50 p-4 rounded-lg">
                  <h4 className="font-medium text-indigo-900 mb-2">Final Scores</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-blue-800">{agent1.profile.name}</p>
                      <p className="text-blue-900 font-medium">
                        {match.final_scores[match.agent1_id]?.toFixed(1) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-purple-800">{agent2.profile.name}</p>
                      <p className="text-purple-900 font-medium">
                        {match.final_scores[match.agent2_id]?.toFixed(1) || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Judge Evaluations */}
          {match.status === MatchStatus.COMPLETED && match.evaluations && match.evaluations.length > 0 && (
            <div className="mt-8">
              <h3 className="font-semibold mb-4 text-indigo-900">Judge Evaluations</h3>
              <div className="space-y-6">
                {match.evaluations.map((evaluation, index) => (
                  <div key={index} className="bg-emerald-50 p-4 rounded-lg">
                    <h4 className="font-medium text-emerald-800 mb-4">Judge {index + 1}</h4>
                    
                    {/* Overall Reasoning */}
                    <div className="mb-4">
                      <p className="font-medium text-emerald-800 mb-1">Overall Analysis</p>
                      <p className="whitespace-pre-wrap text-emerald-900">{evaluation.overall_reasoning}</p>
                    </div>

                    {/* Comparative Analysis */}
                    <div className="mb-4">
                      <p className="font-medium text-emerald-800 mb-1">Comparative Analysis</p>
                      <p className="whitespace-pre-wrap text-emerald-900">{evaluation.comparative_analysis}</p>
                    </div>

                    {/* Key Differentiators */}
                    {evaluation.key_differentiators.length > 0 && (
                      <div className="mb-4">
                        <p className="font-medium text-emerald-800 mb-1">Key Differentiators</p>
                        <ul className="list-disc list-inside space-y-1">
                          {evaluation.key_differentiators.map((point, i) => (
                            <li key={i} className="text-emerald-900">{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Scores */}
                    <div className="mt-4 grid grid-cols-2 gap-4 bg-emerald-100/50 p-3 rounded-lg">
                      <div>
                        <p className="text-blue-800">{agent1.profile.name}</p>
                        <p className="text-blue-900 font-medium">
                          Score: {evaluation.agent1_total_score.toFixed(1)}
                        </p>
                      </div>
                      <div>
                        <p className="text-purple-800">{agent2.profile.name}</p>
                        <p className="text-purple-900 font-medium">
                          Score: {evaluation.agent2_total_score.toFixed(1)}
                        </p>
                      </div>
                    </div>
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