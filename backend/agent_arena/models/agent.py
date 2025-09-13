"""Agent data models for the Intelligence Arena System."""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Division(Enum):
    """Agent division levels in the arena."""

    NOVICE = "novice"
    EXPERT = "expert"
    MASTER = "master"
    KING = "king"


class EloHistoryEntry(BaseModel):
    """Entry for tracking ELO rating changes."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rating: float
    match_id: str
    opponent_id: str
    opponent_rating: float
    result: str  # "win", "loss", or "draw"
    rating_change: float


class DivisionStats(BaseModel):
    """Statistics for performance within a specific division."""

    matches: int = Field(default=0, description="Matches played in this division")
    wins: int = Field(default=0, description="Wins in this division")
    losses: int = Field(default=0, description="Losses in this division")
    draws: int = Field(default=0, description="Draws in this division")
    current_streak: int = Field(
        default=0,
        description="Current win/loss streak in this division (positive=wins, negative=losses)",
    )
    best_streak: int = Field(default=0, description="Best win streak in this division")
    division_entry_date: Optional[datetime] = Field(
        default=None, description="When the agent entered this division"
    )

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage for this division."""
        if self.matches == 0:
            return 0.0
        return (self.wins / self.matches) * 100

    @property
    def loss_rate(self) -> float:
        """Calculate loss rate percentage for this division."""
        if self.matches == 0:
            return 0.0
        return (self.losses / self.matches) * 100


class CareerStats(BaseModel):
    """Career-wide statistics across all divisions."""

    total_matches: int = Field(
        default=0, description="Total matches across all divisions"
    )
    total_wins: int = Field(default=0, description="Total wins across all divisions")
    total_losses: int = Field(
        default=0, description="Total losses across all divisions"
    )
    total_draws: int = Field(default=0, description="Total draws across all divisions")
    divisions_reached: List[str] = Field(
        default_factory=list, description="List of divisions reached in career"
    )
    promotions: int = Field(default=0, description="Total number of promotions")
    demotions: int = Field(default=0, description="Total number of demotions")

    @property
    def career_win_rate(self) -> float:
        """Calculate career win rate percentage."""
        if self.total_matches == 0:
            return 0.0
        return (self.total_wins / self.total_matches) * 100


