'use client';

import { Division, Agent } from '@/types/arena';
import { fetchAgents } from '@/lib/api';
import { AgentCard } from '@/components/AgentCard';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const newAgents = await fetchAgents();
      setAgents(newAgents);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      setError('Failed to fetch models');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh agent data every 2 seconds
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);
  
  // Group agents by division and sort by ELO rating
  const agentsByDivision = Object.values(Division).reduce((acc, division) => {
    const divisionAgents = agents.filter(agent => agent.division === division);
    // Sort by ELO rating (highest first)
    divisionAgents.sort((a, b) => b.stats.elo_rating - a.stats.elo_rating);
    acc[division] = divisionAgents;
    return acc;
  }, {} as Record<Division, Agent[]>);

  if (isLoading) {
    return <div className="min-h-screen p-8">Loading models...</div>;
  }

  if (error) {
    return <div className="min-h-screen p-8 text-red-600">{error}</div>;
  }

  return (
    <main className="min-h-screen p-8">
      {/* Page Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-500 mb-4">👑 The Kingdom</h1>
        <p className="text-lg text-gray-300 max-w-3xl mx-auto">
          Models compete through divisions to reach the throne. 
          Click on any model to see their stats, or head to the <strong>Playground</strong> to start matches and watch debates.
        </p>
      </div>
      
      <div className="grid gap-8">
        {Object.values(Division).map((division) => {
          const divisionAgents = agentsByDivision[division] || [];
          
          return (
            <div key={division} className="p-6 bg-white rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900">
                {division === Division.KING && '👑 '}
                {division.toUpperCase()} DIVISION
                <span className="text-gray-600 text-lg ml-2 font-medium">
                  ({divisionAgents.length})
                </span>
              </h2>
              
              {divisionAgents.length > 0 ? (
                <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                  {divisionAgents.map((agent) => (
                    <AgentCard key={agent.profile.agent_id} agent={agent} />
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-gray-700 italic">No models in this division yet</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
