"""LLM-based judge system for evaluating agent responses in the Intelligence Arena."""

from typing import List, Dict, Optional
from agent_arena.models.challenge import Challenge
from agent_arena.models.match import Match, AgentResponse
from agent_arena.models.evaluation import Evaluation, EvaluationCriteria, JudgeScore
from agent_arena.core.llm_interface import create_system_llm, create_structured_llm, create_judge_llm, EvaluationResponse
from agent_arena.models.match import MatchType


class LLMJudge:
    """An LLM-based judge that evaluates agent responses."""
    
    def __init__(self, judge_id: str = None, agents=None, agent_llms=None):
        """Initialize the LLM judge."""
        # Create judge LLM using best agents or fallback to system LLM
        llm, judge_name = create_judge_llm(agents, agent_llms)
        
        self.judge_id = judge_id or judge_name
        self.llm = llm
        self.structured_llm = create_structured_llm(self.llm, EvaluationResponse)
    
    def evaluate_match(self, match: Match, challenge: Challenge) -> Evaluation:
        """Evaluate a match between two agents."""
        
        # Create the evaluation prompt
        prompt = self._create_evaluation_prompt(match, challenge)
        
        # Get structured evaluation from LLM
        llm_response = self.structured_llm.invoke(prompt)
        
        # Create the Evaluation object
        evaluation = Evaluation(
            match_id=match.match_id,
            judge_id=self.judge_id,
            overall_reasoning=llm_response.overall_reasoning,
            recommended_winner=llm_response.recommended_winner,
            evaluation_quality=llm_response.confidence
        )
        
        # Convert LLM scores to JudgeScore objects
        for criterion_name, score in llm_response.agent1_scores.model_dump().items():
            try:
                criterion = EvaluationCriteria(criterion_name)
                judge_score = JudgeScore(
                    criterion=criterion,
                    score=score,
                    reasoning=f"Agent 1 {criterion_name}: {score}/10",
                    confidence=llm_response.confidence
                )
                evaluation.agent1_scores.append(judge_score)
            except ValueError:
                # Skip invalid criteria
                continue
        
        for criterion_name, score in llm_response.agent2_scores.model_dump().items():
            try:
                if not score:
                    continue
                criterion = EvaluationCriteria(criterion_name)
                judge_score = JudgeScore(
                    criterion=criterion,
                    score=score,
                    reasoning=f"Agent 2 {criterion_name}: {score}/10",
                    confidence=llm_response.confidence
                )
                evaluation.agent2_scores.append(judge_score)
            except ValueError:
                # Skip invalid criteria
                continue
        
        # Calculate total scores
        evaluation.calculate_total_scores()
        
        # Finalize evaluation
        evaluation.finalize_evaluation(
            llm_response.overall_reasoning,
            f"Detailed comparison and analysis of both responses"
        )
        
        return evaluation
    
    def _create_evaluation_prompt(self, match: Match, challenge: Challenge) -> str:
        """Create a detailed prompt for evaluating agent responses."""
        if match.match_type == MatchType.DEBATE:
            return self._create_debate_evaluation_prompt(match, challenge)

        agent1_response = match.agent1_response
        agent2_response = match.agent2_response
        
        if not agent1_response or not agent2_response:
            raise ValueError("Both agent responses must be available for evaluation")
        
        prompt = f"""You are an expert judge in an AI Intelligence Arena. Your job is to fairly and objectively evaluate two AI agents' responses to a challenge.

**CHALLENGE:**
Title: {challenge.title}
Type: {challenge.challenge_type.value.replace('_', ' ').title()}
Difficulty: {challenge.difficulty.name} (Level {challenge.difficulty.value}/5)

Description:
{challenge.description}

**EVALUATION CRITERIA:**
{chr(10).join(f"- {criterion}" for criterion in challenge.evaluation_criteria)}

**EXPECTED CONCEPTS:**
{chr(10).join(f"- {concept}" for concept in challenge.expected_concepts)}
"""

        # Include the answer if it exists
        if challenge.answer:
            prompt += f"""
**CORRECT ANSWER:**
{challenge.answer}
"""

        prompt += f"""
**AGENT 1 RESPONSE:**
{agent1_response.response_text}

**AGENT 2 RESPONSE:**
{agent2_response.response_text}

**EVALUATION INSTRUCTIONS:**
1. Evaluate both responses objectively and fairly
2. Score each response on these criteria (0-10 scale):
   - correctness: Factual accuracy and problem-solving correctness
   - completeness: How thoroughly the response addresses the challenge
   - logical_consistency: Internal logical coherence and reasoning quality
   - clarity: Communication effectiveness and organization
   - creativity: Originality and innovative thinking (where applicable)
   - depth: Sophistication and depth of analysis

3. Consider the specific challenge type and difficulty level
4. Provide your overall reasoning for the evaluation
5. Recommend a winner: 'agent1', 'agent2', or 'draw' (if very close)
6. Rate your confidence in this evaluation (0.0-1.0)

**EVALUATION GUIDELINES:**
- Be objective and consistent
- Consider both strengths and weaknesses
- Factor in the challenge's specific requirements
- A 'draw' is appropriate when responses are very close in quality
- Explain your reasoning clearly
- Scores should reflect the challenge difficulty level
"""

        if challenge.answer:
            prompt += """
- Compare responses against the provided correct answer
- Prioritize correctness when a definitive answer exists
"""

        prompt += """
Provide detailed scores and clear reasoning for your evaluation."""
        
        return prompt

    def _create_debate_evaluation_prompt(self, match: Match, challenge: Challenge) -> str:
        """Create a prompt for evaluating a debate match."""
        
        transcript_text = "\n".join(f"Agent {i%2 + 1} ({res.agent_id}): {res.response_text}" for i, res in enumerate(match.transcript))

        prompt = f"""You are an expert judge in an AI Intelligence Arena. Your job is to evaluate a debate between two AI agents.

**DEBATE TOPIC:**
Title: {challenge.title}
Description:
{challenge.description}
"""

        # Include the answer if it exists
        if challenge.answer:
            prompt += f"""
**REFERENCE INFORMATION:**
{challenge.answer}
"""

        prompt += f"""
**DEBATE TRANSCRIPT:**
{transcript_text}

**EVALUATION INSTRUCTIONS:**
1. Evaluate the entire debate based on the quality of arguments, rebuttals, and overall persuasiveness.
2. Score each agent on these criteria (0-10 scale):
   - logical_consistency: Coherence and logical soundness of arguments.
   - creativity: Originality and depth of thought.
   - clarity: How clearly and effectively each agent communicated their points.
   - depth: The level of detail and sophistication in the arguments.
   - completeness: How well they stayed on topic and addressed the core issues.
   - correctness: Factual accuracy of claims made.
3. Provide your overall reasoning for the evaluation, explaining who you thought won the debate and why.
4. Recommend a winner: 'agent1', 'agent2', or 'draw'.
5. Rate your confidence in this evaluation (0.0-1.0).
"""

        if challenge.answer:
            prompt += """
When evaluating factual claims, compare them against the reference information provided.
"""

        prompt += """
Provide detailed scores and clear reasoning for your evaluation."""
        return prompt


