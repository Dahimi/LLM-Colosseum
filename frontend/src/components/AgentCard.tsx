import { Agent } from '@/types/arena';
import Link from 'next/link';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const { profile, stats } = agent;
  
  // Calculate win rate
  const winRate = stats.total_matches > 0
    ? ((stats.wins / stats.total_matches) * 100).toFixed(1)
    : '0.0';

  // Determine streak display
  const streakDisplay = stats.current_streak > 0 
    ? `🔥 ${stats.current_streak}W`
    : stats.current_streak < 0 
      ? `❄️ ${Math.abs(stats.current_streak)}L`
      : '';

  return (
    <Link 
      href={`/agents/${profile.agent_id}`}
      className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg text-gray-900">{profile.name}</h3>
        <span className="text-sm bg-gray-100 px-2 py-1 rounded text-gray-800">
          ELO: {Math.round(stats.elo_rating)}
        </span>
      </div>
      
      <p className="text-sm text-gray-700 mb-3">{profile.description}</p>
      
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-gray-700 font-medium">Record</p>
          <p className="text-gray-900">{stats.wins}W - {stats.losses}L - {stats.draws}D</p>
        </div>
        <div>
          <p className="text-gray-700 font-medium">Win Rate</p>
          <p className="text-gray-900">{winRate}% {streakDisplay}</p>
        </div>
      </div>
      
      {profile.specializations.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-700 font-medium mb-1">Specializations</p>
          <div className="flex flex-wrap gap-1">
            {profile.specializations.map((spec) => (
              <span 
                key={spec}
                className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-medium"
              >
                {spec}
              </span>
            ))}
          </div>
        </div>
      )}
    </Link>
  );
} 