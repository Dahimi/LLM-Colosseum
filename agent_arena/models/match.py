"""Match data models for the Intelligence Arena System."""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class MatchStatus(Enum):
    """Status of a match."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_JUDGMENT = "awaiting_judgment"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class MatchResult(Enum):
    """Result of a match from perspective of agent1."""
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    NO_CONTEST = "no_contest"


class MatchType(Enum):
    """Type of match being played."""
    REGULAR_DUEL = "regular_duel"
    KING_CHALLENGE = "king_challenge"
    PROMOTION_MATCH = "promotion_match"
    RELEGATION_MATCH = "relegation_match"
    TOURNAMENT = "tournament"


class AgentResponse(BaseModel):
    """An agent's response to a challenge."""
    agent_id: str = Field(description="ID of the responding agent")
    response_text: str = Field(description="The agent's response")
    response_time: float = Field(description="Time taken to respond (seconds)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When response was submitted")
    is_structured: bool = Field(default=False, description="Whether response follows structured format")
    structured_data: Optional[Dict[str, Any]] = Field(default=None, description="Parsed structured response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


class Match(BaseModel):
    """A competition match between agents."""
    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique match identifier")
    match_type: MatchType = Field(description="Type of match")
    challenge_id: str = Field(description="ID of the challenge being used")
    
    # Participants
    agent1_id: str = Field(description="First competing agent ID")
    agent2_id: str = Field(description="Second competing agent ID")
    judge_ids: List[str] = Field(default_factory=list, description="List of judge agent IDs")
    
    # Match state
    status: MatchStatus = Field(default=MatchStatus.PENDING, description="Current match status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Match creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Match start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Match completion timestamp")
    
    # Responses
    agent1_response: Optional[AgentResponse] = Field(default=None, description="Agent 1's response")
    agent2_response: Optional[AgentResponse] = Field(default=None, description="Agent 2's response")
    
    # Results
    winner_id: Optional[str] = Field(default=None, description="ID of the winning agent")
    result: Optional[MatchResult] = Field(default=None, description="Match result from agent1's perspective")
    final_scores: Dict[str, float] = Field(default_factory=dict, description="Final scores for each agent")
    evaluation_ids: List[str] = Field(default_factory=list, description="List of evaluation IDs from judges")
    
    # Match parameters
    division: str = Field(description="Division where this match takes place")
    stakes: Dict[str, Any] = Field(default_factory=dict, description="What's at stake (ELO, promotion, etc.)")
    special_rules: List[str] = Field(default_factory=list, description="Any special rules for this match")
    
    # Metadata
    context: str = Field(default="", description="Additional context about this match")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional match metadata")
    
    def __str__(self) -> str:
        """String representation of the match."""
        return f"Match({self.agent1_id} vs {self.agent2_id}, {self.status.value}, {self.match_type.value})"
    
    def start_match(self) -> None:
        """Mark the match as started."""
        self.status = MatchStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def submit_response(self, agent_id: str, response: AgentResponse) -> bool:
        """Submit a response from an agent."""
        if self.status != MatchStatus.IN_PROGRESS:
            return False
        
        if agent_id == self.agent1_id:
            self.agent1_response = response
        elif agent_id == self.agent2_id:
            self.agent2_response = response
        else:
            return False
        
        # Check if both responses are in
        if self.agent1_response and self.agent2_response:
            self.status = MatchStatus.AWAITING_JUDGMENT
        
        return True
    
    def complete_match(self, winner_id: Optional[str], final_scores: Dict[str, float]) -> None:
        """Complete the match with results."""
        self.status = MatchStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.winner_id = winner_id
        self.final_scores = final_scores
        
        # Determine result from agent1's perspective
        if winner_id is None:
            self.result = MatchResult.DRAW
        elif winner_id == self.agent1_id:
            self.result = MatchResult.WIN
        else:
            self.result = MatchResult.LOSS
    
    def cancel_match(self, reason: str = "") -> None:
        """Cancel the match."""
        self.status = MatchStatus.CANCELLED
        self.metadata["cancellation_reason"] = reason
        self.completed_at = datetime.utcnow()
    
    def get_opponent_id(self, agent_id: str) -> Optional[str]:
        """Get the opponent's ID for a given agent."""
        if agent_id == self.agent1_id:
            return self.agent2_id
        elif agent_id == self.agent2_id:
            return self.agent1_id
        return None
    
    def get_agent_response(self, agent_id: str) -> Optional[AgentResponse]:
        """Get the response for a specific agent."""
        if agent_id == self.agent1_id:
            return self.agent1_response
        elif agent_id == self.agent2_id:
            return self.agent2_response
        return None
    
    def get_agent_score(self, agent_id: str) -> Optional[float]:
        """Get the final score for a specific agent."""
        return self.final_scores.get(agent_id)
    
    def is_ready_for_judgment(self) -> bool:
        """Check if the match is ready for judge evaluation."""
        return (
            self.status == MatchStatus.AWAITING_JUDGMENT and
            self.agent1_response is not None and
            self.agent2_response is not None
        )
    
    def get_match_duration(self) -> Optional[float]:
        """Get the total match duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the match."""
        return {
            "match_id": self.match_id,
            "type": self.match_type.value,
            "status": self.status.value,
            "agents": [self.agent1_id, self.agent2_id],
            "winner": self.winner_id,
            "division": self.division,
            "duration": self.get_match_duration(),
            "scores": self.final_scores,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        } 