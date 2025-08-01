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

export interface EloHistoryEntry {
  timestamp: string;
  rating: number;
  match_id: string;
  opponent_id: string;
  opponent_rating: number;
  result: 'win' | 'loss' | 'draw';
  rating_change: number;
}

export interface AgentStats {
  elo_rating: number;
  total_matches: number;
  wins: number;
  losses: number;
  draws: number;
  current_streak: number;
  best_streak: number;
  consistency_score?: number;
  innovation_index?: number;
  challenges_created?: number;
  challenge_quality_avg?: number;
  judge_accuracy?: number;
  judge_reliability?: number;
  elo_history: EloHistoryEntry[];
  win_rate: number;
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
  division_change_history: DivisionChange[];
} 