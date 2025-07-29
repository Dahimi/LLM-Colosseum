from typing import List, Optional, Dict
from agent_arena.models.match import Match, MatchStatus
from datetime import datetime
import json
import os

class MatchStore:
    """Store for managing matches in memory and on disk."""
    
    def __init__(self, state_file: str = "match_store.json"):
        self.matches: Dict[str, Match] = {}
        self.live_matches: Dict[str, Match] = {}
        self.state_file = state_file
        self.load_state()
    
    def add_match(self, match: Match) -> None:
        """Add a match to the store."""
        if match.status == MatchStatus.IN_PROGRESS:
            self.live_matches[match.match_id] = match
        self.matches[match.match_id] = match
        self.save_state()
    
    def update_match(self, match: Match) -> None:
        """Update a match in the store."""
        if match.status == MatchStatus.IN_PROGRESS:
            self.live_matches[match.match_id] = match
        elif match.match_id in self.live_matches:
            del self.live_matches[match.match_id]
        self.matches[match.match_id] = match
        self.save_state()
    
    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a match by ID."""
        return self.matches.get(match_id)
    
    def get_live_matches(self) -> List[Match]:
        """Get all live matches."""
        return list(self.live_matches.values())
    
    def get_recent_matches(self, limit: int = 10) -> List[Match]:
        """Get recent matches, sorted by start time."""
        completed_matches = [
            m for m in self.matches.values()
            if m.status not in [MatchStatus.IN_PROGRESS, MatchStatus.PENDING]
        ]
        sorted_matches = sorted(
            completed_matches,
            key=lambda m: m.started_at or datetime.min,
            reverse=True
        )
        return sorted_matches[:limit]
    
    def get_matches_for_agent(self, agent_id: str) -> List[Match]:
        """Get all matches for a specific agent."""
        return [
            m for m in self.matches.values()
            if agent_id in [m.agent1_id, m.agent2_id]
        ]

    def save_state(self) -> None:
        """Save matches to disk."""
        try:
            # Only save completed matches
            completed_matches = {
                match_id: match.to_dict()
                for match_id, match in self.matches.items()
                if match.status not in [MatchStatus.IN_PROGRESS, MatchStatus.PENDING]
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(completed_matches, f, indent=2)
        except Exception as e:
            print(f"Error saving match store state: {e}")

    def load_state(self) -> None:
        """Load matches from disk."""
        if not os.path.exists(self.state_file):
            return
            
        try:
            with open(self.state_file, 'r') as f:
                matches_data = json.load(f)
            
            for match_data in matches_data.values():
                match = Match.from_dict(match_data)
                self.matches[match.match_id] = match
        except Exception as e:
            print(f"Error loading match store state: {e}")
            # If loading fails, start with empty state
            self.matches = {} 