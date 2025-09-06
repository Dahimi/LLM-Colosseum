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
  source?: string;
  answer?: string;
  tags?: string[];
}

export interface AgentResponse {
  agent_id: string;
  response_text: string;
  response_time: number;
  timestamp?: string;
  score?: number;
  is_structured?: boolean;
  structured_data?: any;
  metadata?: any;
  is_streaming?: boolean;
}

export interface JudgeScore {
  criterion: string;
  score: number;
  reasoning: string;
  confidence: number;
}

export interface JudgeEvaluation {
  judge_id: string;
  overall_reasoning: string;
  agent1_total_score: number;
  agent2_total_score: number;
  recommended_winner: string | null;
  evaluation_quality: number;
  agent1_scores: JudgeScore[];
  agent2_scores: JudgeScore[];
}

export interface Match {
  match_id: string;
  challenge: Challenge;
  agent1_id: string;
  agent2_id: string;
  status: MatchStatus;
  start_time: string;
  end_time?: string;
  created_at: string;
  completed_at?: string;
  winner_id?: string;
  result?: 'WIN' | 'LOSS' | 'DRAW';  // Match result from agent1's perspective
  agent1_response?: AgentResponse;
  agent2_response?: AgentResponse;
  transcript?: AgentResponse[];  // For debate matches
  judge_feedback?: string[];
  evaluations?: JudgeEvaluation[];  // Legacy field
  evaluation_details?: JudgeEvaluation[];  // Detailed judge evaluations
  match_type: 'REGULAR_DUEL' | 'DEBATE' | 'KING_CHALLENGE';
  final_scores?: { [key: string]: number };
  division?: string;  // Division where the match takes place
} 