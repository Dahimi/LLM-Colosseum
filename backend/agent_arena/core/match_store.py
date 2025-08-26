from typing import List, Optional, Dict
from agent_arena.models.match import Match, MatchStatus
from agent_arena.db import supabase
from agent_arena.utils.logging import get_logger
from datetime import datetime, timezone
import json
import os

logger = get_logger(__name__)

class MatchStore:
    """Store for managing matches in memory with database persistence."""
    
    def __init__(self, state_file: str = "match_store.json"):
        # In-memory storage
        self.matches: Dict[str, Match] = {}
        self.live_matches: Dict[str, Match] = {}
        self.state_file = state_file
        self._load_from_db()
    
    def _load_from_db(self):
        """Load matches from the database into memory."""
        try:
            # Load completed matches
            completed_response = supabase.table("matches").select("*") \
                .not_.in_("status", [MatchStatus.IN_PROGRESS.value, MatchStatus.PENDING.value]) \
                .execute()
            
            # Load in-progress matches
            live_response = supabase.table("matches").select("*") \
                .eq("status", MatchStatus.IN_PROGRESS.value) \
                .execute()
            
            # Process completed matches
            for data in completed_response.data:
                match = Match.from_dict(data)
                self.matches[match.match_id] = match
            
            # Process live matches
            for data in live_response.data:
                match = Match.from_dict(data)
                self.matches[match.match_id] = match
                self.live_matches[match.match_id] = match
                
            logger.info(f"Loaded {len(self.matches)} matches from DB ({len(self.live_matches)} live)")
        except Exception as e:
            logger.error(f"Error loading matches from DB: {e}")
            # If loading fails, start with empty state
            self.matches = {}
            self.live_matches = {}
    
    def add_match(self, match: Match) -> None:
        """Add a match to the store and database."""
        # Update in-memory store
        if match.status == MatchStatus.IN_PROGRESS:
            self.live_matches[match.match_id] = match
        self.matches[match.match_id] = match
        
        # Add to database
        try:
            match_dict = match.model_dump(mode='json')
            # Ensure enums are stored as strings
            match_dict['status'] = match.status.value
            match_dict['match_type'] = match.match_type.value
            if match.division:
                match_dict['division'] = match.division if isinstance(match.division, str) else match.division.value
            
            supabase.table("matches").insert(match_dict).execute()
        except Exception as e:
            logger.error(f"Error adding match to DB: {e}")
    
    def update_match(self, match: Match) -> None:
        """Update a match in the store and optionally in the database."""
        # Always update in-memory store
        if match.status == MatchStatus.IN_PROGRESS:
            self.live_matches[match.match_id] = match
        elif match.match_id in self.live_matches:
            del self.live_matches[match.match_id]
        self.matches[match.match_id] = match
        
        # Only update database if not streaming or match status changed
        if match.status != MatchStatus.IN_PROGRESS and match.status != MatchStatus.AWAITING_JUDGMENT:
            try:
                match_dict = match.model_dump(mode='json')
                # Ensure enums are stored as strings
                match_dict['status'] = match.status.value
                match_dict['match_type'] = match.match_type.value
                if match.division:
                    match_dict['division'] = match.division if isinstance(match.division, str) else match.division.value
                
                supabase.table("matches").update(match_dict).eq("match_id", match.match_id).execute()
            except Exception as e:
                logger.error(f"Error updating match in DB: {e}", exc_info=True)
    
    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a match by ID from memory, falling back to database if needed."""
        # First try in-memory cache
        if match_id in self.matches:
            return self.matches[match_id]
        
        # If not in memory, try database
        try:
            response = supabase.table("matches").select("*").eq("match_id", match_id).execute()
            if not response.data:
                # If not found, try with id field (from the database schema)
                response = supabase.table("matches").select("*").eq("id", match_id).execute()
            
            if response.data:
                match = Match.from_dict(response.data[0])
                # Cache in memory for future use
                self.matches[match.match_id] = match
                if match.status == MatchStatus.IN_PROGRESS:
                    self.live_matches[match.match_id] = match
                return match
            return None
        except Exception as e:
            logger.error(f"Error getting match from DB: {e}")
            return None
    
    def get_live_matches(self) -> List[Match]:
        """Get all live (in-progress) matches from memory."""
        return list(self.live_matches.values())
    
    def get_recent_matches(self, limit: int = 10) -> List[Match]:
        """Get recent matches, sorted by start time."""
        completed_matches = [
            m for m in self.matches.values()
            if m.status not in [MatchStatus.IN_PROGRESS, MatchStatus.PENDING]
        ]
        sorted_matches = sorted(
            completed_matches,
            key=lambda m: (m.started_at.replace(tzinfo=None) if m.started_at and m.started_at.tzinfo else m.started_at) or datetime.min,
            reverse=True
        )
        return sorted_matches[:limit]
    
    def get_matches_for_agent(self, agent_id: str) -> List[Match]:
        """Get all matches for a specific agent from memory."""
        # First try in-memory cache
        agent_matches = [
            m for m in self.matches.values()
            if agent_id in [m.agent1_id, m.agent2_id]
        ]
        
        # If we have matches in memory, return them
        if agent_matches:
            # Sort matches, handling potential timezone issues
            try:
                return sorted(
                    agent_matches,
                    key=lambda m: (m.created_at.replace(tzinfo=None) if m.created_at and m.created_at.tzinfo else m.created_at) or datetime.min,
                    reverse=True
                )
            except Exception as e:
                logger.error(f"Error sorting agent matches: {e}")
                # Fallback sorting method
                return agent_matches
        
        # Otherwise, query the database
        try:
            # Query for matches where agent is either agent1_id or agent2_id
            response = supabase.table("matches").select("*") \
                .eq("agent1_id", agent_id) \
                .execute()
            
            # Get matches where agent is agent2_id
            response2 = supabase.table("matches").select("*") \
                .eq("agent2_id", agent_id) \
                .execute()
            
            # Combine results
            all_matches = response.data + response2.data
            
            # Convert to Match objects and cache in memory
            result = []
            for data in all_matches:
                match = Match.from_dict(data)
                self.matches[match.match_id] = match
                if match.status == MatchStatus.IN_PROGRESS:
                    self.live_matches[match.match_id] = match
                result.append(match)
            
            # Sort by created_at (descending) with timezone handling
            try:
                return sorted(
                    result,
                    key=lambda m: (m.created_at.replace(tzinfo=None) if m.created_at and m.created_at.tzinfo else m.created_at) or datetime.min,
                    reverse=True
                )
            except Exception as e:
                logger.error(f"Error sorting database matches: {e}")
                return result
        except Exception as e:
            logger.error(f"Error getting matches for agent {agent_id} from DB: {e}")
            return []
            
    def sync_to_db(self) -> None:
        """Sync all matches to the database (useful for periodic backups)."""
        try:
            for match in self.matches.values():
                match_dict = match.model_dump(mode='json')
                # Ensure enums are stored as strings
                match_dict['status'] = match.status.value
                match_dict['match_type'] = match.match_type.value
                if match.division:
                    match_dict['division'] = match.division if isinstance(match.division, str) else match.division.value
                
                # Update or insert
                supabase.table("matches").upsert(match_dict).execute()
            
            logger.info(f"Synced {len(self.matches)} matches to database")
        except Exception as e:
            logger.error(f"Error syncing matches to database: {e}") 