class AgentStats(BaseModel):
    """Statistical tracking for agent performance."""

    # Global ELO rating (represents overall skill level)
    elo_rating: float = Field(default=1200.0, description="Global ELO rating score")
    
    # Starting ELO rating (what the agent began with)
    starting_elo: float = Field(default=1200.0, description="Starting ELO rating for this agent")

    # Current division performance (used for promotion/demotion decisions)
    current_division_stats: DivisionStats = Field(
        default_factory=DivisionStats, description="Stats in current division"
    )

    # Career totals (for achievement tracking)
    career_stats: CareerStats = Field(
        default_factory=CareerStats, description="Career-wide statistics"
    )

    # Division history (stats per division)
    division_history: Dict[str, DivisionStats] = Field(
        default_factory=dict, description="Historical stats per division"
    )

    # Other stats (unchanged)
    consistency_score: float = Field(
        default=0.0, description="Performance consistency metric (0-1)"
    )
    innovation_index: float = Field(
        default=0.0, description="Creativity/originality score (0-1)"
    )
    challenges_created: int = Field(
        default=0, description="Number of challenges created"
    )
    challenge_quality_avg: float = Field(
        default=0.0, description="Average quality of created challenges"
    )
    judge_accuracy: float = Field(
        default=0.0, description="Accuracy when acting as judge"
    )
    judge_reliability: float = Field(
        default=1.0, description="Reliability weight for judging (0-1)"
    )
    elo_history: List[EloHistoryEntry] = Field(
        default_factory=list, description="History of ELO rating changes"
    )
    streaming_failures: int = Field(
        default=0, description="Number of times the agent failed during streaming"
    )
    streaming_attempts: int = Field(
        default=0, description="Total number of streaming attempts"
    )

    # Legacy properties for backward compatibility
    @property
    def total_matches(self) -> int:
        """Legacy: Total matches (now from career stats)."""
        return self.career_stats.total_matches

    @property
    def wins(self) -> int:
        """Legacy: Total wins (now from career stats)."""
        return self.career_stats.total_wins

    @property
    def losses(self) -> int:
        """Legacy: Total losses (now from career stats)."""
        return self.career_stats.total_losses

    @property
    def draws(self) -> int:
        """Legacy: Total draws (now from career stats)."""
        return self.career_stats.total_draws

    @property
    def current_streak(self) -> int:
        """Current streak in current division."""
        return self.current_division_stats.current_streak

    @property
    def best_streak(self) -> int:
        """Best streak across all divisions."""
        best = self.current_division_stats.best_streak
        for division_stats in self.division_history.values():
            best = max(best, division_stats.best_streak)
        return best

    @property
    def win_rate(self) -> float:
        """Current division win rate (used for promotions)."""
        return self.current_division_stats.win_rate

    @property
    def loss_rate(self) -> float:
        """Current division loss rate."""
        return self.current_division_stats.loss_rate

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        data = self.model_dump(mode="json")
        
        # Manually add computed properties that Pydantic doesn't serialize
        if "current_division_stats" in data and data["current_division_stats"]:
            data["current_division_stats"]["win_rate"] = self.current_division_stats.win_rate
            data["current_division_stats"]["loss_rate"] = self.current_division_stats.loss_rate
        
        if "career_stats" in data and data["career_stats"]:
            data["career_stats"]["career_win_rate"] = self.career_stats.career_win_rate
        
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStats":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)

    def reset_current_division_stats(self, division: str) -> None:
        """Reset current division stats when promoted/demoted."""
        # Archive current division stats if they exist
        if self.current_division_stats.matches > 0:
            self.division_history[division] = self.current_division_stats.model_copy()

        # Reset current division stats
        self.current_division_stats = DivisionStats(
            division_entry_date=datetime.utcnow()
        )

    def update_match_stats(self, result: str) -> None:
        """Update stats after a match."""
        # Update current division stats
        self.current_division_stats.matches += 1

        if result == "win":
            self.current_division_stats.wins += 1
            self.current_division_stats.current_streak = max(
                1, self.current_division_stats.current_streak + 1
            )
            self.current_division_stats.best_streak = max(
                self.current_division_stats.best_streak,
                self.current_division_stats.current_streak,
            )
        elif result == "loss":
            self.current_division_stats.losses += 1
            self.current_division_stats.current_streak = min(
                -1, self.current_division_stats.current_streak - 1
            )
        else:  # draw
            self.current_division_stats.draws += 1
            self.current_division_stats.current_streak = 0

        # Update career stats
        self.career_stats.total_matches += 1
        if result == "win":
            self.career_stats.total_wins += 1
        elif result == "loss":
            self.career_stats.total_losses += 1
        else:
            self.career_stats.total_draws += 1


