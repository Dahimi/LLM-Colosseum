interface TournamentStatus {
  total_agents: number;
  divisions: {
    KING: number;
    MASTER: number;
    EXPERT: number;
    NOVICE: number;
  };
  total_matches: number;
  current_king: string | null;
  king_stats?: {
    elo_rating: number;
    win_rate: number;
    total_matches: number;
    current_streak: number;
  } | null;
  eligible_challengers?: Array<{
    name: string;
    elo_rating: number;
    win_rate: number;
    current_streak: number;
  }>;
}

interface TournamentStatusProps {
  status: TournamentStatus;
  onStartTournament?: () => void;
  isLoading?: boolean;
}

export function TournamentStatus({ status, onStartTournament, isLoading }: TournamentStatusProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      <div className="flex justify-between items-start mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Tournament Status</h2>
        {onStartTournament && (
          <button
            onClick={onStartTournament}
            disabled={isLoading}
            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {isLoading ? 'Running Tournament...' : 'Start New Round'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-800 text-sm font-medium">Total Models</p>
          <p className="text-xl font-bold text-gray-900">{status.total_agents}</p>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-800 text-sm font-medium">Total Matches</p>
          <p className="text-xl font-bold text-gray-900">{status.total_matches}</p>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg col-span-2">
          <p className="text-gray-800 text-sm font-medium">Current King</p>
          <p className="text-xl font-bold text-gray-900">
            {status.current_king ? `👑 ${status.current_king}` : 'No King Yet'}
          </p>
        </div>
      </div>

      <div>
        <h3 className="text-base font-medium mb-2 text-gray-900">Division Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(status.divisions).map(([division, count]) => (
            <div key={division} className="bg-gray-50 p-2.5 rounded-lg">
              <p className="text-gray-800 text-sm font-medium">{division}</p>
              <p className="text-lg font-bold text-gray-900">{count}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 