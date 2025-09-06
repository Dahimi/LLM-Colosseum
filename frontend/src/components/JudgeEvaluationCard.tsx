import { JudgeEvaluation } from '@/types/matches';
import { Agent } from '@/types/arena';
import { MarkdownRenderer } from './MarkdownRenderer';

interface JudgeEvaluationCardProps {
  evaluation: JudgeEvaluation;
  agent1: Agent;
  agent2: Agent;
}

export function JudgeEvaluationCard({ evaluation, agent1, agent2 }: JudgeEvaluationCardProps) {
  return (
    <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl overflow-hidden">
      {/* Judge Header */}
      <div className="bg-amber-500 text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span className="font-medium">Judge {evaluation.judge_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm">Confidence: {(evaluation.evaluation_quality * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      {/* Overall Reasoning */}
      <div className="p-4 border-b border-amber-200">
        <h4 className="font-medium text-amber-800 mb-2">Overall Analysis</h4>
        <MarkdownRenderer content={evaluation.overall_reasoning} className="text-amber-900" />
      </div>
      
      {/* Scores Summary */}
      <div className="p-4 grid grid-cols-2 gap-4 bg-amber-100/30">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
            {evaluation.agent1_total_score.toFixed(1)}
          </div>
          <p className="text-blue-800 font-medium">{agent1.profile.name}</p>
          <p className="text-blue-600 text-sm">
            {evaluation.recommended_winner === 'agent1' ? '(Winner)' : ''}
          </p>
        </div>
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-purple-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-2">
            {evaluation.agent2_total_score.toFixed(1)}
          </div>
          <p className="text-purple-800 font-medium">{agent2.profile.name}</p>
          <p className="text-purple-600 text-sm">
            {evaluation.recommended_winner === 'agent2' ? '(Winner)' : ''}
          </p>
        </div>
      </div>
    </div>
  );
} 