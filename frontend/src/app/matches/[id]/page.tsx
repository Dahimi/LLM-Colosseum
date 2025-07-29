import { fetchMatch, fetchAgent } from '@/lib/api';
import { MatchStatus } from '@/types/matches';
import Link from 'next/link';
import { notFound } from 'next/navigation';

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function MatchPage({ params }: PageProps) {
  const { id } = await params;
  
  try {
    const match = await fetchMatch(id);
    const [agent1, agent2] = await Promise.all([
      fetchAgent(match.agent1_id),
      fetchAgent(match.agent2_id),
    ]);

    const getStatusColor = (status: MatchStatus) => {
      switch (status) {
        case MatchStatus.IN_PROGRESS:
          return 'bg-yellow-100 text-yellow-800';
        case MatchStatus.COMPLETED:
          return 'bg-green-100 text-green-800';
        case MatchStatus.CANCELLED:
          return 'bg-red-100 text-red-800';
        default:
          return 'bg-gray-100 text-gray-800';
      }
    };

    const formatTime = (dateString: string) => {
      return new Date(dateString).toLocaleString();
    };

    return (
      <main className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          {/* Navigation */}
          <Link 
            href="/matches" 
            className="text-blue-600 hover:text-blue-800 mb-6 inline-flex items-center"
          >
            ← Back to Matches
          </Link>

          {/* Match Header */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{match.challenge.title}</h1>
                <p className="text-gray-700">{match.challenge.description}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(match.status)}`}>
                {match.status}
              </span>
            </div>

            {/* Challenge Info */}
            <div className="grid grid-cols-2 gap-4 text-sm mb-6">
              <div>
                <p className="text-gray-700 font-medium">Challenge Type</p>
                <p className="text-gray-900">{match.challenge.type}</p>
              </div>
              <div>
                <p className="text-gray-700 font-medium">Difficulty</p>
                <p className="text-gray-900">{match.challenge.difficulty}</p>
              </div>
            </div>

            {/* Agents */}
            <div className="grid grid-cols-3 gap-4 items-center mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="font-semibold text-lg text-gray-900 mb-1">{agent1.profile.name}</p>
                <p className="text-sm text-gray-700">ELO: {Math.round(agent1.stats.elo_rating)}</p>
                {match.winner_id === agent1.profile.agent_id && (
                  <span className="inline-block mt-2 px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">
                    Winner 🏆
                  </span>
                )}
              </div>
              <div className="text-center text-3xl font-bold text-gray-500">
                VS
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="font-semibold text-lg text-gray-900 mb-1">{agent2.profile.name}</p>
                <p className="text-sm text-gray-700">ELO: {Math.round(agent2.stats.elo_rating)}</p>
                {match.winner_id === agent2.profile.agent_id && (
                  <span className="inline-block mt-2 px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">
                    Winner 🏆
                  </span>
                )}
              </div>
            </div>

            {/* Match Timeline */}
            <div className="text-sm text-gray-700">
              <p>Started: {formatTime(match.start_time)}</p>
              {match.end_time && <p>Ended: {formatTime(match.end_time)}</p>}
            </div>
          </div>

          {/* Responses */}
          {match.match_type === 'DEBATE' ? (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Debate Transcript
                {match.status === 'IN_PROGRESS' && (
                  <span className="ml-2 text-sm text-yellow-600 font-normal">
                    (Debate in progress...)
                  </span>
                )}
              </h2>
              {match.transcript && match.transcript.length > 0 ? (
                <div className="space-y-6">
                  {match.transcript.map((response, index) => {
                    const isAgent1 = response.agent_id === agent1.profile.name;
                    const agent = isAgent1 ? agent1 : agent2;
                    return (
                      <div 
                        key={index}
                        className={`flex ${isAgent1 ? 'justify-start' : 'justify-end'}`}
                      >
                        <div className={`max-w-[80%] ${isAgent1 ? 'bg-blue-50' : 'bg-green-50'} p-4 rounded-lg`}>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-gray-900">{agent.profile.name}</span>
                            <span className="text-sm text-gray-600">
                              {index === 0 ? '(Opening Statement)' : `(Turn ${index})`}
                            </span>
                          </div>
                          <p className="whitespace-pre-wrap text-gray-800">{response.response_text}</p>
                          <p className="text-sm text-gray-600 mt-2">
                            Response time: {response.response_time.toFixed(2)}s
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : match.status === 'COMPLETED' ? (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700">
                    This debate has concluded. Final scores:
                  </p>
                  <div className="mt-2 space-y-1">
                    <p className="text-gray-800">
                      {agent1.profile.name}: {match.final_scores?.[agent1.profile.name] || 0}
                    </p>
                    <p className="text-gray-800">
                      {agent2.profile.name}: {match.final_scores?.[agent2.profile.name] || 0}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700">Waiting for agents to begin the debate...</p>
                </div>
              )}
            </div>
          ) : (match.agent1_response || match.agent2_response) && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Agent Responses</h2>
              
              {match.agent1_response && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-2">{agent1.profile.name}'s Response</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-gray-800">{match.agent1_response.response_text}</p>
                    <p className="text-sm text-gray-700 mt-2">
                      Response time: {match.agent1_response.response_time.toFixed(2)}s
                      {match.agent1_response.score !== undefined && (
                        <span className="ml-4">Score: {match.agent1_response.score.toFixed(1)}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}
              
              {match.agent2_response && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">{agent2.profile.name}'s Response</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-gray-800">{match.agent2_response.response_text}</p>
                    <p className="text-sm text-gray-700 mt-2">
                      Response time: {match.agent2_response.response_time.toFixed(2)}s
                      {match.agent2_response.score !== undefined && (
                        <span className="ml-4">Score: {match.agent2_response.score.toFixed(1)}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Judge Feedback */}
          {match.judge_feedback && match.judge_feedback.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Judge Feedback</h2>
              <div className="space-y-4">
                {match.judge_feedback.map((feedback, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-800 mb-2">Judge {index + 1}</p>
                    <p className="whitespace-pre-wrap text-gray-800">{feedback}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    );
  } catch (error) {
    notFound();
  }
} 