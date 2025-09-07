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

class AgentStats(BaseModel):
    """Statistical tracking for agent performance."""
    elo_rating: float = Field(default=1200.0, description="ELO rating score")
    total_matches: int = Field(default=0, description="Total matches played")
    wins: int = Field(default=0, description="Total wins")
    losses: int = Field(default=0, description="Total losses")
    draws: int = Field(default=0, description="Total draws")
    current_streak: int = Field(default=0, description="Current win/loss streak (positive=wins, negative=losses)")
    best_streak: int = Field(default=0, description="Best win streak achieved")
    consistency_score: float = Field(default=0.0, description="Performance consistency metric (0-1)")
    innovation_index: float = Field(default=0.0, description="Creativity/originality score (0-1)")
    challenges_created: int = Field(default=0, description="Number of challenges created")
    challenge_quality_avg: float = Field(default=0.0, description="Average quality of created challenges")
    judge_accuracy: float = Field(default=0.0, description="Accuracy when acting as judge")
    judge_reliability: float = Field(default=1.0, description="Reliability weight for judging (0-1)")
    elo_history: List[EloHistoryEntry] = Field(default_factory=list, description="History of ELO rating changes")
    streaming_failures: int = Field(default=0, description="Number of times the agent failed during streaming")
    streaming_attempts: int = Field(default=0, description="Total number of streaming attempts")
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_matches == 0:
            return 0.0
        return (self.wins / self.total_matches) * 100
    
    @property
    def loss_rate(self) -> float:
        """Calculate loss rate percentage."""
        if self.total_matches == 0:
            return 0.0
        return (self.losses / self.total_matches) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStats":
        """Deserialize an object from a dictionary."""
        return cls.model_validate(data)


class AgentProfile(BaseModel):
    """Profile information for an agent."""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique agent identifier")
    name: str = Field(description="Agent display name")
    description: str = Field(default="", description="Agent description or bio")
    specializations: List[str] = Field(default_factory=list, description="Areas of expertise")
    model: str = Field(default="openai/gpt-4o-mini", description="LLM model identifier")
    temperature: float = Field(default=0.5, ge=0.0, le=1.0, description="LLM temperature setting")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    is_active: bool = Field(default=True, description="Whether agent is currently active")
    supports_structured_output: bool = Field(default=False, description="Whether agent's model supports structured output")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional agent metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode='json')

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
    stats: AgentStats = Field(default_factory=AgentStats, description="Performance statistics")
    match_history: List[str] = Field(default_factory=list, description="List of match IDs")
    challenge_history: List[str] = Field(default_factory=list, description="List of challenge IDs created")
    division_change_history: List[DivisionChangeHistoryEntry] = Field(default_factory=list, description="Division promotion/demotion history")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a JSON-compatible dictionary."""
        return self.model_dump(mode='json')

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
        self.division = new_division
        entry = DivisionChangeHistoryEntry(
            from_division=old_division.value,
            to_division=new_division.value,
            reason=reason,
            type="promotion"
        )
        self.division_change_history.append(entry)
        self.update_last_active()
    
    def demote_division(self, new_division: Division, reason: str = "") -> None:
        """Demote agent to a lower division."""
        old_division = self.division
        self.division = new_division
        entry = DivisionChangeHistoryEntry(
            from_division=old_division.value,
            to_division=new_division.value,
            reason=reason,
            type="demotion"
        )
        self.division_change_history.append(entry)
        self.update_last_active()
    
    def is_eligible_for_promotion(self) -> bool:
        """Check if agent is eligible for promotion based on performance."""
        # Promotion criteria: 
        # - Win streak >= 3
        # - Win rate > 60%
        # - At least 5 matches played
        return (
            self.stats.current_streak >= 3 and
            self.stats.win_rate > 60 and
            self.stats.total_matches >= 5
        )
    
    def should_be_demoted(self) -> bool:
        """Check if agent should be demoted based on poor performance."""
        # Demotion criteria:
        # - Loss streak >= 5
        # - Win rate < 30% (with at least 10 matches)
        return (
            self.stats.current_streak <= -5 or
            (self.stats.win_rate < 30 and self.stats.total_matches >= 10)
        ) 
        
    def deactivate(self, reason: str = "") -> None:
        """Deactivate the agent."""
        self.profile.is_active = False
        self.profile.metadata["deactivation_reason"] = reason
        self.profile.metadata["deactivation_timestamp"] = datetime.utcnow().isoformat()
        self.update_last_active()
        
    def update_elo(self, new_rating: float, match_id: str, opponent_id: str, opponent_rating: float, result: str, rating_change: float) -> None:
        """Update ELO rating and record the change in history."""
        old_rating = self.stats.elo_rating
        self.stats.elo_rating = new_rating
        
        # Record the change in history
        entry = EloHistoryEntry(
            rating=new_rating,
            match_id=match_id,
            opponent_id=opponent_id,
            opponent_rating=opponent_rating,
            result=result,
            rating_change=rating_change
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
                "rating_change": rating_change
            }
            
            supabase.table("elo_history").insert(elo_history_data).execute()
        except Exception as e:
            print(f"Error saving ELO history to database: {e}")
            
        self.update_last_active() 