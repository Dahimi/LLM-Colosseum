import { Match, MatchStatus } from '@/types/matches';
import { Agent } from '@/types/arena';
import Link from 'next/link';

interface MatchCardProps {
  match: Match;
  agents: {
    [key: string]: Agent;
  };
}

export function MatchCard({ match, agents }: MatchCardProps) {
  const agent1 = agents[match.agent1_id];
  const agent2 = agents[match.agent2_id];
  
  // Debug logging
  // console.log('MatchCard rendering:', { match, agent1, agent2 });
  
  if (!agent1 || !agent2) {
    console.warn('Missing agent data:', { 
      match_id: match.match_id,
      agent1_id: match.agent1_id,
      agent2_id: match.agent2_id,
      available_agents: Object.keys(agents)
    });
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">Match data incomplete (missing agent information)</p>
        <p className="text-sm text-yellow-600">Match ID: {match.match_id}</p>
      </div>
    );
  }

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
    try {
      return new Date(dateString).toLocaleString();
    } catch (e) {
      console.warn('Invalid date:', dateString);
      return 'Invalid time';
    }
  };

  return (
    <Link 
      href={`/matches/${match.match_id}`}
      className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200"
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold text-lg mb-1 text-gray-900">{match.challenge.title}</h3>
            <div className="flex items-center gap-2">
              <p className="text-sm text-gray-900">{match.challenge.type}</p>
              {match.match_type === 'DEBATE' && (
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full">
                  Debate Match
                </span>
              )}
              {match.match_type === 'KING_CHALLENGE' && (
                <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full flex items-center">
                  👑 King Challenge
                </span>
              )}
            </div>
          </div>
          <span className={`px-2 py-1 rounded text-sm ${getStatusColor(match.status)}`}>
            {match.status}
          </span>
        </div>

        {/* Agents */}
        <div className="grid grid-cols-3 gap-2 items-center mb-4">
          <div className="text-center">
            <p className="font-medium text-gray-900">{agent1.profile.name}</p>
            <p className="text-sm text-gray-900">ELO: {Math.round(agent1.stats.elo_rating)}</p>
          </div>
          <div className="text-center text-2xl font-bold text-gray-500">
            VS
          </div>
          <div className="text-center">
            <p className="font-medium text-gray-900">{agent2.profile.name}</p>
            <p className="text-sm text-gray-900">ELO: {Math.round(agent2.stats.elo_rating)}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center text-sm text-gray-900">
          <p>Started: {formatTime(match.created_at)}</p>
          {match.completed_at && <p>Ended: {formatTime(match.completed_at)}</p>}
          {match.winner_id && agents[match.winner_id] && (
            <p className="font-medium text-green-800">
              Winner: {agents[match.winner_id].profile.name}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
} 