"""Challenge data models for the Intelligence Arena System."""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class ChallengeType(Enum):
    """Types of intellectual challenges."""

    LOGICAL_REASONING = "logical_reasoning"
    CREATIVE_PROBLEM_SOLVING = "creative_problem_solving"
    KNOWLEDGE_INTEGRATION = "knowledge_integration"
    ABSTRACT_THINKING = "abstract_thinking"
    ADAPTIVE_LEARNING = "adaptive_learning"
    META_COGNITION = "meta_cognition"
    MATHEMATICAL = "mathematical"
    LINGUISTIC = "linguistic"
    PATTERN_RECOGNITION = "pattern_recognition"
    ETHICAL_REASONING = "ethical_reasoning"
    DEBATE = "debate"


class ChallengeDifficulty(Enum):
    """Difficulty levels for challenges."""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5


class Challenge(BaseModel):
    """A challenge/problem for agents to solve."""

    challenge_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique challenge identifier",
    )
    title: str = Field(description="Challenge title")
    description: str = Field(description="Detailed challenge description/prompt")
    challenge_type: ChallengeType = Field(description="Type of challenge")
    difficulty: ChallengeDifficulty = Field(description="Difficulty level")
    creator_id: Optional[str] = Field(
        default=None, description="ID of agent who created this challenge"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    # Challenge parameters
    time_limit_minutes: Optional[int] = Field(
        default=None, description="Time limit in minutes (None = no limit)"
    )
    max_response_length: Optional[int] = Field(
        default=None, description="Maximum response length in characters"
    )
    requires_structured_output: bool = Field(
        default=False, description="Whether response must follow a specific format"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None, description="Pydantic schema for structured output"
    )

    # Challenge content
    context: str = Field(default="", description="Background context for the challenge")
    constraints: List[str] = Field(
        default_factory=list, description="Constraints or rules for solving"
    )
    hints: List[str] = Field(
        default_factory=list,
        description="Optional hints (revealed based on difficulty)",
    )
    examples: List[Dict[str, str]] = Field(
        default_factory=list, description="Example inputs/outputs"
    )
    answer: Optional[str] = Field(
        default=None, description="Correct answer or solution (used for evaluation)"
    )

    # Evaluation criteria
    evaluation_criteria: List[str] = Field(
        default_factory=list, description="Specific criteria for judging responses"
    )
    expected_concepts: List[str] = Field(
        default_factory=list, description="Concepts expected in a good response"
    )
    scoring_rubric: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed scoring criteria"
    )

    # Usage tracking
    times_used: int = Field(
        default=0, description="Number of times this challenge has been used"
    )
    average_score: float = Field(
        default=0.0, description="Average score across all attempts"
    )
    difficulty_rating: float = Field(
        default=0.0, description="Actual difficulty based on performance (0-10)"
    )
    discrimination_power: float = Field(
        default=0.0, description="How well it separates strong/weak agents (0-1)"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    source: str = Field(
        default="generated",
        description="Source of the challenge (generated, imported, etc.)",
    )
    is_active: bool = Field(
        default=True, description="Whether challenge is currently usable"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional challenge metadata"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Challenge":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)

    def __str__(self) -> str:
        """String representation of the challenge."""
        return f"Challenge({self.title}, {self.challenge_type.value}, Difficulty: {self.difficulty.value})"

    def get_prompt(self, include_hints: bool = False, hint_level: int = 0) -> str:
        """Get the full challenge prompt for agents."""
        prompt_parts = [
            f"**Challenge: {self.title}**",
            f"**Type:** {self.challenge_type.value.replace('_', ' ').title()}",
            f"**Difficulty:** {self.difficulty.name}",
            "",
        ]

        if self.context:
            prompt_parts.extend(["**Context:**", self.context, ""])

        prompt_parts.extend(["**Challenge:**", self.description, ""])

        if self.constraints:
            prompt_parts.extend(
                [
                    "**Constraints:**",
                    *[f"- {constraint}" for constraint in self.constraints],
                    "",
                ]
            )

        if include_hints and self.hints and hint_level > 0:
            available_hints = self.hints[:hint_level]
            prompt_parts.extend(
                ["**Hints:**", *[f"- {hint}" for hint in available_hints], ""]
            )

        if self.examples:
            prompt_parts.extend(
                [
                    "**Examples:**",
                    *[
                        f"Input: {ex.get('input', 'N/A')}\nOutput: {ex.get('output', 'N/A')}"
                        for ex in self.examples
                    ],
                    "",
                ]
            )

        if self.time_limit_minutes:
            prompt_parts.append(f"**Time Limit:** {self.time_limit_minutes} minutes")

        if self.max_response_length:
            prompt_parts.append(
                f"**Max Response Length:** {self.max_response_length} characters"
            )

        if self.requires_structured_output:
            prompt_parts.extend(
                [
                    "",
                    "**Note:** Your response must follow the specified structured format.",
                ]
            )

        return "\n".join(prompt_parts)

    def update_stats(self, score: float, agent_elo: float) -> None:
        """Update challenge statistics based on a new attempt."""
        # Update usage count
        self.times_used += 1

        # Update average score (running average)
        if self.times_used == 1:
            self.average_score = score
        else:
            self.average_score = (
                (self.average_score * (self.times_used - 1)) + score
            ) / self.times_used

        # Update difficulty rating based on performance
        # If high-ELO agents struggle, increase difficulty rating
        # If low-ELO agents do well, decrease difficulty rating
        expected_performance = min(
            10.0, max(0.0, agent_elo / 200)
        )  # Normalize ELO to 0-10 scale
        performance_diff = score - expected_performance

        # Adjust difficulty rating (exponential moving average)
        alpha = 0.1  # Learning rate
        if performance_diff < 0:  # Agent performed worse than expected
            self.difficulty_rating = (
                self.difficulty_rating * (1 - alpha)
                + (self.difficulty_rating + abs(performance_diff)) * alpha
            )
        else:  # Agent performed better than expected
            self.difficulty_rating = max(
                0.0,
                self.difficulty_rating * (1 - alpha)
                + (self.difficulty_rating - performance_diff) * alpha,
            )

    def is_suitable_for_division(self, division: str) -> bool:
        """Check if this challenge is suitable for a given division."""
        division_difficulty_map = {
            "novice": [ChallengeDifficulty.BEGINNER, ChallengeDifficulty.INTERMEDIATE],
            "expert": [ChallengeDifficulty.INTERMEDIATE, ChallengeDifficulty.ADVANCED],
            "master": [ChallengeDifficulty.ADVANCED, ChallengeDifficulty.EXPERT],
            "king": [ChallengeDifficulty.EXPERT, ChallengeDifficulty.MASTER],
        }

        return self.difficulty in division_difficulty_map.get(division, [])