class JudgePanel:
    """A panel of multiple LLM judges for comprehensive evaluation."""
    
    def __init__(self, judge_count: int = 5, agents=None, agent_llms=None):
        """Initialize a panel of judges."""
        self.judges = []
        
        for i in range(judge_count):
            try:
                judge = LLMJudge(agents=agents, agent_llms=agent_llms)
                self.judges.append(judge)
            except Exception as e:
                print(f"   ⚠️  Failed to create judge {i+1}: {e}")
                # Fallback to system LLM judge
                fallback_judge_id = f"system_judge_{i+1}"
                fallback_judge = LLMJudge(judge_id=fallback_judge_id)
                self.judges.append(fallback_judge)
    
    def evaluate_match(self, match: Match, challenge: Challenge) -> List[Evaluation]:
        """Evaluate a match using all judges in the panel."""
        evaluations = []
        
        print(f"⚖️  Evaluating match with {len(self.judges)} LLM judges...")
        
        for i, judge in enumerate(self.judges):
            try:
                evaluation = judge.evaluate_match(match, challenge)
                evaluations.append(evaluation)
                print(f"   ✅ Judge {i+1}: {evaluation.recommended_winner} (confidence: {evaluation.evaluation_quality})")
            except Exception as e:
                print(f"   ❌ Judge {i+1} failed: {e}")
                continue
        
        return evaluations
    
    def get_consensus_result(self, evaluations: List[Evaluation]) -> Dict:
        """Calculate consensus results from multiple judge evaluations."""
        if not evaluations:
            return {"winner": None, "confidence": 0.0, "agent1_avg": 0.0, "agent2_avg": 0.0}
        
        # Calculate average scores
        agent1_scores = [eval.agent1_total_score for eval in evaluations]
        agent2_scores = [eval.agent2_total_score for eval in evaluations]
        
        avg_agent1 = sum(agent1_scores) / len(agent1_scores)
        avg_agent2 = sum(agent2_scores) / len(agent2_scores)
        
        # Determine consensus winner
        score_diff = abs(avg_agent1 - avg_agent2)
        if score_diff < 0.5:
            winner = None  # Draw
        elif avg_agent1 > avg_agent2:
            winner = "agent1"
        else:
            winner = "agent2"
        
        # Calculate consensus confidence (agreement between judges)
        recommendations = [eval.recommended_winner for eval in evaluations]
        winner_votes = recommendations.count(winner) if winner else 0
        draw_votes = recommendations.count(None)
        
        if winner:
            consensus_confidence = winner_votes / len(recommendations)
        else:
            consensus_confidence = draw_votes / len(recommendations)
        
        return {
            "winner": winner,
            "confidence": consensus_confidence,
            "agent1_avg": avg_agent1,
            "agent2_avg": avg_agent2,
            "score_difference": score_diff,
            "evaluations": evaluations
        }


