from typing import List, Optional, Dict
from agent_arena.models.match import Match, MatchStatus
from agent_arena.models.challenge import Challenge
from agent_arena.db import supabase
from agent_arena.utils.logging import get_logger
from datetime import datetime, timezone
import json
import os

logger = get_logger(__name__)


class MatchStore:
    """Store for managing matches in memory with database persistence."""

    def __init__(
        self,
        state_file: str = "match_store.json",
        max_completed_matches: int = 1000,
        max_live_matches: int = None,
    ):
        # In-memory storage
        self.matches: Dict[str, Match] = {}
        self.live_matches: Dict[str, Match] = {}
        self.challenge_cache: Dict[str, Challenge] = (
            {}
        )  # Cache challenges by challenge_id
        self.state_file = state_file
        self.max_completed_matches = max_completed_matches
        self.max_live_matches = (
            max_live_matches
            if max_live_matches
            else int(os.getenv("MAX_LIVE_MATCHES", 10))
        )
        self._load_from_db()

    def _load_from_db(self):
        """Load matches from the database into memory."""
        try:
            # Load limited number of completed matches (most recent first)
            completed_response = (
                supabase.table("matches")
                .select("*")
                .not_.in_(
                    "status",
                    [
                        MatchStatus.IN_PROGRESS.value,
                        MatchStatus.PENDING.value,
                        MatchStatus.AWAITING_JUDGMENT.value,
                    ],
                )
                .order("completed_at", desc=True)
                .limit(self.max_completed_matches)
                .execute()
            )

            # Load in-progress matches
            live_response = (
                supabase.table("matches")
                .select("*")
                .eq("status", MatchStatus.IN_PROGRESS.value)
                .execute()
            )

            # Process completed matches
            for data in completed_response.data:
                match = Match.from_dict(data)
                self.matches[match.match_id] = match

            # Process live matches
            for data in live_response.data:
                match = Match.from_dict(data)
                self.matches[match.match_id] = match
                self.live_matches[match.match_id] = match

            logger.info(
                f"Loaded {len(self.matches)} matches from DB ({len(self.live_matches)} live)"
            )
        except Exception as e:
            logger.error(f"Error loading matches from DB: {e}")
            # If loading fails, start with empty state
            self.matches = {}
            self.live_matches = {}

    def add_match(self, match: Match, challenge: Optional[Challenge] = None) -> None:
        """Add a match to the store and database."""
        # Update in-memory store
        if match.status == MatchStatus.IN_PROGRESS:
            self.live_matches[match.match_id] = match
        self.matches[match.match_id] = match

        # Cache the challenge if provided
        if challenge and match.challenge_id:
            self.challenge_cache[match.challenge_id] = challenge

        # Add to database
        try:
            match_dict = match.model_dump(mode="json")
            # Ensure enums are stored as strings
            match_dict["status"] = match.status.value
            match_dict["match_type"] = match.match_type.value
            if match.division:
                match_dict["division"] = (
                    match.division
                    if isinstance(match.division, str)
                    else match.division.value
                )

            supabase.table("matches").insert(match_dict).execute()
        except Exception as e:
            logger.error(f"Error adding match to DB: {e}")

    def update_match(self, match: Match) -> None:
        """Update a match in the store and optionally in the database."""
        # Always update in-memory store
        if (
            match.status == MatchStatus.IN_PROGRESS
            or match.status == MatchStatus.PENDING
            or match.status == MatchStatus.AWAITING_JUDGMENT
        ):
            self.live_matches[match.match_id] = match
        else:
            # Match is completed, check if we need to trim the cache
            if match.match_id in self.live_matches:
                del self.live_matches[match.match_id]

        self.matches[match.match_id] = match
        self._trim_completed_matches()

        # Only update database if not streaming or match status changed
        if (
            match.status != MatchStatus.IN_PROGRESS
            and match.status != MatchStatus.AWAITING_JUDGMENT
        ):
            try:
                match_dict = match.model_dump(mode="json")
                # Ensure enums are stored as strings
                match_dict["status"] = match.status.value
                match_dict["match_type"] = match.match_type.value
                if match.division:
                    match_dict["division"] = (
                        match.division
                        if isinstance(match.division, str)
                        else match.division.value
                    )

                supabase.table("matches").update(match_dict).eq(
                    "match_id", match.match_id
                ).execute()
            except Exception as e:
                logger.error(f"Error updating match in DB: {e}", exc_info=True)

    def _trim_completed_matches(self):
        """Trim the completed matches cache if it exceeds the maximum size. and Remove the challenge cache if it exceeds the maximum size."""
        completed_matches = {
            match_id: match
            for match_id, match in self.matches.items()
            if match_id not in self.live_matches
        }

        if len(completed_matches) > self.max_completed_matches:
            # Sort completed matches by completion time (oldest first)
            sorted_matches = sorted(
                completed_matches.items(),
                key=lambda x: (
                    x[1].completed_at.replace(tzinfo=None)
                    if x[1].completed_at and x[1].completed_at.tzinfo
                    else x[1].completed_at
                )
                or datetime.min,
            )

            # Remove oldest matches until we're under the limit
            matches_to_remove = len(completed_matches) - self.max_completed_matches
            for i in range(matches_to_remove):
                match_id, _ = sorted_matches[i]
                if match_id in self.matches:
                    del self.matches[match_id]
                    # Remove the challenge cache if it exists
                    if match_id in self.challenge_cache:
                        del self.challenge_cache[match_id]

            logger.info(
                f"Trimmed {matches_to_remove} old completed matches from memory cache"
            )

    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a match by ID from memory, falling back to database if needed."""
        # First try in-memory cache
        if match_id in self.matches:
            return self.matches[match_id]

        # If not in memory, try database
        try:
            response = (
                supabase.table("matches").select("*").eq("match_id", match_id).execute()
            )
            if not response.data:
                # If not found, try with id field (from the database schema)
                response = (
                    supabase.table("matches").select("*").eq("id", match_id).execute()
                )

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

    def get_challenge_for_match(self, challenge_id: str) -> Optional[Challenge]:
        """Get challenge details for a match, using cache or fetching from DB if needed."""
        # First try in-memory cache
        if challenge_id in self.challenge_cache:
            return self.challenge_cache[challenge_id]

        # If not in cache, fetch from database
        try:
            response = (
                supabase.table("challenges")
                .select("*")
                .eq("challenge_id", challenge_id)
                .execute()
            )
            if response.data:
                challenge = Challenge.from_dict(response.data[0])
                # Cache for future use
                self.challenge_cache[challenge_id] = challenge
                return challenge
            return None
        except Exception as e:
            logger.error(f"Error getting challenge {challenge_id} from DB: {e}")
            return None

    def add_challenge(self, challenge: Challenge) -> None:
        """Add a challenge to the cache."""
        self.challenge_cache[challenge.challenge_id] = challenge

    def get_live_matches(self) -> List[Match]:
        """Get all live (in-progress) matches from memory."""
        return list(self.live_matches.values())

    def get_recent_matches(self, limit: int = 10) -> List[Match]:
        """Get recent matches, sorted by start time."""
        completed_matches = [
            m
            for m in self.matches.values()
            if m.status not in [MatchStatus.IN_PROGRESS, MatchStatus.PENDING]
        ]
        sorted_matches = sorted(
            completed_matches,
            key=lambda m: (
                m.started_at.replace(tzinfo=None)
                if m.started_at and m.started_at.tzinfo
                else m.started_at
            )
            or datetime.min,
            reverse=True,
        )
        return sorted_matches[:limit]

    def get_matches_for_agent(self, agent_id: str) -> List[Match]:
        """Get all matches for a specific agent from memory."""
        # First try in-memory cache
        agent_matches = [
            m for m in self.matches.values() if agent_id in [m.agent1_id, m.agent2_id]
        ]

        # If we have matches in memory, return them
        if agent_matches:
            # Sort matches, handling potential timezone issues
            try:
                return sorted(
                    agent_matches,
                    key=lambda m: (
                        m.created_at.replace(tzinfo=None)
                        if m.created_at and m.created_at.tzinfo
                        else m.created_at
                    )
                    or datetime.min,
                    reverse=True,
                )
            except Exception as e:
                logger.error(f"Error sorting agent matches: {e}")
                # Fallback sorting method
                return agent_matches

        # Otherwise, query the database
        try:
            # Query for matches where agent is either agent1_id or agent2_id
            response = (
                supabase.table("matches")
                .select("*")
                .eq("agent1_id", agent_id)
                .execute()
            )

            # Get matches where agent is agent2_id
            response2 = (
                supabase.table("matches")
                .select("*")
                .eq("agent2_id", agent_id)
                .execute()
            )

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
                    key=lambda m: (
                        m.created_at.replace(tzinfo=None)
                        if m.created_at and m.created_at.tzinfo
                        else m.created_at
                    )
                    or datetime.min,
                    reverse=True,
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
                match_dict = match.model_dump(mode="json")
                # Ensure enums are stored as strings
                match_dict["status"] = match.status.value
                match_dict["match_type"] = match.match_type.value
                if match.division:
                    match_dict["division"] = (
                        match.division
                        if isinstance(match.division, str)
                        else match.division.value
                    )

                # Update or insert
                supabase.table("matches").upsert(match_dict).execute()

            logger.info(f"Synced {len(self.matches)} matches to database")
        except Exception as e:
            logger.error(f"Error syncing matches to database: {e}")

    def has_reached_live_match_limit(self) -> bool:
        """Check if the number of live matches has reached the configured limit.

        Returns:
            bool: True if the limit has been reached, False otherwise
        """
        return len(self.live_matches) >= self.max_live_matches
