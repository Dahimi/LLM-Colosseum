'use client';

import { useState, useEffect } from 'react';
import { Division, Agent } from '@/types/arena';
import { fetchAgents, startQuickMatch } from '@/lib/api';

interface QuickMatchControlsProps {
  onMatchStart?: () => void;
}

export function QuickMatchControls({ onMatchStart }: QuickMatchControlsProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchLimitInfo, setMatchLimitInfo] = useState<{
    current: number;
    max: number;
  } | null>(null);
  const [selectedDivision, setSelectedDivision] = useState<string>(Division.NOVICE);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [matchType, setMatchType] = useState<'random' | 'manual'>('random');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent1, setSelectedAgent1] = useState<string>('');
  const [selectedAgent2, setSelectedAgent2] = useState<string>('');

  // Load agents when component mounts or division changes
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const allAgents = await fetchAgents();
        setAgents(allAgents);
      } catch (e) {
        console.error('Failed to load agents:', e);
      }
    };
    loadAgents();
  }, []);

  // Reset agent selections when division or match type changes
  useEffect(() => {
    setSelectedAgent1('');
    setSelectedAgent2('');
  }, [selectedDivision, matchType]);

  // Get agents in the selected division
  const divisionAgents = agents.filter(agent => 
    agent.division.toLowerCase() === selectedDivision.toLowerCase() && 
    agent.profile.name // Ensure agent has a name
  );

  const handleStartMatch = async () => {
    try {
      setIsStarting(true);
      setError(null);
      setMatchLimitInfo(null);
      
      // Validate manual selection
      if (matchType === 'manual') {
        if (!selectedAgent1 || !selectedAgent2) {
          throw new Error('Please select both models for the battle');
        }
        if (selectedAgent1 === selectedAgent2) {
          throw new Error('Please select two different models');
        }
      }
      
      // Use the new API function
      const match = await startQuickMatch(
        selectedDivision,
        matchType === 'manual' ? selectedAgent1 : undefined,
        matchType === 'manual' ? selectedAgent2 : undefined
      );
      
      // Match started successfully, trigger refresh of matches list
      onMatchStart?.();
      
      // Show success message
      const agents = [match.agent1_id, match.agent2_id];
      setSuccessMessage(`Battle started between ${agents.join(' and ')}!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (e) {
      console.error('Error starting match:', e);
      if (e instanceof Error && e.message.includes('429')) {
        // Parse match limit info from error if available
        setMatchLimitInfo({ current: 20, max: 20 }); // Fallback values
      }
      setError(e instanceof Error ? e.message : 'Failed to start match');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
          ⚔️
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Quick Battle</h3>
          <p className="text-xs text-gray-600">
            {matchType === 'random' ? 'Random models face off' : 'Choose specific models'}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {/* Division Selection */}
        <div>
          <label htmlFor="division" className="block text-sm font-medium text-gray-700 mb-1">
            Choose Division
          </label>
          <select
            id="division"
            value={selectedDivision}
            onChange={(e) => setSelectedDivision(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 text-sm py-2"
            disabled={isStarting}
          >
            {Object.values(Division).filter(division => division !== Division.KING).map((division) => (
              <option key={division} value={division}>
                {division === Division.NOVICE && '👶 '}
                {division === Division.EXPERT && '🎓 '}
                {division === Division.MASTER && '🥇 '}
                {division.charAt(0).toUpperCase() + division.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Match Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Battle Type</label>
          <div className="flex gap-2">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="matchType"
                value="random"
                checked={matchType === 'random'}
                onChange={(e) => setMatchType(e.target.value as 'random' | 'manual')}
                className="mr-2 text-blue-600 focus:ring-blue-500"
                disabled={isStarting}
              />
              <span className="text-sm text-gray-700">🎲 Random Matchup</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="matchType"
                value="manual"
                checked={matchType === 'manual'}
                onChange={(e) => setMatchType(e.target.value as 'random' | 'manual')}
                className="mr-2 text-blue-600 focus:ring-blue-500"
                disabled={isStarting}
              />
              <span className="text-sm text-gray-700">🎯 Choose Models</span>
            </label>
          </div>
        </div>

        {/* Manual Agent Selection */}
        {matchType === 'manual' && (
          <div className="grid grid-cols-2 gap-3 p-3 bg-gray-50 rounded-md">
            <div>
              <label htmlFor="agent1" className="block text-sm font-medium text-gray-700 mb-1">
                Model 1
              </label>
              <select
                id="agent1"
                value={selectedAgent1}
                onChange={(e) => setSelectedAgent1(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 text-sm py-2"
                disabled={isStarting}
              >
                <option value="">Select model...</option>
                {divisionAgents.map((agent) => (
                  <option key={agent.profile.agent_id} value={agent.profile.name}>
                    {agent.profile.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="agent2" className="block text-sm font-medium text-gray-700 mb-1">
                Model 2
              </label>
              <select
                id="agent2"
                value={selectedAgent2}
                onChange={(e) => setSelectedAgent2(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 text-sm py-2"
                disabled={isStarting}
              >
                <option value="">Select model...</option>
                {divisionAgents.filter(agent => agent.profile.name !== selectedAgent1).map((agent) => (
                  <option key={agent.profile.agent_id} value={agent.profile.name}>
                    {agent.profile.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Start Button */}
        <div className="flex justify-end">
          <button
            onClick={handleStartMatch}
            disabled={isStarting || !!matchLimitInfo || (matchType === 'manual' && (!selectedAgent1 || !selectedAgent2 || selectedAgent1 === selectedAgent2))}
            className="bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors disabled:cursor-not-allowed text-sm font-medium flex items-center gap-2"
          >
            {isStarting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Starting...
              </>
            ) : (
              <>⚔️ Start Battle</>
            )}
          </button>
        </div>
        
        {/* Match limit warning */}
          {matchLimitInfo && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
            <div className="flex items-center">
              <div className="text-amber-600 mr-2">⚠️</div>
              <div>
                <p className="text-sm font-medium text-amber-800">Arena Full</p>
                <p className="text-xs text-amber-700">Maximum concurrent battles reached. Please wait for a battle to finish.</p>
                </div>
              </div>
            </div>
          )}
          
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          
          {successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <p className="text-sm text-green-600">{successMessage}</p>
            </div>
          )}
      </div>
    </div>
  );
} 