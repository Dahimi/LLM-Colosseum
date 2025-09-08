'use client';

import { use } from 'react';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { fetchAgent } from '@/lib/api';
import { Agent } from '@/types/arena';
import { MatchCard } from '@/components/MatchCard';
import { EloHistoryEntry } from '@/types/arena';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function AgentPage({ params }: PageProps) {
  const { id } = use(params);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgent = async () => {
      try {
        const data = await fetchAgent(id);
        setAgent(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load model data');
      }
    };
    loadAgent();
  }, [id]);

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  if (!agent) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center p-8 max-w-md">
          <div className="inline-block relative w-16 h-16 mb-4">
            <div className="absolute top-0 w-6 h-6 bg-indigo-500 rounded-full animate-ping opacity-75"></div>
            <div className="relative w-6 h-6 bg-indigo-600 rounded-full"></div>
          </div>
          <h2 className="text-xl font-medium text-gray-700">Loading model details...</h2>
          <p className="text-gray-500 mt-2">Retrieving the latest information</p>
        </div>
      </div>
    );
  }

  // Initialize elo_history if it doesn't exist
  const elo_history = agent.stats.elo_history || [];
  const hasEloHistory = elo_history.length > 0;

  // Prepare ELO history data for the chart
  const eloData = hasEloHistory ? {
    labels: elo_history.map((entry: EloHistoryEntry) => 
      new Date(entry.timestamp).toLocaleDateString()
    ),
    datasets: [
      {
        label: 'ELO Rating',
        data: elo_history.map((entry: EloHistoryEntry) => entry.rating),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      }
    ]
  } : {
    labels: [],
    datasets: [{
      label: 'ELO Rating',
      data: [],
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1,
    }]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'ELO Rating History'
      }
    },
    scales: {
      y: hasEloHistory ? {
        min: Math.min(...elo_history.map((e: EloHistoryEntry) => e.rating)) - 50,
        max: Math.max(...elo_history.map((e: EloHistoryEntry) => e.rating)) + 50,
      } : {
        min: agent.stats.elo_rating - 50,
        max: agent.stats.elo_rating + 50,
      }
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Agent Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{agent.profile.name}</h1>
              <p className="text-lg text-gray-700 mt-2">{agent.profile.description}</p>
              <div className="mt-4 flex gap-2">
                {agent.profile.specializations.map((spec, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {spec}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-gray-500">Division</div>
              <div className="text-2xl font-bold text-indigo-600 capitalize">{agent.division}</div>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">Current ELO</div>
                <div className="text-2xl font-bold text-gray-900">{Math.round(agent.stats.elo_rating)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Win Rate</div>
                <div className="text-2xl font-bold text-gray-900">{agent.stats.win_rate.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Current Streak</div>
                <div className={`text-2xl font-bold ${
                  agent.stats.current_streak > 0 ? 'text-green-600' :
                  agent.stats.current_streak < 0 ? 'text-red-600' :
                  'text-gray-900'
                }`}>
                  {agent.stats.current_streak > 0 ? `+${agent.stats.current_streak}` : agent.stats.current_streak}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Match History</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">Total Matches</div>
                <div className="text-2xl font-bold text-gray-900">{agent.stats.total_matches}</div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Wins</div>
                  <div className="text-xl font-bold text-green-600">{agent.stats.wins}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Losses</div>
                  <div className="text-xl font-bold text-red-600">{agent.stats.losses}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Draws</div>
                  <div className="text-xl font-bold text-gray-600">{agent.stats.draws}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Achievements</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">Best Streak</div>
                <div className="text-2xl font-bold text-green-600">+{agent.stats.best_streak}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Division Changes</div>
                <div className="text-2xl font-bold text-indigo-600">{agent.division_change_history.length}</div>
              </div>
            </div>
          </div>
        </div>

        {/* ELO History Chart */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">ELO Rating History</h3>
          {hasEloHistory ? (
            <div className="h-[400px]">
              <Line data={eloData} options={chartOptions} />
            </div>
          ) : (
            <div className="h-[400px] flex items-center justify-center text-gray-500">
              No ELO history available yet
            </div>
          )}
        </div>

        {/* Recent Matches */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Matches</h3>
          {hasEloHistory ? (
            <div className="space-y-4">
              {elo_history.slice(-5).reverse().map((entry: EloHistoryEntry, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium text-gray-900">vs {entry.opponent_id}</div>
                      <div className="text-sm text-gray-500">
                        {new Date(entry.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${
                        entry.result === 'win' ? 'text-green-600' :
                        entry.result === 'loss' ? 'text-red-600' :
                        'text-gray-600'
                      }`}>
                        {entry.result.toUpperCase()}
                      </div>
                      <div className={`text-sm ${
                        entry.rating_change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {entry.rating_change >= 0 ? '+' : ''}{entry.rating_change.toFixed(1)} ELO
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              No matches played yet
            </div>
          )}
        </div>
      </div>
    </main>
  );
} 