import { Agent, Division } from '@/types/arena';
import { Match, MatchStatus, ChallengeType } from '@/types/matches';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
export { API_BASE_URL };

export function transformMatch(rawMatch: any): Match {
  if (!rawMatch) return rawMatch;
  return {
    ...rawMatch,
    status: rawMatch.status?.toUpperCase() as MatchStatus,
    match_type: rawMatch.match_type?.toUpperCase() as 'REGULAR_DUEL' | 'DEBATE',
    challenge: {
      ...rawMatch.challenge,
      type: rawMatch.challenge.type?.toUpperCase() as ChallengeType,
    },
  };
}

function transformAgent(rawAgent: any): Agent {
  return {
    profile: {
      agent_id: rawAgent.profile.name,  // Use name as ID
      name: rawAgent.profile.name,
      description: rawAgent.profile.description || `Agent based on ${rawAgent.profile.name}`,
      specializations: rawAgent.profile.specializations || []
    },
    division: rawAgent.division as Division,
    stats: {
      total_matches: rawAgent.stats?.total_matches || 0,
      wins: rawAgent.stats?.wins || 0,
      losses: rawAgent.stats?.losses || 0,
      draws: rawAgent.stats?.draws || 0,
      elo_rating: rawAgent.stats?.elo_rating || 1000,
      current_streak: rawAgent.stats?.current_streak || 0,
      best_streak: rawAgent.stats?.best_streak || 0,
      win_rate: rawAgent.stats?.win_rate || 0,
      elo_history: rawAgent.stats?.elo_history || [],
      consistency_score: rawAgent.stats?.consistency_score || 0,
      innovation_index: rawAgent.stats?.innovation_index || 0,
      challenges_created: rawAgent.stats?.challenges_created || 0,
      challenge_quality_avg: rawAgent.stats?.challenge_quality_avg || 0,
      judge_accuracy: rawAgent.stats?.judge_accuracy || 0,
      judge_reliability: rawAgent.stats?.judge_reliability || 1.0
    },
    division_change_history: rawAgent.division_change_history || [],
    match_history: rawAgent.match_history || []
  };
}

export async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE_URL}/agents`);
  if (!response.ok) {
    throw new Error('Failed to fetch agents');
  }
  const data = await response.json();
  return data.map(transformAgent);
}

export async function fetchAgent(agentId: string): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/agents/${agentId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch agent');
  }
  const data = await response.json();
  return transformAgent(data);
}

export async function fetchMatches(): Promise<Match[]> {
  const response = await fetch(`${API_BASE_URL}/matches`);
  if (!response.ok) {
    throw new Error('Failed to fetch matches');
  }
  const data = await response.json();
  console.log('Raw matches data:', data);
  return data.map(transformMatch);
}

export async function fetchMatch(matchId: string): Promise<Match> {
  const response = await fetch(`${API_BASE_URL}/matches/${matchId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch match');
  }
  const data = await response.json();
  return transformMatch(data);
}

export async function fetchLiveMatches(): Promise<Match[]> {
  const response = await fetch(`${API_BASE_URL}/matches/live`);
  if (!response.ok) {
    throw new Error('Failed to fetch live matches');
  }
  const data = await response.json();
  console.log('Raw live matches data:', data);
  return data.map(transformMatch);
}

export async function startTournament(numRounds: number = 1): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/tournament/start?num_rounds=${numRounds}`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error('Failed to start tournament');
  }
}

export async function fetchTournamentStatus(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tournament/status`);
  if (!response.ok) {
    throw new Error('Failed to fetch tournament status');
  }
  return response.json();
}