import json
import os
import random
import time
import asyncio
from typing import List, Dict, Optional, Tuple
import threading

from agent_arena.models.agent import Agent, AgentProfile, Division, AgentStats
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.models.match import Match, MatchType, AgentResponse, MatchStatus
from agent_arena.core.llm_interface import (
    create_agent_llm,
    get_content,
    create_system_llm,
)
from agent_arena.core.challenge_generator import ChallengeGenerator
from agent_arena.core.judge_system import evaluate_match_with_llm_judges
from agent_arena.core.match_store import MatchStore
from agent_arena.utils.logging import arena_logger, get_logger
from agent_arena.db import supabase
from agent_arena.models.agent import EloHistoryEntry

logger = get_logger(__name__)

MAX_STREAMING_FAILURES = 1
MAX_STREAMING_FAILURE_RATE = 50.0


class Arena:
    def __init__(self):
        self.agents: List[Agent] = []
        self.agent_llms: Dict[str, any] = {}
        # Initialize match store with a file in the same directory as state_file
        self.match_store = MatchStore()  # Will be updated later
        self._initialize_from_db()
        logger.info("Arena initialized from database")

    def _initialize_from_db(self):
        """Initializes the arena state from the database."""
        self.load_agents_from_db()

    def load_agent_configs_from_db(self):
        """Load agent configurations from the database."""
        try:
            logger.info("Loading agent configurations from database")
            response = supabase.table("agent_configs").select("*").execute()
            self.agent_configs = {config["name"]: config for config in response.data}
            logger.info(
                f"Loaded {len(self.agent_configs)} agent configurations from database"
            )

        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}", exc_info=True)

    def start_match_async(
        self, agent1: Agent, agent2: Agent, challenge: Challenge
    ) -> Match:
        """Start a match asynchronously and return immediately."""
        match = Match(
            match_type=(
                MatchType.DEBATE
                if challenge.challenge_type == ChallengeType.DEBATE
                else MatchType.REGULAR_DUEL
            ),
            challenge_id=challenge.challenge_id,
            agent1_id=agent1.profile.name,  # Use name instead of UUID
            agent2_id=agent2.profile.name,  # Use name instead of UUID
            division=agent1.division.value,
        )
        match.start_match()
        # Cache the challenge when adding the match
        self.match_store.add_match(match, challenge)

        # Run the match in a background thread
        def run_match():
            try:
                if challenge.challenge_type == ChallengeType.DEBATE:
                    self.simulate_debate_match(agent1, agent2, challenge)
                else:
                    self.simulate_realistic_match(agent1, agent2, challenge)
            except Exception as e:
                logger.error(f"Error in background match: {e}")
                # In case of error, mark the match as cancelled
                match.status = MatchStatus.CANCELLED
                self.match_store.update_match(match)

        thread = threading.Thread(target=run_match)
        thread.daemon = True  # Make thread daemon so it doesn't block program exit
        thread.start()

        return match

    def start_quick_match(self, division: str, agent1_id: str = None, agent2_id: str = None) -> Match:
        """Start a quick match between agents in a division (random or specific selection)."""
        # Check if we've reached the maximum number of live matches
        if self.match_store.has_reached_live_match_limit():
            raise ValueError(
                f"Maximum number of live matches ({self.match_store.max_live_matches}) reached. Please wait for some matches to complete."
            )

        # Get active agents in the division
        division_agents = [
            agent
            for agent in self.agents
            if agent.division.value.lower() == division.lower()
            and agent.profile.is_active
        ]

        if len(division_agents) < 2:
            raise ValueError(f"Not enough active agents in {division} division")

        # Agent selection logic
        if agent1_id and agent2_id:
            # Manual selection: find specific agents
            agent1 = None
            agent2 = None
            
            for agent in division_agents:
                if agent.profile.name == agent1_id:
                    agent1 = agent
                elif agent.profile.name == agent2_id:
                    agent2 = agent
            
            if not agent1:
                raise ValueError(f"Agent '{agent1_id}' not found in {division} division or not active")
            if not agent2:
                raise ValueError(f"Agent '{agent2_id}' not found in {division} division or not active")
            if agent1_id == agent2_id:
                raise ValueError("Cannot start a match between the same agent")
                
        else:
            # Random selection (default behavior)
            agent1, agent2 = random.sample(division_agents, 2)

        # Select appropriate challenge directly from the database
        if division.lower() == Division.NOVICE.value:
            challenge = self.get_random_challenge_from_db(difficulty_max=2)
        elif division.lower() == Division.EXPERT.value:
            challenge = self.get_random_challenge_from_db(difficulty_max=3)
        else:
            challenge = self.get_random_challenge_from_db(difficulty_min=3)

        # Fall back: If no challenges found, create a new one
        if not challenge:
            logger.warning("No challenges available, generating a new one")
            generator = ChallengeGenerator(
                agents=self.agents, agent_llms=self.agent_llms
            )
            if division.lower() == Division.NOVICE.value:
                challenge = generator.generate_challenge(
                    ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.BEGINNER
                )
            elif division.lower() == Division.EXPERT.value:
                challenge = generator.generate_challenge(
                    ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.INTERMEDIATE
                )
            else:
                challenge = generator.generate_challenge(
                    ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.ADVANCED
                )

        # Start match asynchronously
        return self.start_match_async(agent1, agent2, challenge)

    def load_agents_from_db(self):
        """Loads agents from the Supabase database."""
        try:
            response = supabase.table("agents").select("*").execute()
            if not response.data:
                logger.info(
                    "No agents found in the database. Seeding from agent configs..."
                )
                self.seed_agents_from_config()
                # Retry loading after seeding
                response = supabase.table("agents").select("*").execute()

            agents_data = response.data

            for agent_data in agents_data:
                # Reconstruct Agent Pydantic model from DB data
                profile_data = {
                    "agent_id": agent_data["id"],
                    "name": agent_data["name"],
                    "description": agent_data["description"],
                    "specializations": agent_data["specializations"],
                    "model": agent_data["model"],
                    "temperature": agent_data["temperature"],
                    "created_at": agent_data["created_at"],
                    "last_active": agent_data["last_active"],
                    "is_active": agent_data["is_active"],
                    "supports_structured_output": agent_data.get(
                        "supports_structured_output", False
                    ),
                    "metadata": agent_data.get("metadata") or {},
                }

                # Handle migration from old stats structure to new division-specific stats
                if "current_division_stats" in agent_data:
                    # New format - use as is
                    stats_data = {
                        key: agent_data[key]
                        for key in [
                            "elo_rating",
                            "current_division_stats",
                            "career_stats",
                            "division_history",
                            "consistency_score",
                            "innovation_index",
                            "challenges_created",
                            "challenge_quality_avg",
                            "judge_accuracy",
                            "judge_reliability",
                        ]
                        if key in agent_data
                    }

                agent = Agent(
                    profile=AgentProfile(**profile_data),
                    division=Division(agent_data["current_division"]),
                    stats=AgentStats(**stats_data),
                    # match_history, challenge_history, and division_change_history would need to be loaded if stored
                    division_change_history=agent_data.get("division_change_history")
                    or [],
                )

                # Load ELO history from the elo_history table
                try:
                    elo_history_response = (
                        supabase.table("elo_history")
                        .select("*")
                        .eq("agent_id", agent.profile.name)
                        .order("timestamp", desc=False)
                        .execute()
                    )

                    if elo_history_response.data:
                        # Start with base rating and reconstruct historical ratings
                        historical_rating = 1200.0  # Base ELO rating

                        for entry in elo_history_response.data:
                            # Get the rating change from this match
                            rating_change = entry.get("rating_change", 0.0)

                            # Calculate the rating after this match
                            historical_rating += rating_change

                            elo_entry = EloHistoryEntry(
                                timestamp=entry.get("timestamp"),
                                rating=historical_rating,  # Use calculated historical rating
                                match_id=entry.get("match_id"),
                                opponent_id=entry.get("opponent_id"),
                                opponent_rating=entry.get("opponent_elo", 1200.0),
                                result=entry.get("result"),
                                rating_change=rating_change,
                            )
                            agent.stats.elo_history.append(elo_entry)

                        # Verify that the final calculated rating matches the current rating
                        if abs(historical_rating - agent.stats.elo_rating) > 0.01:
                            logger.warning(
                                f"Calculated historical rating ({historical_rating:.1f}) doesn't match "
                                f"current rating ({agent.stats.elo_rating:.1f}) for agent {agent.profile.name}. "
                                f"There may be missing entries in the ELO history."
                            )
                except Exception as e:
                    logger.error(
                        f"Error loading ELO history for agent {agent.profile.name}: {e}",
                        exc_info=True,
                    )

                self.agents.append(agent)

                # Create LLM for the agent using data from agent profile
                try:
                    agent_llm = create_agent_llm(
                        model_name=agent.profile.model,
                        temperature=agent.profile.temperature,
                        max_tokens=1500,
                    )
                    self.agent_llms[agent.profile.agent_id] = agent_llm
                except Exception as e:
                    logger.warning(
                        f"Failed to create LLM for agent {agent.profile.name}: {e}"
                    )

            logger.info(f"Loaded {len(self.agents)} agents from the database.")
        except Exception as e:
            logger.error(f"Error loading agents from database: {e}")
            raise

    def seed_agents_from_config(self):
        """Seeds the database with agents from the agent configurations."""
        try:
            # Use configs from database instead of file
            if not self.agent_configs:
                logger.warning("No agent configurations available for seeding agents")
                return

            agents_to_insert = []
            for name, config in self.agent_configs.items():
                agent_data = {
                    "name": config["name"],
                    "model": config["model"],
                    "temperature": config.get("temperature", 0.5),
                    "description": f"Agent based on {config['model']}",
                    "specializations": config.get("specializations", []),
                    "current_division": config["division"].lower(),
                }
                agents_to_insert.append(agent_data)

            if agents_to_insert:
                supabase.table("agents").insert(agents_to_insert).execute()
                logger.info(
                    f"Successfully seeded {len(agents_to_insert)} agents to the database."
                )

        except Exception as e:
            logger.error(f"Error seeding agents from config: {e}")
            raise

    def update_agent_in_db(self, agent: Agent):
        """Updates an agent's state in the database."""
        try:
            agent_data = agent.model_dump(mode="json")
            profile_data = agent_data["profile"]
            stats_data = agent_data["stats"]

            # Remove elo_history from stats_data to avoid schema mismatch
            if "elo_history" in stats_data:
                del stats_data["elo_history"]

            update_data = {
                "description": profile_data["description"],
                "specializations": profile_data["specializations"],
                "model": profile_data["model"],
                "temperature": profile_data["temperature"],
                "last_active": profile_data["last_active"],
                "is_active": profile_data["is_active"],
                "supports_structured_output": profile_data[
                    "supports_structured_output"
                ],
                "metadata": profile_data["metadata"],
                "current_division": agent.division.value,
                "division_change_history": agent_data["division_change_history"],
                # New stats structure
                "current_division_stats": stats_data.get("current_division_stats"),
                "career_stats": stats_data.get("career_stats"),
                "division_history": stats_data.get("division_history"),
                # Legacy stats for backward compatibility (computed from current division)
                "total_matches": agent.stats.total_matches,
                "wins": agent.stats.wins,
                "losses": agent.stats.losses,
                "draws": agent.stats.draws,
                "current_streak": agent.stats.current_streak,
                "best_streak": agent.stats.best_streak,
                # Other stats
                "elo_rating": stats_data.get("elo_rating"),
                "consistency_score": stats_data.get("consistency_score"),
                "innovation_index": stats_data.get("innovation_index"),
                "challenges_created": stats_data.get("challenges_created"),
                "challenge_quality_avg": stats_data.get("challenge_quality_avg"),
                "judge_accuracy": stats_data.get("judge_accuracy"),
                "judge_reliability": stats_data.get("judge_reliability"),
            }

            supabase.table("agents").update(update_data).eq(
                "id", agent.profile.agent_id
            ).execute()
        except Exception as e:
            logger.error(f"Error updating agent {agent.profile.name} in DB: {e}")

    def save_state(self):
        """Saves the current state of all agents to the database."""
        print("Saving arena state to database...")
        try:
            for agent in self.agents:
                self.update_agent_in_db(agent)

            # Challenges are currently in-memory, but could be saved too
            # For now, we only save agents.

            print("Arena state saved successfully to database.")
        except Exception as e:
            logger.error(f"Error saving arena state to database: {e}")
            raise

    def reload_from_db(self) -> Dict[str, int]:
        """Reloads agents and challenges from the database.

        This method should be called when changes are made directly to the database
        and need to be reflected in the running application.

        Returns:
            A dictionary with counts of loaded entities
        """
        logger.info("Reloading arena state from database...")

        # Check if there are any active matches that could be affected
        active_matches = self.match_store.get_live_matches()
        if active_matches:
            logger.warning(
                f"Reloading with {len(active_matches)} active matches. This could cause inconsistencies."
            )

        # Clear existing agents
        old_agents = {agent.profile.name: agent for agent in self.agents}
        self.agents = []

        # Reload agents from DB
        self.load_agents_from_db()

        # No need to reload challenges as they're fetched on demand
        old_challenge_count = len(self.match_store.challenge_cache)

        # Reinitialize the match store to reload matches from DB
        old_match_store = self.match_store
        old_match_count = len(old_match_store.matches)
        old_live_match_count = len(old_match_store.live_matches)

        # Create a new match store instance which will load from DB
        self.match_store = MatchStore()
        new_match_count = len(self.match_store.matches)
        new_live_match_count = len(self.match_store.live_matches)

        # Count changes for reporting
        new_agents = set(agent.profile.name for agent in self.agents)
        old_agent_names = set(old_agents.keys())

        added_agents = new_agents - old_agent_names
        removed_agents = old_agent_names - new_agents
        updated_agents = new_agents.intersection(old_agent_names)

        result = {
            "agents_loaded": len(self.agents),
            "challenge_cache_before": old_challenge_count,
            "challenge_cache_after": len(self.match_store.challenge_cache),
            "agents_added": len(added_agents),
            "agents_removed": len(removed_agents),
            "agents_updated": len(updated_agents),
            "matches_before": old_match_count,
            "matches_after": new_match_count,
            "live_matches_before": old_live_match_count,
            "live_matches_after": new_live_match_count,
        }

        logger.info(f"Arena reload complete: {result}")
        return result

    def simulate_realistic_match(
        self, agent1: Agent, agent2: Agent, challenge: Challenge
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """Simulate a complete match with real LLM responses and evaluation."""
        try:
            # Find the existing match for these agents and challenge
            match = next(
                (
                    m
                    for m in self.match_store.get_live_matches()
                    if m.agent1_id == agent1.profile.name
                    and m.agent2_id == agent2.profile.name
                    and m.challenge_id == challenge.challenge_id
                ),
                None,
            )

            if not match:
                print(
                    f"      ❌ No active match found for {agent1.profile.name} vs {agent2.profile.name}"
                )
                return None, {}

            prompt = challenge.get_prompt()

            print(f"      🤖 Streaming real LLM responses in parallel...")

            # Run both agents in parallel using asyncio
            import asyncio

            async def stream_agent_response(agent: Agent, agent_num: int):
                """Stream a single agent's response."""
                agent_llm = self.agent_llms[agent.profile.agent_id]
                start_time = time.time()
                response_chunks = []

                # Record this streaming attempt
                agent.stats.streaming_attempts += 1

                try:
                    async for chunk in agent_llm.astream(prompt):
                        chunk_content = get_content(chunk)
                        response_chunks.append(chunk_content)

                        # Create partial response and update match in real-time
                        partial_response_text = "".join(response_chunks)
                        partial_response = AgentResponse(
                            agent_id=agent.profile.name,
                            response_text=partial_response_text,
                            response_time=time.time() - start_time,
                            is_streaming=True,
                        )

                        # Update match with partial response
                        match.submit_partial_response(
                            agent.profile.name, partial_response
                        )
                        self.match_store.update_match(match)

                    response_time = time.time() - start_time
                    final_response_text = "".join(response_chunks)

                    # Mark agent response as complete
                    final_response = AgentResponse(
                        agent_id=agent.profile.name,
                        response_text=final_response_text,
                        response_time=response_time,
                        is_streaming=False,
                    )
                    match.submit_response(agent.profile.name, final_response)

                    # Update match with correct streaming status
                    self.match_store.update_match(match)

                    print(
                        f"      ✅ {agent.profile.name} finished streaming ({response_time:.1f}s)"
                    )
                    return final_response_text, response_time

                except Exception as e:
                    print(f"      ❌ Error streaming {agent.profile.name}: {e}")
                    # Record this as a failed attempt
                    agent.stats.streaming_failures += 1
                    failure_rate = (
                        agent.stats.streaming_failures / agent.stats.streaming_attempts
                    )
                    # Check if the agent should be deactivated due to high failure rate
                    print(
                        f"      ❌ {agent.profile.name} failed streaming {agent.stats.streaming_failures} times out of {agent.stats.streaming_attempts} attempts"
                    )
                    if (
                        agent.stats.streaming_failures >= MAX_STREAMING_FAILURES
                        and failure_rate > MAX_STREAMING_FAILURE_RATE
                    ):
                        reason = f"Deactivated due to high failure rate ({failure_rate:.1f}% over {agent.stats.streaming_attempts} attempts)"
                        print(
                            f"      🚫 Deactivating agent {agent.profile.name}: {reason}"
                        )
                        agent.deactivate(reason=reason)
                        # Update the agent in the database
                        self.update_agent_in_db(agent)

                    # Fallback response
                    fallback_text = (
                        f"Error occurred while generating response: {str(e)}"
                    )
                    fallback_response = AgentResponse(
                        agent_id=agent.profile.name,
                        response_text=fallback_text,
                        response_time=time.time() - start_time,
                        is_streaming=False,
                    )
                    match.submit_response(agent.profile.name, fallback_response)
                    # Update match with correct streaming status
                    self.match_store.update_match(match)

                    return fallback_text, time.time() - start_time

            # Create event loop if it doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run both agents in parallel
            agent1_task = stream_agent_response(agent1, 1)
            agent2_task = stream_agent_response(agent2, 2)

            # Wait for both to complete
            results = loop.run_until_complete(asyncio.gather(agent1_task, agent2_task))
            (response1_text, response1_time), (response2_text, response2_time) = results
            match.status = MatchStatus.AWAITING_JUDGMENT
            # Now that both agents have completed, update the match in the database
            self.match_store.update_match(match)

            print(
                f"      🏁 Both agents completed! Agent1: {response1_time:.1f}s, Agent2: {response2_time:.1f}s"
            )

            print(f"      ⚖️  Evaluating with real LLM judges...")
            evaluation_result = evaluate_match_with_llm_judges(
                match,
                challenge,
                judge_count=2,
                agents=self.agents,
                agent_llms=self.agent_llms,
            )

            winner_agent_num = evaluation_result.get("winner")
            final_score_agent1 = evaluation_result.get("agent1_avg", 5.0)
            final_score_agent2 = evaluation_result.get("agent2_avg", 5.0)

            if winner_agent_num == "agent1":
                winner_id = agent1.profile.name
            elif winner_agent_num == "agent2":
                winner_id = agent2.profile.name
            else:
                winner_id = None

            scores = {
                agent1.profile.name: final_score_agent1,
                agent2.profile.name: final_score_agent2,
            }

            # Store evaluation details in the match
            if "evaluation_details" in evaluation_result:
                match.evaluation_details = evaluation_result["evaluation_details"]

            # Update match with results
            match.complete_match(winner_id, scores)
            self.match_store.update_match(match)

            # Update agent stats with match ID
            print("update_agent_stats_and_elo realistic match")
            self.update_agent_stats_and_elo(
                agent1, agent2, winner_id, scores, match_id=match.match_id
            )

            # Apply division changes after each match
            self.apply_realistic_division_changes()

            return winner_id, scores
        except Exception as e:
            logger.error(f"      ❌ Match simulation failed: {e}", exc_info=True)
            winner_id = random.choice([agent1.profile.name, agent2.profile.name])
            scores = {agent1.profile.name: 6.0, agent2.profile.name: 5.5}
            match.complete_match(winner_id, scores)
            self.match_store.update_match(match)
            # Update agent stats even on failure
            self.update_agent_stats_and_elo(
                agent1, agent2, winner_id, scores, match_id=match.match_id
            )

            # Apply division changes even on failure
            self.apply_realistic_division_changes()

            return winner_id, scores

    def simulate_debate_match(
        self, agent1: Agent, agent2: Agent, challenge: Challenge, num_turns: int = 3
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """Simulate a complete debate match."""
        stances = ["for", "against"]
        random.shuffle(stances)
        agent1_stance, agent2_stance = stances

        # Find the existing match for these agents and challenge
        match = next(
            (
                m
                for m in self.match_store.get_live_matches()
                if m.agent1_id == agent1.profile.name
                and m.agent2_id == agent2.profile.name
                and m.challenge_id == challenge.challenge_id
            ),
            None,
        )

        if not match:
            print(
                f"      ❌ No active match found for {agent1.profile.name} vs {agent2.profile.name}"
            )
            return None, {}

        print(f"      Debate Topic: {challenge.title}")
        print(f"      {agent1.profile.name} will argue: {agent1_stance.upper()}")
        print(f"      {agent2.profile.name} will argue: {agent2_stance.upper()}")

        current_transcript = []
        for i in range(num_turns * 2):
            print(f"      Turn {i+1} of {num_turns*2}")
            is_agent1_turn = i % 2 == 0
            agent_to_respond = agent1 if is_agent1_turn else agent2
            opponent_agent = agent2 if is_agent1_turn else agent1
            agent_stance = agent1_stance if is_agent1_turn else agent2_stance
            opponent_stance = agent2_stance if is_agent1_turn else agent1_stance

            prompt = f"Debate Topic: {challenge.description}\n\n"
            prompt += f"You are arguing the '{agent_stance}' position. Your opponent is arguing the '{opponent_stance}' position.\n"
            if current_transcript:
                prompt += "\n--- Debate History ---\n"
                for turn in current_transcript:
                    prompt += f"{turn['agent_name']}: {turn['response_text']}\n"
                prompt += "\n--- Your Turn ---\n"
                prompt += "Provide your rebuttal or next argument."
            else:
                prompt += "Provide your opening statement."

            agent_llm = self.agent_llms[agent_to_respond.profile.agent_id]
            # Record this streaming attempt
            agent_to_respond.stats.streaming_attempts += 1
            try:
                start_time = time.time()
                response_chunks = []

                # Stream the response chunk by chunk
                for chunk in agent_llm.stream(prompt):
                    chunk_content = get_content(chunk)
                    response_chunks.append(chunk_content)

                    # Create partial response and update match in memory
                    partial_response_text = "".join(response_chunks)
                    partial_response = AgentResponse(
                        agent_id=agent_to_respond.profile.name,
                        response_text=partial_response_text,
                        response_time=time.time() - start_time,
                        is_streaming=True,
                    )

                    # Update transcript with partial response (replace last entry if it's partial)
                    if (
                        match.transcript
                        and match.transcript[-1].agent_id
                        == agent_to_respond.profile.name
                        and hasattr(match.transcript[-1], "is_streaming")
                        and match.transcript[-1].is_streaming
                    ):
                        match.transcript[-1] = partial_response
                    else:
                        match.transcript.append(partial_response)

                    self.match_store.update_match(match)

                # Final complete response
                response_text = "".join(response_chunks)
                response_time = time.time() - start_time

            except Exception as e:
                print(
                    f"      ❌ Error getting response from {agent_to_respond.profile.name}: {e}"
                )

                # Record this as a failed attempt
                agent_to_respond.stats.streaming_failures += 1
                failure_rate = (
                    (
                        agent_to_respond.stats.streaming_failures
                        / agent_to_respond.stats.streaming_attempts
                    )
                    * 100.0
                    if agent_to_respond.stats.streaming_attempts > 0
                    else 0
                )

                print(
                    f"      ❌ {agent_to_respond.profile.name} failed streaming {agent_to_respond.stats.streaming_failures} times out of {agent_to_respond.stats.streaming_attempts} attempts. Failure rate: {failure_rate:.1f}%"
                )

                # Check if the agent should be deactivated due to high failure rate
                if (
                    agent_to_respond.stats.streaming_failures >= MAX_STREAMING_FAILURES
                    and failure_rate > MAX_STREAMING_FAILURE_RATE
                ):
                    reason = f"Deactivated due to high failure rate ({failure_rate:.1f}% over {agent_to_respond.stats.streaming_attempts} attempts)"
                    print(
                        f"      🚫 Deactivating agent {agent_to_respond.profile.name}: {reason}"
                    )
                    agent_to_respond.deactivate(reason=reason)
                    # Update the agent in the database
                    self.update_agent_in_db(agent_to_respond)

                print(
                    f"      {opponent_agent.profile.name} wins by default as their opponent failed to respond."
                )
                winner_id = opponent_agent.profile.name
                scores = {
                    opponent_agent.profile.name: 8.0,
                    agent_to_respond.profile.name: 2.0,
                }
                match.complete_match(winner_id, scores)
                self.match_store.update_match(match)
                return winner_id, scores

            current_transcript.append(
                {
                    "agent_name": agent_to_respond.profile.name,
                    "response_text": response_text,
                }
            )

            # Create final response (not streaming)
            response = AgentResponse(
                agent_id=agent_to_respond.profile.name,
                response_text=response_text,
                response_time=response_time,
                is_streaming=False,
            )

            # Replace the last partial response with the complete one
            if (
                match.transcript
                and match.transcript[-1].agent_id == agent_to_respond.profile.name
            ):
                match.transcript[-1] = response
            else:
                match.transcript.append(response)

            # Update database after each complete turn
            self.match_store.update_match(match)

        # After all turns, set status to awaiting judgment
        match.status = MatchStatus.AWAITING_JUDGMENT
        self.match_store.update_match(match)

        print(f"      ⚖️  Evaluating debate with real LLM judges...")
        evaluation_result = evaluate_match_with_llm_judges(
            match,
            challenge,
            judge_count=2,
            agents=self.agents,
            agent_llms=self.agent_llms,
        )
        winner_agent_num = evaluation_result.get("winner")
        if winner_agent_num == "agent1":
            winner_id = agent1.profile.name
        elif winner_agent_num == "agent2":
            winner_id = agent2.profile.name
        else:
            winner_id = None

        scores = {
            agent1.profile.name: evaluation_result.get("agent1_avg", 5.0),
            agent2.profile.name: evaluation_result.get("agent2_avg", 5.0),
        }

        # Store evaluation details in the match
        if "evaluation_details" in evaluation_result:
            match.evaluation_details = evaluation_result["evaluation_details"]

        match.complete_match(winner_id, scores)
        self.match_store.update_match(match)
        print("update_agent_stats_and_elo debate match")
        self.update_agent_stats_and_elo(
            agent1, agent2, winner_id, scores, match_id=match.match_id
        )

        # Apply division changes after each match
        self.apply_realistic_division_changes()

        return winner_id, scores

    def update_agent_stats_and_elo(
        self,
        agent1: Agent,
        agent2: Agent,
        winner_id: Optional[str],
        scores: Dict[str, float],
        match_id: str,
    ):
        """Update agent statistics and ELO ratings after a match."""
        print(
            "Updating agent stats and ELO for",
            agent1.profile.name,
            "and",
            agent2.profile.name,
        )

        # Find the actual agents in self.agents
        arena_agent1 = next(
            a for a in self.agents if a.profile.name == agent1.profile.name
        )
        arena_agent2 = next(
            a for a in self.agents if a.profile.name == agent2.profile.name
        )

        # Add match to both agents' history
        arena_agent1.add_match(match_id)
        arena_agent2.add_match(match_id)

        k_factor = 32
        agent1_elo = arena_agent1.stats.elo_rating
        agent2_elo = arena_agent2.stats.elo_rating
        expected1 = 1 / (1 + 10 ** ((agent2_elo - agent1_elo) / 400))
        expected2 = 1 / (1 + 10 ** ((agent1_elo - agent2_elo) / 400))

        if winner_id == arena_agent1.profile.name:
            actual1, actual2 = 1, 0
            result1, result2 = "win", "loss"
        elif winner_id == arena_agent2.profile.name:
            actual1, actual2 = 0, 1
            result1, result2 = "loss", "win"
        else:
            actual1, actual2 = 0.5, 0.5
            result1 = result2 = "draw"

        # Calculate ELO changes
        rating_change1 = k_factor * (actual1 - expected1)
        rating_change2 = k_factor * (actual2 - expected2)
        new_rating1 = arena_agent1.stats.elo_rating + rating_change1
        new_rating2 = arena_agent2.stats.elo_rating + rating_change2

        # Update ELO ratings and record history (this also updates match stats)
        arena_agent1.update_elo(
            new_rating=new_rating1,
            match_id=match_id,
            opponent_id=arena_agent2.profile.name,
            opponent_rating=agent2_elo,
            result=result1,
            rating_change=rating_change1,
        )
        arena_agent2.update_elo(
            new_rating=new_rating2,
            match_id=match_id,
            opponent_id=arena_agent1.profile.name,
            opponent_rating=agent1_elo,
            result=result2,
            rating_change=rating_change2,
        )

        arena_agent1.stats.streaming_attempts = agent1.stats.streaming_attempts
        arena_agent1.stats.streaming_failures = agent1.stats.streaming_failures
        arena_agent2.stats.streaming_attempts = agent2.stats.streaming_attempts
        arena_agent2.stats.streaming_failures = agent2.stats.streaming_failures

        # Update agents in the database
        self.update_agent_in_db(arena_agent1)
        self.update_agent_in_db(arena_agent2)

        print(
            "Updated ELO ratings and saved to DB:",
            f"{arena_agent1.profile.name}: {arena_agent1.stats.elo_rating:.0f}",
            f"{arena_agent2.profile.name}: {arena_agent2.stats.elo_rating:.0f}",
        )

        self.save_state()

    def apply_realistic_division_changes(self, context: str = "match"):
        """Apply promotion and demotion rules based on performance metrics."""
        changes = []
        eligible_challengers = []

        for agent in self.agents:
            # Use current division stats for promotion/demotion decisions
            current_stats = agent.stats.current_division_stats
            win_rate = current_stats.win_rate
            streak = current_stats.current_streak
            matches = current_stats.matches
            elo = agent.stats.elo_rating

            # Promotion logic - minimum 5 matches in current division
            if matches >= 5:
                if agent.division == Division.NOVICE and (
                    win_rate >= 60 or streak >= 3
                ):
                    agent.promote_division(
                        Division.EXPERT,
                        f"Promoted with {win_rate:.1f}% win rate in Novice division ({matches} matches, {elo:.0f} ELO)",
                    )
                    self.update_agent_in_db(agent)
                    changes.append(
                        f"🔺 {agent.profile.name}: NOVICE → EXPERT (Division stats: {win_rate:.1f}% WR, {matches} matches)"
                    )
                elif agent.division == Division.EXPERT and (
                    win_rate >= 70 or streak >= 4
                ):
                    agent.promote_division(
                        Division.MASTER,
                        f"Promoted with {win_rate:.1f}% win rate in Expert division ({matches} matches, {elo:.0f} ELO)",
                    )
                    self.update_agent_in_db(agent)
                    changes.append(
                        f"🔺 {agent.profile.name}: EXPERT → MASTER (Division stats: {win_rate:.1f}% WR, {matches} matches)"
                    )
                elif agent.division == Division.MASTER and (
                    win_rate >= 75 or streak >= 5
                ):
                    # Check if there's already a King
                    current_kings = [
                        a
                        for a in self.agents
                        if a.division == Division.KING and a.profile.is_active
                    ]
                    if not current_kings:
                        # No current King, so promote this Master to King
                        agent.promote_division(
                            Division.KING,
                            f"Crowned with {win_rate:.1f}% win rate in Master division ({matches} matches, {elo:.0f} ELO)",
                        )
                        self.update_agent_in_db(agent)
                        changes.append(
                            f"👑 {agent.profile.name}: MASTER → KING (CROWNED! Division stats: {win_rate:.1f}% WR, {matches} matches)"
                        )
                    else:
                        # There's already a King, so this Master is now eligible to challenge
                        king = current_kings[0]
                        logger.info(
                            f"{agent.profile.name} qualifies for King promotion but must challenge {king.profile.name} for the crown"
                        )
                        changes.append(
                            f"⚔️  {agent.profile.name} is now ELIGIBLE TO CHALLENGE THE KING! (Division stats: {win_rate:.1f}% WR, {matches} matches)"
                        )
                        # Add to eligible challengers list
                        eligible_challengers.append(agent)
                        # We don't automatically start a challenge here - that's done through the king-challenge endpoint

            # Demotion logic - minimum 5 matches in current division
            if matches >= 5:
                if agent.division == Division.KING and (win_rate <= 40 or streak <= -3):
                    agent.demote_division(
                        Division.MASTER,
                        f"Dethroned with {win_rate:.1f}% win rate in King division ({matches} matches, {elo:.0f} ELO)",
                    )
                    self.update_agent_in_db(agent)
                    changes.append(
                        f"🔻 {agent.profile.name}: KING → MASTER (DETHRONED! Division stats: {win_rate:.1f}% WR, {matches} matches)"
                    )
                elif agent.division == Division.MASTER and (
                    win_rate <= 35 or streak <= -4
                ):
                    agent.demote_division(
                        Division.EXPERT,
                        f"Demoted with {win_rate:.1f}% win rate in Master division ({matches} matches, {elo:.0f} ELO)",
                    )
                    self.update_agent_in_db(agent)
                    changes.append(
                        f"🔻 {agent.profile.name}: MASTER → EXPERT (Division stats: {win_rate:.1f}% WR, {matches} matches)"
                    )
                elif agent.division == Division.EXPERT and (
                    win_rate <= 30 or streak <= -4
                ):
                    agent.demote_division(
                        Division.NOVICE,
                        f"Demoted with {win_rate:.1f}% win rate in Expert division ({matches} matches, {elo:.0f} ELO)",
                    )
                    self.update_agent_in_db(agent)
                    changes.append(
                        f"🔻 {agent.profile.name}: EXPERT → NOVICE (Division stats: {win_rate:.1f}% WR, {matches} matches)"
                    )

        # Automatically trigger a king challenge if there are eligible challengers
        if (
            eligible_challengers and context != "king_challenge"
        ):  # Prevent infinite recursion
            # Sort challengers by ELO rating to find the best one
            eligible_challengers.sort(key=lambda a: a.stats.elo_rating, reverse=True)
            best_challenger = eligible_challengers[0]

            try:
                # Check if we can start a king challenge (not too many matches already)
                if not self.match_store.has_reached_live_match_limit():
                    # Check if a king challenge is already in progress
                    existing_king_challenges = [
                        m
                        for m in self.match_store.get_live_matches()
                        if m.match_type == MatchType.KING_CHALLENGE
                    ]
                    if not existing_king_challenges:
                        logger.info(
                            f"Automatically starting king challenge for {best_challenger.profile.name}"
                        )
                        self.start_king_challenge()
                        changes.append(
                            f"⚔️  AUTOMATIC KING CHALLENGE: {best_challenger.profile.name} steps forward to challenge the crown!"
                        )
                    else:
                        logger.info(
                            "Cannot start automatic king challenge: another king challenge is already in progress"
                        )
                        changes.append(
                            f"⏳ {best_challenger.profile.name} awaits their chance to challenge the King (another challenge in progress)"
                        )
            except Exception as e:
                logger.error(f"Failed to automatically start king challenge: {e}")

        # Handle King succession if no King exists
        current_kings = [
            a
            for a in self.agents
            if a.division == Division.KING and a.profile.is_active
        ]
        if not current_kings:  # No King exists
            # Find the best Master to promote to King
            masters = [
                a
                for a in self.agents
                if a.division == Division.MASTER and a.profile.is_active
            ]
            if masters:
                masters.sort(key=lambda a: a.stats.elo_rating, reverse=True)
                new_king = masters[0]
                new_king.promote_division(
                    Division.KING,
                    f"Ascended to the throne with {new_king.stats.elo_rating:.0f} ELO",
                )
                self.update_agent_in_db(new_king)
                changes.append(
                    f"👑 {new_king.profile.name}: MASTER → KING (ASCENDED TO THE THRONE! The realm has a new ruler!)"
                )

        if changes:
            print(f"\n🔄 DIVISION CHANGES (after {context}):")
            for change in changes:
                print(f"   {change}")
        elif (
            context == "round"
        ):  # Only show this message for tournament rounds to avoid spam
            print(f"\n📋 No division changes after {context}")

    def create_dynamic_challenge_pool(self, challenge_count: int = 8):
        """Create challenges using real LLM generation and save them to the database."""
        print(
            f"   🎯 Generating {challenge_count} dynamic challenges using real LLMs..."
        )
        generator = ChallengeGenerator(agents=self.agents, agent_llms=self.agent_llms)

        challenge_specs = [
            (ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.BEGINNER),
            (ChallengeType.DEBATE, ChallengeDifficulty.BEGINNER),
            (ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.DEBATE, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.CREATIVE_PROBLEM_SOLVING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.CREATIVE_PROBLEM_SOLVING, ChallengeDifficulty.ADVANCED),
            (ChallengeType.MATHEMATICAL, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.DEBATE, ChallengeDifficulty.ADVANCED),
            (ChallengeType.ABSTRACT_THINKING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.DEBATE, ChallengeDifficulty.EXPERT),
        ]

        new_challenges = []
        for i, (challenge_type, difficulty) in enumerate(
            challenge_specs[:challenge_count]
        ):
            try:
                challenge = generator.generate_challenge(challenge_type, difficulty)
                self.match_store.add_challenge(challenge)
                new_challenges.append(challenge)
                print(
                    f"      ✅ Generated #{i+1}: {challenge.title} ({challenge_type.value}, {difficulty.name})"
                )

            except Exception as e:
                print(f"      ❌ Failed to generate challenge #{i+1}: {e}")
                time.sleep(2)

        if new_challenges:
            try:
                challenges_to_insert = [
                    {
                        "challenge_id": c.challenge_id,
                        "title": c.title,
                        "description": c.description,
                        "challenge_type": c.challenge_type.value,
                        "difficulty": c.difficulty.value,  # Store as integer directly
                        "scoring_rubric": c.scoring_rubric,
                        "tags": c.tags,
                        "source": c.source,
                        "is_active": c.is_active,
                        "metadata": c.metadata,
                        "answer": c.answer,  # Include the answer field
                    }
                    for c in new_challenges
                ]
                supabase.table("challenges").insert(challenges_to_insert).execute()
                logger.info(
                    f"Saved {len(new_challenges)} new challenges to the database."
                )
            except Exception as e:
                logger.error(f"Error saving challenges to database: {e}")

    def get_random_challenge_from_db(
        self,
        difficulty_min: int = None,
        difficulty_max: int = None,
        challenge_type: ChallengeType = None,
    ) -> Optional[Challenge]:
        """Get a random challenge directly from the database based on criteria.

        Args:
            difficulty_min: Minimum difficulty value (inclusive)
            difficulty_max: Maximum difficulty value (inclusive)
            challenge_type: Specific challenge type to filter by

        Returns:
            A randomly selected Challenge object, or None if no matching challenges found
        """
        try:
            # Call the database function with parameters
            challenge_type_value = challenge_type.value if challenge_type else None
            response = supabase.rpc(
                "get_random_challenge",
                {
                    "difficulty_min": difficulty_min,
                    "difficulty_max": difficulty_max,
                    "challenge_type": challenge_type_value,
                },
            ).execute()

            if response.data and len(response.data) > 0:
                return Challenge.from_dict(response.data[0])
            else:
                logger.warning("No matching challenges found in database")
                return None

        except Exception as e:
            logger.error(
                f"Error getting random challenge from database: {e}", exc_info=True
            )
            return None

    def run_tournament(self, num_rounds: int = 5):
        """Runs the entire tournament for a specified number of rounds."""
        print("🏆 ARENA TOURNAMENT STARTED 🏆")
        for round_num in range(1, num_rounds + 1):
            print(f"🏆 REALISTIC TOURNAMENT ROUND {round_num}")
            print("=" * 60)
            self.run_tournament_round(round_num)
            print(f"✅ Round {round_num} completed, now saving state...")
            self.save_state()  # Save state after each round
            print("State saved.")
            print_comprehensive_status(self.agents, round_num)
        print("🎊 ARENA TOURNAMENT COMPLETE 🎊")

    def run_tournament_round(self, round_num: int):
        print(f"\n🏆 REALISTIC TOURNAMENT ROUND {round_num}")
        print("=" * 60)

        # Group active agents by division
        divisions = {}
        for agent in self.agents:
            if not agent.profile.is_active:
                continue  # Skip inactive agents

            if agent.division not in divisions:
                divisions[agent.division] = []
            divisions[agent.division].append(agent)

        match_count = 0
        for division, division_agents in divisions.items():
            if len(division_agents) < 2:
                print(
                    f"\n⚠️ Not enough active agents in {division.value.upper()} division for matches"
                )
                continue

            print(f"\n📊 {division.value.upper()} DIVISION MATCHES:")
            random.shuffle(division_agents)

            # If odd number of agents, the last one will sit out this round
            agents_to_match = (
                division_agents
                if len(division_agents) % 2 == 0
                else division_agents[:-1]
            )

            for i in range(0, len(agents_to_match), 2):
                agent1 = agents_to_match[i]
                agent2 = agents_to_match[i + 1]

                if division == Division.NOVICE:
                    challenge = self.get_random_challenge_from_db(difficulty_max=2)
                elif division == Division.EXPERT:
                    challenge = self.get_random_challenge_from_db(difficulty_max=3)
                else:
                    challenge = self.get_random_challenge_from_db(difficulty_min=3)

                # Fall back to cached challenges if database query failed
                if not challenge and self.match_store.challenge_cache:
                    logger.warning("Falling back to cached challenges")
                    cached_challenges = list(self.match_store.challenge_cache.values())

                    if division == Division.NOVICE:
                        appropriate_challenges = [
                            c for c in cached_challenges if c.difficulty.value <= 2
                        ]
                    elif division == Division.EXPERT:
                        appropriate_challenges = [
                            c for c in cached_challenges if c.difficulty.value <= 3
                        ]
                    else:
                        appropriate_challenges = [
                            c for c in cached_challenges if c.difficulty.value >= 3
                        ]

                    if appropriate_challenges:
                        challenge = random.choice(appropriate_challenges)
                    elif cached_challenges:
                        challenge = random.choice(cached_challenges)

                if not challenge:
                    # If no challenges found, create a new one
                    logger.warning("No challenges available, generating a new one")
                    generator = ChallengeGenerator(
                        agents=self.agents, agent_llms=self.agent_llms
                    )
                    if division == Division.NOVICE:
                        challenge = generator.generate_challenge(
                            ChallengeType.LOGICAL_REASONING,
                            ChallengeDifficulty.BEGINNER,
                        )
                    elif division == Division.EXPERT:
                        challenge = generator.generate_challenge(
                            ChallengeType.LOGICAL_REASONING,
                            ChallengeDifficulty.INTERMEDIATE,
                        )
                    else:
                        challenge = generator.generate_challenge(
                            ChallengeType.LOGICAL_REASONING,
                            ChallengeDifficulty.ADVANCED,
                        )

                    # Cache the new challenge
                    self.match_store.add_challenge(challenge)

                print(
                    f"\n   🥊 Match {match_count + 1}: {agent1.profile.name} vs {agent2.profile.name}"
                )
                print(
                    f"      Challenge: {challenge.title} ({challenge.difficulty.name})"
                )

                start_time = time.time()
                if challenge.challenge_type == ChallengeType.DEBATE:
                    winner_id, scores = self.simulate_debate_match(
                        agent1, agent2, challenge
                    )
                else:
                    winner_id, scores = self.simulate_realistic_match(
                        agent1, agent2, challenge
                    )
                match_duration = time.time() - start_time

                # Note: stats and division changes are already handled inside simulate_*_match methods

                if winner_id:
                    winner_name = (
                        agent1.profile.name
                        if winner_id == agent1.profile.name
                        else agent2.profile.name
                    )
                    print(f"      🏆 Winner: {winner_name}")
                else:
                    print(f"      🤝 Draw")

                print(
                    f"      📊 Scores: {agent1.profile.name}: {scores.get(agent1.profile.name, 0):.1f}, "
                    f"{agent2.profile.name}: {scores.get(agent2.profile.name, 0):.1f}"
                )
                print(f"      ⏱️  Match duration: {match_duration:.1f}s")

                match_count += 1

        print(f"\n✅ Round {round_num} completed: {match_count} realistic matches")
        self.apply_realistic_division_changes(context="round")

    def start_king_challenge(self) -> Match:
        """Start a king challenge match between the current king and the best performing master.

        This allows the top Master division agent to challenge the current King.
        If the challenger wins, they become the new King and the previous King is demoted to Master.

        Returns:
            Match: The created match object

        Raises:
            ValueError: If there's no King or no eligible Master challenger
        """
        # Check if we've reached the maximum number of live matches
        if self.match_store.has_reached_live_match_limit():
            raise ValueError(
                f"Maximum number of live matches ({self.match_store.max_live_matches}) reached. Please wait for some matches to complete."
            )

        # Check if a king challenge is already in progress
        existing_king_challenges = [
            m
            for m in self.match_store.get_live_matches()
            if m.match_type == MatchType.KING_CHALLENGE
        ]
        if existing_king_challenges:
            raise ValueError(
                "A King Challenge is already in progress. Please wait for it to complete before starting another."
            )

        # Find the current king
        kings = [
            agent
            for agent in self.agents
            if agent.division == Division.KING and agent.profile.is_active
        ]
        if not kings:
            raise ValueError(
                "No King to challenge. Run tournaments until a King is crowned."
            )

        king = kings[0]  # There should only be one king

        # Find the best performing Master
        masters = [
            agent
            for agent in self.agents
            if agent.division == Division.MASTER and agent.profile.is_active
        ]
        if not masters:
            raise ValueError(
                "No Master division agents available to challenge the King."
            )

        # Sort masters by ELO rating to find the best challenger
        masters.sort(key=lambda a: a.stats.elo_rating, reverse=True)
        challenger = masters[0]

        print(
            f"👑 KING CHALLENGE: {challenger.profile.name} (Master) challenges {king.profile.name} (King)"
        )

        # Select an advanced challenge for the king match
        challenge = self.get_random_challenge_from_db(difficulty_min=4)

        # Fall back to generating a challenge if none found
        if not challenge:
            logger.warning(
                "No suitable challenge found for King Challenge, generating a new one"
            )
            generator = ChallengeGenerator(
                agents=self.agents, agent_llms=self.agent_llms
            )
            challenge = generator.generate_challenge(
                ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.ADVANCED
            )
            self.match_store.add_challenge(challenge)

        # Create the match with special type
        match = Match(
            match_type=MatchType.KING_CHALLENGE,
            challenge_id=challenge.challenge_id,
            agent1_id=king.profile.name,
            agent2_id=challenger.profile.name,
            division=Division.KING.value,
            stakes={"title": "King of the Hill"},
            special_rules=[
                "King defends the crown",
                "Challenger must win to claim the crown",
            ],
            context="King Challenge Match",
        )

        match.start_match()
        self.match_store.add_match(match, challenge)

        # Run the match in a background thread
        def run_match():
            try:
                winner_id, scores = self.simulate_realistic_match(
                    king, challenger, challenge
                )

                # Handle the outcome of the king challenge
                if winner_id == challenger.profile.name:
                    # Challenger won - they get prestige and ELO boost, but King keeps crown for now
                    print(
                        f"👑 {challenger.profile.name} DEFEATS THE KING {king.profile.name}!"
                    )
                    print(
                        f"   🔥 The challenger has proven their worth! The King's reign is under threat!"
                    )
                    print(
                        f"   📊 Final scores: {challenger.profile.name}: {scores[challenger.profile.name]:.1f}, {king.profile.name}: {scores[king.profile.name]:.1f}"
                    )

                    # The normal ELO and stats updates will happen through update_agent_stats_and_elo
                    # If the King's performance drops consistently, normal demotion rules will handle dethroning

                else:
                    # King successfully defended
                    print(
                        f"👑 {king.profile.name} DEFENDS THE CROWN against {challenger.profile.name}!"
                    )
                    print(f"   ⚔️  The King's reign continues strong!")
                    print(
                        f"   📊 Final scores: {king.profile.name}: {scores[king.profile.name]:.1f}, {challenger.profile.name}: {scores[challenger.profile.name]:.1f}"
                    )

                # Apply division changes with special context to prevent automatic king challenge
                # This will handle any natural promotions/demotions based on sustained performance
                self.apply_realistic_division_changes(context="king_challenge")
                self.save_state()

            except Exception as e:
                logger.error(f"Error in king challenge match: {e}", exc_info=True)
                match.status = MatchStatus.CANCELLED
                self.match_store.update_match(match)

        thread = threading.Thread(target=run_match)
        thread.daemon = True
        thread.start()

        return match


def print_comprehensive_status(agents: List[Agent], round_num: int):
    print(f"\n{'='*70}")
    print(f"🏟️  INTELLIGENCE ARENA STATUS - ROUND {round_num}")
    print(f"{'='*70}")

    divisions = {
        Division.KING: [],
        Division.MASTER: [],
        Division.EXPERT: [],
        Division.NOVICE: [],
    }

    for agent in agents:
        divisions[agent.division].append(agent)

    for division, division_agents in divisions.items():
        if not division_agents:
            continue

        print(f"\n👑 {division.value.upper()} DIVISION:")
        print("-" * 50)

        sorted_agents = sorted(
            division_agents, key=lambda a: a.stats.elo_rating, reverse=True
        )

        for agent in sorted_agents:
            win_rate = agent.stats.win_rate
            streak_indicator = ""
            if agent.stats.current_streak > 0:
                streak_indicator = f"🔥{agent.stats.current_streak}W"
            elif agent.stats.current_streak < 0:
                streak_indicator = f"❄️{abs(agent.stats.current_streak)}L"

            crown = "👑 " if division == Division.KING else ""

            print(
                f"  {crown} {agent.profile.name:15} | "
                f"ELO: {agent.stats.elo_rating:4.0f} | "
                f"Matches: {agent.stats.total_matches:2} | "
                f"W/L/D: {agent.stats.wins:2}/{agent.stats.losses:2}/{agent.stats.draws:2} | "
                f"Win%: {win_rate:5.1f}% {streak_indicator}"
            )

    total_matches = sum(agent.stats.total_matches for agent in agents) // 2
    king_agents = [a for a in agents if a.division == Division.KING]

    print(f"\n📊 ARENA STATISTICS:")
    print(f"   Total Agents: {len(agents)}")
    print(f"   Total Matches: {total_matches}")

    if king_agents:
        king = king_agents[0]
        print(
            f"   👑 Current King: {king.profile.name} (ELO: {king.stats.elo_rating:.0f})"
        )
