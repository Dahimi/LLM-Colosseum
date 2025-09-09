'use client';

interface ColosseumStatsProps {
  status: {
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
  };
}

export function ColosseumStats({ status }: ColosseumStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
      {/* Total Models */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
        <div className="text-2xl font-bold text-gray-900">{status.total_agents}</div>
        <div className="text-sm text-gray-600 font-medium">Total Models</div>
      </div>

      {/* Total Matches */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
        <div className="text-2xl font-bold text-gray-900">{status.total_matches}</div>
        <div className="text-sm text-gray-600 font-medium">Battles Fought</div>
      </div>

      {/* Current King - Only accent color */}
      <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-lg shadow-sm border border-amber-200 p-4 text-center col-span-2">
        <div className="text-lg font-bold text-amber-800 flex items-center justify-center gap-1">
          👑 {status.current_king || 'No King Yet'}
        </div>
        <div className="text-sm text-amber-700 font-medium">Reigning Champion</div>
        {status.king_stats && (
          <div className="text-xs text-amber-600 mt-1">
            {Math.round(status.king_stats.elo_rating)} ELO • {status.king_stats.win_rate.toFixed(1)}% WR
          </div>
        )}
      </div>

      {/* Division Distribution - Simplified to grays */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 col-span-2">
        <div className="text-sm text-gray-700 font-medium mb-3 text-center">Kingdom Hierarchy</div>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div>
            <div className="text-lg font-bold text-amber-600">{status.divisions.KING}</div>
            <div className="text-xs text-gray-600 font-medium">King</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-800">{status.divisions.MASTER}</div>
            <div className="text-xs text-gray-600 font-medium">Master</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-700">{status.divisions.EXPERT}</div>
            <div className="text-xs text-gray-600 font-medium">Expert</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-600">{status.divisions.NOVICE}</div>
            <div className="text-xs text-gray-600 font-medium">Novice</div>
          </div>
        </div>
      </div>
    </div>
  );
} 