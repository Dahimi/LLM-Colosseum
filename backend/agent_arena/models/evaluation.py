"""Evaluation data models for the Intelligence Arena System."""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class EvaluationCriteria(Enum):
    """Criteria for evaluating agent responses."""

    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    LOGICAL_CONSISTENCY = "logical_consistency"
    CREATIVITY = "creativity"
    CLARITY = "clarity"
    DEPTH = "depth"
    ORIGINALITY = "originality"
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    RELEVANCE = "relevance"


class JudgeScore(BaseModel):
    """A judge's score for a specific criterion."""

    criterion: EvaluationCriteria = Field(description="The evaluation criterion")
    score: float = Field(ge=0.0, le=10.0, description="Score from 0-10")
    reasoning: str = Field(description="Explanation for the score")
    confidence: float = Field(
        ge=0.0, le=1.0, default=1.0, description="Judge's confidence in this score"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JudgeScore":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)


class Evaluation(BaseModel):
    """A judge's evaluation of agent responses in a match."""

    evaluation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique evaluation identifier",
    )
    match_id: str = Field(description="ID of the match being evaluated")
    judge_id: str = Field(description="ID of the judging agent")

    # Timing
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Evaluation creation timestamp"
    )
    submitted_at: Optional[datetime] = Field(
        default=None, description="Evaluation submission timestamp"
    )

    # Scores for each agent
    agent1_scores: List[JudgeScore] = Field(
        default_factory=list, description="Scores for agent 1"
    )
    agent2_scores: List[JudgeScore] = Field(
        default_factory=list, description="Scores for agent 2"
    )

    # Overall assessment
    agent1_total_score: float = Field(
        default=0.0, description="Total weighted score for agent 1"
    )
    agent2_total_score: float = Field(
        default=0.0, description="Total weighted score for agent 2"
    )
    recommended_winner: Optional[str] = Field(
        default=None, description="Judge's recommended winner (agent ID)"
    )

    # Judge's reasoning
    overall_reasoning: str = Field(
        default="", description="Judge's overall reasoning for the decision"
    )
    comparative_analysis: str = Field(
        default="", description="Comparative analysis of both responses"
    )
    key_differentiators: List[str] = Field(
        default_factory=list,
        description="Key factors that differentiated the responses",
    )

    # Quality metrics
    evaluation_quality: float = Field(
        default=0.0, description="Quality of this evaluation (meta-score)"
    )
    is_final: bool = Field(
        default=False, description="Whether this evaluation is finalized"
    )

    # Metadata
    evaluation_time_seconds: float = Field(
        default=0.0, description="Time taken to complete evaluation"
    )
    judge_specialization_match: float = Field(
        default=0.0,
        description="How well judge's specialization matches challenge type",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional evaluation metadata"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evaluation":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)

    def __str__(self) -> str:
        """String representation of the evaluation."""
        return f"Evaluation({self.judge_id}, Match: {self.match_id}, Winner: {self.recommended_winner})"

    def add_score(
        self,
        agent_id: str,
        criterion: EvaluationCriteria,
        score: float,
        reasoning: str,
        confidence: float = 1.0,
    ) -> None:
        """Add a score for a specific agent and criterion."""
        judge_score = JudgeScore(
            criterion=criterion, score=score, reasoning=reasoning, confidence=confidence
        )

        # Add to appropriate agent's scores
        if agent_id.endswith("1"):  # Simple way to identify agent1 vs agent2
            self.agent1_scores.append(judge_score)
        else:
            self.agent2_scores.append(judge_score)

    def calculate_total_scores(
        self, criteria_weights: Optional[Dict[EvaluationCriteria, float]] = None
    ) -> None:
        """Calculate total weighted scores for both agents."""
        if criteria_weights is None:
            # Default equal weights
            criteria_weights = {criterion: 1.0 for criterion in EvaluationCriteria}

        def calculate_agent_score(scores: List[JudgeScore]) -> float:
            if not scores:
                return 0.0

            total_weighted_score = 0.0
            total_weight = 0.0

            for score in scores:
                weight = criteria_weights.get(score.criterion, 1.0)
                confidence_weight = score.confidence
                final_weight = weight * confidence_weight

                total_weighted_score += score.score * final_weight
                total_weight += final_weight

            return total_weighted_score / total_weight if total_weight > 0 else 0.0

        self.agent1_total_score = calculate_agent_score(self.agent1_scores)
        self.agent2_total_score = calculate_agent_score(self.agent2_scores)

    def determine_winner(self, min_score_difference: float = 0.5) -> Optional[str]:
        """Determine the recommended winner based on scores."""
        score_diff = abs(self.agent1_total_score - self.agent2_total_score)

        if score_diff < min_score_difference:
            return None  # Too close to call
        elif self.agent1_total_score > self.agent2_total_score:
            return "agent1"  # This would need to be replaced with actual agent ID
        else:
            return "agent2"  # This would need to be replaced with actual agent ID

    def finalize_evaluation(
        self, overall_reasoning: str = "", comparative_analysis: str = ""
    ) -> None:
        """Finalize the evaluation."""
        self.overall_reasoning = overall_reasoning
        self.comparative_analysis = comparative_analysis
        self.submitted_at = datetime.utcnow()
        self.is_final = True

        # Calculate evaluation time
        if self.created_at:
            self.evaluation_time_seconds = (
                self.submitted_at - self.created_at
            ).total_seconds()

    def get_score_by_criterion(
        self, agent_id: str, criterion: EvaluationCriteria
    ) -> Optional[JudgeScore]:
        """Get a specific score for an agent and criterion."""
        scores = self.agent1_scores if agent_id.endswith("1") else self.agent2_scores

        for score in scores:
            if score.criterion == criterion:
                return score
        return None

    def get_agent_scores_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get a summary of scores for a specific agent."""
        scores = self.agent1_scores if agent_id.endswith("1") else self.agent2_scores
        total_score = (
            self.agent1_total_score
            if agent_id.endswith("1")
            else self.agent2_total_score
        )

        return {
            "total_score": total_score,
            "individual_scores": [
                {
                    "criterion": score.criterion.value,
                    "score": score.score,
                    "reasoning": score.reasoning,
                    "confidence": score.confidence,
                }
                for score in scores
            ],
            "average_score": (
                sum(s.score for s in scores) / len(scores) if scores else 0.0
            ),
            "average_confidence": (
                sum(s.confidence for s in scores) / len(scores) if scores else 0.0
            ),
        }

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a complete summary of the evaluation."""
        return {
            "evaluation_id": self.evaluation_id,
            "judge_id": self.judge_id,
            "match_id": self.match_id,
            "agent1_total": self.agent1_total_score,
            "agent2_total": self.agent2_total_score,
            "recommended_winner": self.recommended_winner,
            "score_difference": abs(self.agent1_total_score - self.agent2_total_score),
            "evaluation_time": self.evaluation_time_seconds,
            "is_final": self.is_final,
            "created_at": self.created_at,
            "submitted_at": self.submitted_at,
        }