class AgentProfile(BaseModel):
    """Profile information for an agent."""

    agent_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique agent identifier"
    )
    name: str = Field(description="Agent display name")
    description: str = Field(default="", description="Agent description or bio")
    specializations: List[str] = Field(
        default_factory=list, description="Areas of expertise"
    )
    model: str = Field(default="openai/gpt-4o-mini", description="LLM model identifier")
    temperature: float = Field(
        default=0.5, ge=0.0, le=1.0, description="LLM temperature setting"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    is_active: bool = Field(
        default=True, description="Whether agent is currently active"
    )
    supports_structured_output: bool = Field(
        default=False, description="Whether agent's model supports structured output"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional agent metadata"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentProfile":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)


class DivisionChangeHistoryEntry(BaseModel):
    """Entry for tracking division changes."""

    from_division: str
    to_division: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: str
    type: str  # "promotion" or "demotion"


class Agent(BaseModel):
    """Main agent class representing a competitor in the arena."""

    profile: AgentProfile = Field(description="Agent profile information")
    division: Division = Field(default=Division.NOVICE, description="Current division")
    stats: AgentStats = Field(
        default_factory=AgentStats, description="Performance statistics"
    )
    match_history: List[str] = Field(
        default_factory=list, description="List of match IDs"
    )
    challenge_history: List[str] = Field(
        default_factory=list, description="List of challenge IDs created"
    )
    division_change_history: List[DivisionChangeHistoryEntry] = Field(
        default_factory=list, description="Division promotion/demotion history"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"Agent({self.profile.name}, {self.division.value}, ELO: {self.stats.elo_rating:.0f})"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"Agent(id={self.profile.agent_id}, name={self.profile.name}, division={self.division.value}, elo={self.stats.elo_rating})"

    def update_last_active(self) -> None:
        """Update the last active timestamp."""
        self.profile.last_active = datetime.utcnow()

    def add_match(self, match_id: str) -> None:
        """Add a match to the agent's history."""
        self.match_history.append(match_id)
        self.update_last_active()

    def add_challenge(self, challenge_id: str) -> None:
        """Add a created challenge to the agent's history."""
        self.challenge_history.append(challenge_id)
        self.stats.challenges_created += 1
        self.update_last_active()

    def promote_division(self, new_division: Division, reason: str = "") -> None:
        """Promote agent to a higher division."""
        old_division = self.division

        # Archive current division stats and reset for new division
        self.stats.reset_current_division_stats(old_division.value)

        # Update division
        self.division = new_division

        # Update career stats
        if new_division.value not in self.stats.career_stats.divisions_reached:
            self.stats.career_stats.divisions_reached.append(new_division.value)
        self.stats.career_stats.promotions += 1

        # Add to history
        entry = DivisionChangeHistoryEntry(
            from_division=old_division.value,
            to_division=new_division.value,
            reason=reason,
            type="promotion",
        )
        self.division_change_history.append(entry)
        self.update_last_active()

    def demote_division(self, new_division: Division, reason: str = "") -> None:
        """Demote agent to a lower division."""
        old_division = self.division

        # Archive current division stats and reset for new division
        self.stats.reset_current_division_stats(old_division.value)

        # Update division
        self.division = new_division

        # Update career stats
        self.stats.career_stats.demotions += 1

        # Add to history
        entry = DivisionChangeHistoryEntry(
            from_division=old_division.value,
            to_division=new_division.value,
            reason=reason,
            type="demotion",
        )
        self.division_change_history.append(entry)
        self.update_last_active()

    def is_eligible_for_promotion(self) -> bool:
        """Check if agent is eligible for promotion based on current division performance."""
        current_stats = self.stats.current_division_stats
        # Require minimum 5 matches in current division
        return (
            current_stats.current_streak >= 3
            and current_stats.win_rate > 60
            and current_stats.matches >= 5
        )

    def should_be_demoted(self) -> bool:
        """Check if agent should be demoted based on current division performance."""
        current_stats = self.stats.current_division_stats
        # Require minimum 5 matches in current division for demotion
        return current_stats.matches >= 5 and (
            current_stats.current_streak <= -4
            or (current_stats.win_rate < 30 and current_stats.matches >= 8)
        )

    def deactivate(self, reason: str = "") -> None:
        """Deactivate the agent."""
        self.profile.is_active = False
        self.profile.metadata["deactivation_reason"] = reason
        self.profile.metadata["deactivated_at"] = datetime.utcnow().isoformat()
        self.update_last_active()

    def update_elo(
        self,
        new_rating: float,
        match_id: str,
        opponent_id: str,
        opponent_rating: float,
        result: str,
        rating_change: float,
    ) -> None:
        """Update ELO rating and add to history."""
        self.stats.elo_rating = new_rating

        # Record the change in history
        entry = EloHistoryEntry(
            rating=new_rating,
            match_id=match_id,
            opponent_id=opponent_id,
            opponent_rating=opponent_rating,
            result=result,
            rating_change=rating_change,
        )
        self.stats.elo_history.append(entry)

        # Also save to the elo_history table in the database
        try:
            from agent_arena.db import supabase

            # Insert the ELO history entry into the database
            elo_history_data = {
                "agent_id": self.profile.name,
                "match_id": match_id,
                "opponent_id": opponent_id,
                "opponent_elo": opponent_rating,
                "result": result,
                "rating_change": rating_change,
            }

            supabase.table("elo_history").insert(elo_history_data).execute()
        except Exception as e:
            print(f"Error saving ELO history to database: {e}")

        # Update match stats
        self.stats.update_match_stats(result)

        self.update_last_active()
