
import json
import os
import random
import time
from typing import List, Dict, Optional, Tuple

from agent_arena.models.agent import Agent, AgentProfile, Division
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.models.match import Match, MatchType, AgentResponse
from agent_arena.core.llm_interface import create_agent_llm, get_content, create_system_llm
from agent_arena.core.challenge_generator import ChallengeGenerator
from agent_arena.core.judge_system import evaluate_match_with_llm_judges
from agent_arena.utils.logging import arena_logger, get_logger

logger = get_logger(__name__)


class Arena:
    def __init__(self, agents_file: str, state_file: str):
        self.agents_file = agents_file
        self.state_file = state_file
        self.agents: List[Agent] = []
        self.challenges: List[Challenge] = []
        self.agent_llms: Dict[str, any] = {}
        self.load_state()

    def load_agents_from_config(self):
        """Loads agents from the configuration file."""
        try:
            with open(self.agents_file, 'r') as f:
                agents_config = json.load(f)

            for config in agents_config:
                profile = AgentProfile(
                    name=config["name"],
                    description=f"Agent based on {config['model']}",
                    specializations=config.get("specializations", [])
                )
                agent = Agent(
                    profile=profile,
                    division=Division[config["division"]]
                )
                self.agents.append(agent)

                # Create LLM for the agent
                agent_llm = create_agent_llm(
                    model_name=config["model"],
                    temperature=config["temperature"],
                    max_tokens=1500
                )
                self.agent_llms[agent.profile.agent_id] = agent_llm
            logger.info(f"Loaded {len(self.agents)} agents from {self.agents_file}")
        except FileNotFoundError:
            logger.error(f"Agents file not found: {self.agents_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading agents from config: {e}")
            raise

    def save_state(self):
        """Saves the current state of the arena to a file."""
        state = {
            "agents": [agent.to_dict() for agent in self.agents],
            "challenges": [challenge.to_dict() for challenge in self.challenges]
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
            logger.info(f"Arena state saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving arena state: {e}")

    def load_state(self):
        """Loads the arena state from a file, or initializes a new state."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.agents = [Agent.from_dict(agent_data) for agent_data in state["agents"]]
                self.challenges = [Challenge.from_dict(challenge_data) for challenge_data in state.get("challenges", [])]
                
                # Re-create LLM clients for loaded agents
                self.recreate_llm_clients()

                logger.info(f"Arena state loaded from {self.state_file}")
            except Exception as e:
                logger.error(f"Error loading state from {self.state_file}, creating new state. Error: {e}")
                self.initialize_new_state()
        else:
            logger.info("No state file found, initializing a new arena state.")
            self.initialize_new_state()

    def recreate_llm_clients(self):
        """Recreates LLM clients for all agents, needed after loading state."""
        # This requires matching loaded agents back to their original config to get model names
        try:
            with open(self.agents_file, 'r') as f:
                agents_config = json.load(f)
            
            config_map = {cfg['name']: cfg for cfg in agents_config}

            for agent in self.agents:
                if agent.profile.name in config_map:
                    config = config_map[agent.profile.name]
                    agent_llm = create_agent_llm(
                        model_name=config["model"],
                        temperature=config["temperature"],
                        max_tokens=1500
                    )
                    self.agent_llms[agent.profile.agent_id] = agent_llm
        except Exception as e:
            logger.error(f"Failed to recreate LLM clients: {e}")

    def initialize_new_state(self):
        """Initializes a new arena state from the agent configuration file."""
        self.load_agents_from_config()
        self.create_dynamic_challenge_pool()
        self.save_state()

    def simulate_realistic_match(self, agent1: Agent, agent2: Agent, challenge: Challenge) -> Tuple[Optional[str], Dict[str, float]]:
        """Simulate a complete match with real LLM responses and evaluation."""
        try:
            match = Match(
                match_type=MatchType.REGULAR_DUEL,
                challenge_id=challenge.challenge_id,
                agent1_id=agent1.profile.agent_id,
                agent2_id=agent2.profile.agent_id,
                division=agent1.division.value
            )
            match.start_match()
            prompt = challenge.get_prompt()

            print(f"      🤖 Getting real LLM responses...")
            agent1_llm = self.agent_llms[agent1.profile.agent_id]
            start_time = time.time()
            response1_obj = agent1_llm.invoke(prompt)
            response1_text = get_content(response1_obj)
            response1_time = time.time() - start_time

            agent2_llm = self.agent_llms[agent2.profile.agent_id]
            start_time = time.time()
            response2_obj = agent2_llm.invoke(prompt)
            response2_text = get_content(response2_obj)
            response2_time = time.time() - start_time

            response1 = AgentResponse(agent_id=agent1.profile.agent_id, response_text=response1_text, response_time=response1_time)
            response2 = AgentResponse(agent_id=agent2.profile.agent_id, response_text=response2_text, response_time=response2_time)

            match.submit_response(agent1.profile.agent_id, response1)
            match.submit_response(agent2.profile.agent_id, response2)

            print(f"      ⚖️  Evaluating with real LLM judges...")
            evaluation_result = evaluate_match_with_llm_judges(match, challenge, judge_count=2)

            winner_agent_num = evaluation_result.get("winner")
            final_score_agent1 = evaluation_result.get("agent1_avg", 5.0)
            final_score_agent2 = evaluation_result.get("agent2_avg", 5.0)

            if winner_agent_num == "agent1":
                winner_id = agent1.profile.agent_id
            elif winner_agent_num == "agent2":
                winner_id = agent2.profile.agent_id
            else:
                winner_id = None

            scores = {
                agent1.profile.agent_id: final_score_agent1,
                agent2.profile.agent_id: final_score_agent2
            }
            return winner_id, scores
        except Exception as e:
            print(f"      ❌ Match simulation failed: {e}")
            winner_id = random.choice([agent1.profile.agent_id, agent2.profile.agent_id])
            return winner_id, {agent1.profile.agent_id: 6.0, agent2.profile.agent_id: 5.5}

    def simulate_debate_match(self, agent1: Agent, agent2: Agent, challenge: Challenge, num_turns: int = 10) -> Tuple[Optional[str], Dict[str, float]]:
        """Simulate a complete debate match."""
        stances = ["for", "against"]
        random.shuffle(stances)
        agent1_stance, agent2_stance = stances

        match = Match(
            match_type=MatchType.DEBATE,
            challenge_id=challenge.challenge_id,
            agent1_id=agent1.profile.agent_id,
            agent2_id=agent2.profile.agent_id,
            division=agent1.division.value
        )
        match.start_match()

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
            try:
                response_obj = agent_llm.invoke(prompt)
                response_text = get_content(response_obj)
            except Exception as e:
                print(f"      ❌ Error getting response from {agent_to_respond.profile.name}: {e}")
                print(f"      {opponent_agent.profile.name} wins by default as their opponent failed to respond.")
                winner_id = opponent_agent.profile.agent_id
                scores = {
                    opponent_agent.profile.agent_id: 8.0,
                    agent_to_respond.profile.agent_id: 2.0,
                }
                return winner_id, scores

            current_transcript.append({"agent_name": agent_to_respond.profile.name, "response_text": response_text})
            
            response = AgentResponse(
                agent_id=agent_to_respond.profile.agent_id,
                response_text=response_text,
                response_time=0  # Not timing turns for now
            )
            match.transcript.append(response)
            with open("transcript.txt", "w", encoding="utf-8") as f:
                f.write(prompt)

        print(f"      ⚖️  Evaluating debate with real LLM judges...")
        evaluation_result = evaluate_match_with_llm_judges(match, challenge, judge_count=2)
        winner_agent_num = evaluation_result.get("winner")
        if winner_agent_num == "agent1":
            winner_id = agent1.profile.agent_id
        elif winner_agent_num == "agent2":
            winner_id = agent2.profile.agent_id
        else:
            winner_id = None
        
        scores = {
            agent1.profile.agent_id: evaluation_result.get("agent1_avg", 5.0),
            agent2.profile.agent_id: evaluation_result.get("agent2_avg", 5.0)
        }
        return winner_id, scores

    def update_agent_stats_and_elo(self, agent1: Agent, agent2: Agent, winner_id: Optional[str], scores: Dict[str, float]):
        """Update agent statistics and ELO ratings after a match."""
        agent1.stats.total_matches += 1
        agent2.stats.total_matches += 1
        k_factor = 32
        agent1_elo = agent1.stats.elo_rating
        agent2_elo = agent2.stats.elo_rating
        expected1 = 1 / (1 + 10 ** ((agent2_elo - agent1_elo) / 400))
        expected2 = 1 / (1 + 10 ** ((agent1_elo - agent2_elo) / 400))

        if winner_id == agent1.profile.agent_id:
            actual1, actual2 = 1, 0
            agent1.stats.wins += 1
            agent2.stats.losses += 1
            agent1.stats.current_streak = max(1, agent1.stats.current_streak + 1)
            agent2.stats.current_streak = min(-1, agent2.stats.current_streak - 1)
        elif winner_id == agent2.profile.agent_id:
            actual1, actual2 = 0, 1
            agent2.stats.wins += 1
            agent1.stats.losses += 1
            agent2.stats.current_streak = max(1, agent2.stats.current_streak + 1)
            agent1.stats.current_streak = min(-1, agent1.stats.current_streak - 1)
        else:
            actual1, actual2 = 0.5, 0.5
            agent1.stats.draws += 1
            agent2.stats.draws += 1
            agent1.stats.current_streak = 0
            agent2.stats.current_streak = 0

        agent1.stats.elo_rating += k_factor * (actual1 - expected1)
        agent2.stats.elo_rating += k_factor * (actual2 - expected2)
        agent1.stats.best_streak = max(agent1.stats.best_streak, agent1.stats.current_streak)
        agent2.stats.best_streak = max(agent2.stats.best_streak, agent2.stats.current_streak)

    def apply_realistic_division_changes(self):
        """Apply promotion and demotion rules based on performance metrics."""
        changes = []
        for agent in self.agents:
            win_rate = agent.stats.win_rate
            streak = agent.stats.current_streak
            elo = agent.stats.elo_rating
            matches = agent.stats.total_matches

            if matches >= 3:
                if agent.division == Division.NOVICE and (win_rate >= 60 or streak >= 3):
                    agent.promote_division(Division.EXPERT, f"Promoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"🔺 {agent.profile.name}: NOVICE → EXPERT (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                elif agent.division == Division.EXPERT and (win_rate >= 70 or streak >= 4):
                    agent.promote_division(Division.MASTER, f"Promoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"🔺 {agent.profile.name}: EXPERT → MASTER (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                elif agent.division == Division.MASTER and (win_rate >= 75 or streak >= 5):
                    current_kings = [a for a in self.agents if a.division == Division.KING]
                    if not current_kings:
                        agent.promote_division(Division.KING, f"Crowned with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                        changes.append(f"👑 {agent.profile.name}: MASTER → KING (CROWNED! Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
            
            if matches >= 4:
                if agent.division == Division.KING and (win_rate <= 40 or streak <= -3):
                    agent.demote_division(Division.MASTER, f"Dethroned with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"🔻 {agent.profile.name}: KING → MASTER (DETHRONED! Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                elif agent.division == Division.MASTER and (win_rate <= 35 or streak <= -4):
                    agent.demote_division(Division.EXPERT, f"Demoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"🔻 {agent.profile.name}: MASTER → EXPERT (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                elif agent.division == Division.EXPERT and (win_rate <= 30 or streak <= -4):
                    agent.demote_division(Division.NOVICE, f"Demoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"🔻 {agent.profile.name}: EXPERT → NOVICE (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
        
        if changes:
            print("\n🔄 DIVISION CHANGES:")
            for change in changes:
                print(f"   {change}")
        else:
            print("\n📋 No division changes this round")

    def create_dynamic_challenge_pool(self, challenge_count: int = 8):
        """Create challenges using real LLM generation."""
        print(f"   🎯 Generating {challenge_count} dynamic challenges using real LLMs...")
        generator = ChallengeGenerator()
        
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
        
        for i, (challenge_type, difficulty) in enumerate(challenge_specs[:challenge_count]):
            try:
                challenge = generator.generate_challenge(challenge_type, difficulty)
                self.challenges.append(challenge)
                print(f"      ✅ Generated #{i+1}: {challenge.title} ({challenge_type.value}, {difficulty.name})")
                
            except Exception as e:
                print(f"      ❌ Failed to generate challenge #{i+1}: {e}")
                time.sleep(2)

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
        
        divisions = {}
        for agent in self.agents:
            if agent.division not in divisions:
                divisions[agent.division] = []
            divisions[agent.division].append(agent)
        
        match_count = 0
        for division, division_agents in divisions.items():
            if len(division_agents) < 2:
                continue
            
            print(f"\n📊 {division.value.upper()} DIVISION MATCHES:")
            random.shuffle(division_agents)
            for i in range(0, len(division_agents) - 1, 2):
                agent1 = division_agents[i]
                agent2 = division_agents[i + 1]
                
                if division == Division.NOVICE:
                    appropriate_challenges = [c for c in self.challenges if c.difficulty.value <= 2]
                elif division == Division.EXPERT:
                    appropriate_challenges = [c for c in self.challenges if c.difficulty.value <= 3]
                else:
                    appropriate_challenges = [c for c in self.challenges if c.difficulty.value >= 3]
                
                if not appropriate_challenges:
                    appropriate_challenges = self.challenges
                
                challenge = random.choice(appropriate_challenges)
                
                print(f"\n   🥊 Match {match_count + 1}: {agent1.profile.name} vs {agent2.profile.name}")
                print(f"      Challenge: {challenge.title} ({challenge.difficulty.name})")
                
                start_time = time.time()
                if challenge.challenge_type == ChallengeType.DEBATE:
                    winner_id, scores = self.simulate_debate_match(agent1, agent2, challenge)
                else:
                    winner_id, scores = self.simulate_realistic_match(agent1, agent2, challenge)
                match_duration = time.time() - start_time
                
                self.update_agent_stats_and_elo(agent1, agent2, winner_id, scores)
                
                if winner_id:
                    winner_name = agent1.profile.name if winner_id == agent1.profile.agent_id else agent2.profile.name
                    print(f"      🏆 Winner: {winner_name}")
                else:
                    print(f"      🤝 Draw")
                
                print(f"      📊 Scores: {agent1.profile.name}: {scores.get(agent1.profile.agent_id, 0):.1f}, "
                      f"{agent2.profile.name}: {scores.get(agent2.profile.agent_id, 0):.1f}")
                print(f"      ⏱️  Match duration: {match_duration:.1f}s")
                
                match_count += 1
        
        print(f"\n✅ Round {round_num} completed: {match_count} realistic matches")
        self.apply_realistic_division_changes()


def print_comprehensive_status(agents: List[Agent], round_num: int):
    print(f"\n{'='*70}")
    print(f"🏟️  INTELLIGENCE ARENA STATUS - ROUND {round_num}")
    print(f"{'='*70}")
    
    divisions = {
        Division.KING: [],
        Division.MASTER: [],
        Division.EXPERT: [],
        Division.NOVICE: []
    }
    
    for agent in agents:
        divisions[agent.division].append(agent)
    
    for division, division_agents in divisions.items():
        if not division_agents:
            continue
            
        print(f"\n👑 {division.value.upper()} DIVISION:")
        print("-" * 50)
        
        sorted_agents = sorted(division_agents, key=lambda a: a.stats.elo_rating, reverse=True)
        
        for agent in sorted_agents:
            win_rate = agent.stats.win_rate
            streak_indicator = ""
            if agent.stats.current_streak > 0:
                streak_indicator = f"🔥{agent.stats.current_streak}W"
            elif agent.stats.current_streak < 0:
                streak_indicator = f"❄️{abs(agent.stats.current_streak)}L"
            
            crown = "👑 " if division == Division.KING else ""
            
            print(f"  {crown} {agent.profile.name:15} | "
                  f"ELO: {agent.stats.elo_rating:4.0f} | "
                  f"Matches: {agent.stats.total_matches:2} | "
                  f"W/L/D: {agent.stats.wins:2}/{agent.stats.losses:2}/{agent.stats.draws:2} | "
                  f"Win%: {win_rate:5.1f}% {streak_indicator}")
    
    total_matches = sum(agent.stats.total_matches for agent in agents) // 2
    king_agents = [a for a in agents if a.division == Division.KING]
    
    print(f"\n📊 ARENA STATISTICS:")
    print(f"   Total Agents: {len(agents)}")
    print(f"   Total Matches: {total_matches}")
    
    if king_agents:
        king = king_agents[0]
        print(f"   👑 Current King: {king.profile.name} (ELO: {king.stats.elo_rating:.0f})") 