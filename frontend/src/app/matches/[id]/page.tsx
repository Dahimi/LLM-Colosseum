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
              <h3 className="font-semibold mb-6 text-indigo-900 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-3.774-.9L3 21l1.9-6.226A8.955 8.955 0 013 12a8 8 0 018-8c4.418 0 8 3.582 8 8z" />
                </svg>
                Debate Conversation
              </h3>
              
              {match.transcript && match.transcript.length > 0 ? (
                <div className="bg-gradient-to-b from-gray-50 to-white border border-gray-200 rounded-xl p-6 space-y-6 max-h-[600px] overflow-y-auto">
                  {match.transcript.map((response, index) => {
                    const isAgent1 = response.agent_id === match.agent1_id;
                    const agent = isAgent1 ? agent1 : agent2;
                    const isFirstMessage = index === 0;
                    const turnNumber = Math.floor(index / 2) + 1;
                    
                    return (
                      <div 
                        key={index}
                        className={`flex ${isAgent1 ? 'justify-start' : 'justify-end'} animate-fade-in`}
                      >
                        <div className={`max-w-[85%] ${isAgent1 ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200' : 'bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200'} border rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200`}>
                          {/* Message Header */}
                          <div className={`flex items-center justify-between px-4 py-2 border-b ${isAgent1 ? 'border-blue-200 bg-blue-50/50' : 'border-purple-200 bg-purple-50/50'} rounded-t-2xl`}>
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${isAgent1 ? 'bg-blue-500' : 'bg-purple-500'}`}>
                                {agent.profile.name.charAt(0)}
                              </div>
                              <span className={`font-semibold ${isAgent1 ? 'text-blue-800' : 'text-purple-800'}`}>
                                {agent.profile.name}
                              </span>
                              <span className={`text-xs px-2 py-1 rounded-full ${isAgent1 ? 'bg-blue-200 text-blue-700' : 'bg-purple-200 text-purple-700'}`}>
                                {isFirstMessage ? 'Opening' : `Turn ${turnNumber}`}
                              </span>
                            </div>
                            <div className={`text-xs ${isAgent1 ? 'text-blue-600' : 'text-purple-600'}`}>
                              {new Date(response.timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                          
                          {/* Message Content */}
                          <div className="p-4">
                            <p className={`whitespace-pre-wrap leading-relaxed ${isAgent1 ? 'text-blue-900' : 'text-purple-900'}`}>
                              {response.response_text}
                            </p>
                            {response.response_time > 0 && (
                              <div className={`flex items-center gap-1 mt-3 text-xs ${isAgent1 ? 'text-blue-600' : 'text-purple-600'}`}>
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{response.response_time.toFixed(2)}s</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 p-8 rounded-xl text-center">
                  <svg className="w-12 h-12 text-indigo-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-3.774-.9L3 21l1.9-6.226A8.955 8.955 0 013 12a8 8 0 018-8c4.418 0 8 3.582 8 8z" />
                  </svg>
                  <p className="text-indigo-700 font-medium">
                    {match.status === MatchStatus.COMPLETED 
                      ? 'This debate has concluded.'
                      : 'Waiting for the debate to begin...'}
                  </p>
                  {match.status !== MatchStatus.COMPLETED && (
                    <p className="text-indigo-600 text-sm mt-1">The agents will start their opening statements shortly.</p>
                  )}
                </div>
              )}

              {/* Show final scores for completed debates */}
              {match.status === MatchStatus.COMPLETED && match.final_scores && (
                <div className="mt-6 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 p-6 rounded-xl">
                  <h4 className="font-semibold text-emerald-800 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Final Scores
                  </h4>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
                        {match.final_scores[match.agent1_id]?.toFixed(1) || 'N/A'}
                      </div>
                      <p className="text-blue-800 font-medium">{agent1.profile.name}</p>
                    </div>
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-purple-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
                        {match.final_scores[match.agent2_id]?.toFixed(1) || 'N/A'}
                      </div>
                      <p className="text-purple-800 font-medium">{agent2.profile.name}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-8">
              <h3 className="font-semibold mb-6 text-indigo-900 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-3.774-.9L3 21l1.9-6.226A8.955 8.955 0 013 12a8 8 0 018-8c4.418 0 8 3.582 8 8z" />
                </svg>
                Agent Responses
              </h3>
              
              {(match.agent1_response || match.agent2_response) ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Agent 1 Response */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                        {agent1.profile.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-semibold text-blue-800">{agent1.profile.name}</h4>
                        <p className="text-blue-600 text-sm">Rating: {Math.round(agent1.stats.elo_rating)}</p>
                      </div>
                    </div>
                    
                    {match.agent1_response ? (
                      <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200">
                        <div className="bg-blue-500 text-white px-4 py-2 flex items-center justify-between">
                          <span className="font-medium">Response</span>
                          <div className="flex items-center gap-2 text-blue-100">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-sm">{match.agent1_response.response_time.toFixed(2)}s</span>
                          </div>
                        </div>
                        <div className="p-6">
                          <p className="whitespace-pre-wrap text-blue-900 leading-relaxed">
                            {match.agent1_response.response_text}
                          </p>
                        </div>
                        {match.agent1_response.score !== undefined && (
                          <div className="bg-blue-500/10 px-4 py-2 border-t border-blue-200">
                            <div className="flex items-center justify-center">
                              <span className="text-blue-700 text-sm font-medium">Score: </span>
                              <span className="text-blue-800 text-lg font-bold ml-1">
                                {match.agent1_response.score.toFixed(1)}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="bg-blue-50 border-2 border-dashed border-blue-200 rounded-xl p-8 text-center">
                        <svg className="w-8 h-8 text-blue-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <p className="text-blue-600">Waiting for response...</p>
                      </div>
                    )}
                  </div>

                  {/* Agent 2 Response */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center text-white font-bold">
                        {agent2.profile.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-semibold text-purple-800">{agent2.profile.name}</h4>
                        <p className="text-purple-600 text-sm">Rating: {Math.round(agent2.stats.elo_rating)}</p>
                      </div>
                    </div>
                    
                    {match.agent2_response ? (
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200">
                        <div className="bg-purple-500 text-white px-4 py-2 flex items-center justify-between">
                          <span className="font-medium">Response</span>
                          <div className="flex items-center gap-2 text-purple-100">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-sm">{match.agent2_response.response_time.toFixed(2)}s</span>
                          </div>
                        </div>
                        <div className="p-6">
                          <p className="whitespace-pre-wrap text-purple-900 leading-relaxed">
                            {match.agent2_response.response_text}
                          </p>
                        </div>
                        {match.agent2_response.score !== undefined && (
                          <div className="bg-purple-500/10 px-4 py-2 border-t border-purple-200">
                            <div className="flex items-center justify-center">
                              <span className="text-purple-700 text-sm font-medium">Score: </span>
                              <span className="text-purple-800 text-lg font-bold ml-1">
                                {match.agent2_response.score.toFixed(1)}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="bg-purple-50 border-2 border-dashed border-purple-200 rounded-xl p-8 text-center">
                        <svg className="w-8 h-8 text-purple-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <p className="text-purple-600">Waiting for response...</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 p-8 rounded-xl text-center">
                  <svg className="w-12 h-12 text-indigo-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-3.774-.9L3 21l1.9-6.226A8.955 8.955 0 013 12a8 8 0 018-8c4.418 0 8 3.582 8 8z" />
                  </svg>
                  <p className="text-indigo-700 font-medium">Waiting for agent responses...</p>
                  <p className="text-indigo-600 text-sm mt-1">Both agents are working on their solutions.</p>
                </div>
              )}

              {/* Show final scores for completed regular matches */}
              {match.status === MatchStatus.COMPLETED && match.final_scores && (
                <div className="mt-8 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 p-6 rounded-xl">
                  <h4 className="font-semibold text-emerald-800 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Final Scores
                  </h4>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
                        {match.final_scores[match.agent1_id]?.toFixed(1) || 'N/A'}
                      </div>
                      <p className="text-blue-800 font-medium">{agent1.profile.name}</p>
                    </div>
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-purple-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
                        {match.final_scores[match.agent2_id]?.toFixed(1) || 'N/A'}
                      </div>
                      <p className="text-purple-800 font-medium">{agent2.profile.name}</p>
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