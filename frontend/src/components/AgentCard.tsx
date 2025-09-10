import { Agent } from '@/types/arena';
import Link from 'next/link';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const { profile, stats } = agent;
  
  // Use current division stats for primary display
  const currentDivisionStats = stats.current_division_stats;
  const careerStats = stats.career_stats;
  
  // Get values with proper fallbacks
  const matches = currentDivisionStats?.matches || stats.total_matches;
  const wins = currentDivisionStats?.wins || stats.wins;
  const losses = currentDivisionStats?.losses || stats.losses;
  const draws = currentDivisionStats?.draws || stats.draws;
  const currentStreak = currentDivisionStats?.current_streak || stats.current_streak;
  const totalCareerMatches = careerStats?.total_matches || stats.total_matches;
  
  // Calculate win rate from current division
  const winRate = matches > 0
    ? ((wins / matches) * 100).toFixed(1)
    : '0.0';

  // Determine streak display from current division
  const streakDisplay = currentStreak > 0 
    ? `🔥 ${currentStreak}W`
    : currentStreak < 0 
      ? `❄️ ${Math.abs(currentStreak)}L`
      : '';

  // Show division experience
  const divisionMatches = matches;

  return (
    <Link 
      href={`/agents/${profile.agent_id}`}
      className="block border border-gray-200 rounded-lg p-4 hover:shadow-lg hover:border-blue-300 transition-all duration-200 bg-white cursor-pointer group"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition-colors">
          {profile.name}
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-sm bg-gray-100 group-hover:bg-blue-100 px-2 py-1 rounded text-gray-800 group-hover:text-blue-800 transition-colors">
          ELO: {Math.round(stats.elo_rating)}
        </span>
          <div className="text-gray-400 group-hover:text-blue-500 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-3 group-hover:text-gray-700 transition-colors">
        {profile.description}
      </p>
      
      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div className="p-2 bg-gray-50 rounded group-hover:bg-blue-50 transition-colors">
          <p className="text-gray-600 font-medium text-xs">Division Record</p>
          <p className="text-gray-900 font-semibold">{wins}W - {losses}L - {draws}D</p>
        </div>
        <div className="p-2 bg-gray-50 rounded group-hover:bg-blue-50 transition-colors">
          <p className="text-gray-600 font-medium text-xs">Division Win Rate</p>
          <p className="text-gray-900 font-semibold">{winRate}% {streakDisplay}</p>
        </div>
      </div>
      
      {divisionMatches > 0 && (
        <div className="text-xs text-gray-500 mb-2 text-center">
          {divisionMatches} matches in {agent.division.charAt(0).toUpperCase() + agent.division.slice(1)} division
          {totalCareerMatches > divisionMatches && (
            <span className="ml-1">• {totalCareerMatches} career total</span>
          )}
        </div>
      )}
      
      {profile.specializations.length > 0 && (
        <div className="mb-2">
          <p className="text-xs text-gray-600 font-medium mb-1">Specializations</p>
          <div className="flex flex-wrap gap-1">
            {profile.specializations.map((spec) => (
              <span 
                key={spec}
                className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-medium group-hover:bg-blue-200 transition-colors"
              >
                {spec}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Click hint */}
      <div className="text-center pt-2 border-t border-gray-100">
        <p className="text-xs text-gray-400 group-hover:text-blue-500 transition-colors">
          Click to view details →
        </p>
      </div>
    </Link>
  );
} 