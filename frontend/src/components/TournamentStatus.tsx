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
}

interface TournamentStatusProps {
  status: TournamentStatus;
  onStartTournament?: () => void;
  isLoading?: boolean;
}

export function TournamentStatus({ status, onStartTournament, isLoading }: TournamentStatusProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-start mb-6">
        <h2 className="text-2xl font-semibold">Tournament Status</h2>
        {onStartTournament && (
          <button
            onClick={onStartTournament}
            disabled={isLoading}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Running Tournament...' : 'Start New Round'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Total Agents</p>
          <p className="text-2xl font-bold">{status.total_agents}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Total Matches</p>
          <p className="text-2xl font-bold">{status.total_matches}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg col-span-2">
          <p className="text-gray-600 text-sm">Current King</p>
          <p className="text-2xl font-bold">
            {status.current_king ? `👑 ${status.current_king}` : 'No King Yet'}
          </p>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-3">Division Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(status.divisions).map(([division, count]) => (
            <div key={division} className="bg-gray-50 p-3 rounded-lg">
              <p className="text-gray-600 text-sm">{division}</p>
              <p className="text-xl font-bold">{count}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 