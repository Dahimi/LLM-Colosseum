'use client';

interface LiveActivityIndicatorProps {
  liveMatchCount: number;
  totalMatches: number;
}

export function LiveActivityIndicator({ liveMatchCount, totalMatches }: LiveActivityIndicatorProps) {
  if (liveMatchCount === 0 && totalMatches === 0) {
    return null;
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {liveMatchCount > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="font-medium text-gray-900">
                {liveMatchCount} Live Battle{liveMatchCount > 1 ? 's' : ''} in Progress
              </span>
            </div>
          )}
          
          {totalMatches > 0 && (
            <div className="text-gray-600">
              • {totalMatches} Recent Battles
            </div>
          )}
        </div>
        
        <button 
          onClick={() => {
            document.querySelector('#live-matches')?.scrollIntoView({ 
              behavior: 'smooth',
              block: 'start'
            });
          }}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors"
        >
          <span>Watch Now</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      </div>
    </div>
  );
} 