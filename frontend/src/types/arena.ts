import { Match } from './matches';

export enum Division {
  KING = 'king',
  MASTER = 'master',
  EXPERT = 'expert',
  NOVICE = 'novice'
}

export interface AgentProfile {
  agent_id: string;
  name: string;
  description: string;
  specializations: string[];
}

export interface AgentStats {
  elo_rating: number;
  total_matches: number;
  wins: number;
  losses: number;
  draws: number;
  current_streak: number;
  best_streak: number;
}

export interface DivisionChange {
  from_division: string;
  to_division: string;
  timestamp: string;
  reason: string;
  type: 'promotion' | 'demotion';
}

export interface Agent {
  profile: AgentProfile;
  division: Division;
  stats: AgentStats;
  match_history?: Match[];
  division_changes?: DivisionChange[];
} 