def evaluate_match_with_llm_judges(
    match: Match, 
    challenge: Challenge, 
    judge_count: int = 3,
    agents=None,
    agent_llms=None
) -> Dict:
    """Convenience function to evaluate a match with LLM judges."""
    
    judge_panel = JudgePanel(judge_count, agents=agents, agent_llms=agent_llms)
    evaluations = judge_panel.evaluate_match(match, challenge)
    consensus = judge_panel.get_consensus_result(evaluations)
    
    # Convert evaluations to serializable format
    evaluation_details = []
    for eval in evaluations:
        # Extract key information from each evaluation
        eval_detail = {
            "judge_id": eval.judge_id,
            "recommended_winner": eval.recommended_winner,
            "overall_reasoning": eval.overall_reasoning,
            "agent1_total_score": eval.agent1_total_score,
            "agent2_total_score": eval.agent2_total_score,
            "evaluation_quality": eval.evaluation_quality,
            "agent1_scores": [],
            "agent2_scores": []
        }
        
        # Add detailed scores for each criterion
        for score in eval.agent1_scores:
            eval_detail["agent1_scores"].append({
                "criterion": score.criterion.value,
                "score": score.score,
                "reasoning": score.reasoning,
                "confidence": score.confidence
            })
            
        for score in eval.agent2_scores:
            eval_detail["agent2_scores"].append({
                "criterion": score.criterion.value,
                "score": score.score,
                "reasoning": score.reasoning,
                "confidence": score.confidence
            })
            
        evaluation_details.append(eval_detail)
    
    consensus["evaluation_details"] = evaluation_details
    return consensus


# Example usage and testing
def test_judge_system():
    """Test the LLM judge system."""
    from agent_arena.models.match import Match, MatchType, AgentResponse
    from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
    
    print("🧪 Testing LLM Judge System...")
    
    # Create a mock challenge
    challenge = Challenge(
        title="Logic Puzzle Test",
        description="Solve this logic puzzle: If all A are B, and some B are C, what can we conclude about A and C?",
        challenge_type=ChallengeType.LOGICAL_REASONING,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        evaluation_criteria=["Logical correctness", "Clear reasoning", "Complete analysis"],
        expected_concepts=["logical deduction", "set theory", "inference rules"]
    )
    
    # Create mock responses
    response1 = AgentResponse(
        agent_id="agent1",
        response_text="Based on the given premises, we cannot definitively conclude anything about the relationship between A and C. While all A are B, and some B are C, this doesn't guarantee that any A are C.",
        response_time=2.5
    )
    
    response2 = AgentResponse(
        agent_id="agent2", 
        response_text="Since all A are B, and some B are C, we can conclude that some A might be C, but we cannot be certain.",
        response_time=3.0
    )
    
    # Create mock match
    match = Match(
        match_type=MatchType.REGULAR_DUEL,
        challenge_id=challenge.challenge_id,
        agent1_id="agent1",
        agent2_id="agent2",
        division="expert"
    )
    
    match.agent1_response = response1
    match.agent2_response = response2
    
    # Test evaluation
    try:
        result = evaluate_match_with_llm_judges(match, challenge, judge_count=2)
        print(f"✅ Evaluation completed!")
        print(f"   Winner: {result['winner']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Agent 1 avg score: {result['agent1_avg']:.1f}")
        print(f"   Agent 2 avg score: {result['agent2_avg']:.1f}")
        
        return result
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None


if __name__ == "__main__":
    test_judge_system() 