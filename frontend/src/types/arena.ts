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

export interface DivisionStats {
  matches: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  current_streak: number;
  best_streak: number;
}

export interface CareerStats {
  total_matches: number;
  total_wins: number;
  total_losses: number;
  total_draws: number;
  career_win_rate: number;
  divisions_reached: string[];
  promotions: number;
  demotions: number;
}

export interface AgentStats {
  // Global ELO rating
  elo_rating: number;
  
  // Current division performance (primary for UI)
  current_division_stats?: DivisionStats;
  
  // Career totals (secondary for achievements)
  career_stats?: CareerStats;
  
  // Legacy properties for backward compatibility
  total_matches: number;
  wins: number;
  losses: number;
  draws: number;
  current_streak: number;
  best_streak: number;
  win_rate: number;
  
  // Other stats
  consistency_score?: number;
  innovation_index?: number;
  challenges_created?: number;
  challenge_quality_avg?: number;
  judge_accuracy?: number;
  judge_reliability?: number;
  elo_history: EloHistoryEntry[];
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