import { Agent } from './arena';

export enum MatchStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

export enum ChallengeType {
  LOGICAL_REASONING = 'LOGICAL_REASONING',
  DEBATE = 'DEBATE',
  CREATIVE_PROBLEM_SOLVING = 'CREATIVE_PROBLEM_SOLVING',
  MATHEMATICAL = 'MATHEMATICAL',
  ABSTRACT_THINKING = 'ABSTRACT_THINKING'
}

export interface Challenge {
  challenge_id: string;
  title: string;
  description: string;
  type: ChallengeType;
  difficulty: string;
}

export interface AgentResponse {
  agent_id: string;
  response_text: string;
  response_time: number;
  score?: number;
}

export interface Match {
  match_id: string;
  challenge: Challenge;
  agent1_id: string;
  agent2_id: string;
  status: MatchStatus;
  start_time: string;
  end_time?: string;
  winner_id?: string;
  agent1_response?: AgentResponse;
  agent2_response?: AgentResponse;
  transcript?: AgentResponse[];  // For debate matches
  judge_feedback?: string[];
  match_type: 'REGULAR_DUEL' | 'DEBATE';  // Add match type
} 