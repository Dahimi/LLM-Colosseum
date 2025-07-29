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
      setError('Failed to fetch agents');
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
  
  // Group agents by division
  const agentsByDivision = Object.values(Division).reduce((acc, division) => {
    acc[division] = agents.filter(agent => agent.division === division);
    return acc;
  }, {} as Record<Division, Agent[]>);

  if (isLoading) {
    return <div className="min-h-screen p-8">Loading agents...</div>;
  }

  if (error) {
    return <div className="min-h-screen p-8 text-red-600">{error}</div>;
  }

  return (
    <main className="min-h-screen p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Agent Arena</h1>
        <Link 
          href="/matches" 
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          View Matches
        </Link>
      </div>
      
      <div className="grid gap-8">
        {Object.values(Division).map((division) => {
          const divisionAgents = agentsByDivision[division] || [];
          
          return (
            <div key={division} className="p-6 bg-white rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900">
                {division === Division.KING && '👑 '}
                {division} Division
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
                  <p className="text-gray-700 italic">No agents in this division yet</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
