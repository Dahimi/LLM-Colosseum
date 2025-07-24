#!/usr/bin/env python3
"""
Comprehensive Realistic Demo for the Intelligence Arena System.

This script demonstrates a full arena simulation with:
- Multiple real LLM agents using OpenRouter API
- Extensive match rounds with promotion/demotion
- King of the Hill mechanics
- Real LLM-based challenge generation and evaluation
- Multiple models for diversity

Run with: python demo.py

Environment Variables (required):
- OPENROUTER_API_KEY: For accessing all LLM models
- OPENROUTER_BASE_URL: OpenRouter API base URL
"""

import dotenv
dotenv.load_dotenv()
import os
import time
import random
from typing import List, Optional, Tuple, Dict

from agent_arena.models.agent import Agent, AgentProfile, Division
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.models.match import Match, MatchType, AgentResponse

from agent_arena.core.llm_interface import create_agent_llm, get_content, create_system_llm
from agent_arena.core.challenge_generator import ChallengeGenerator
from agent_arena.core.judge_system import evaluate_match_with_llm_judges
from agent_arena.utils.config import get_development_config
from agent_arena.utils.logging import setup_logging, arena_logger


# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "challenge_generation_delay": (2, 4),  # 2-4 seconds between challenge generations
    "agent_response_delay": (1, 2),       # 1-2 seconds between agent responses
    "judge_evaluation_delay": (2, 3),     # 2-3 seconds for judge evaluation
    "match_completion_delay": (1, 2),     # 1-2 seconds after match completion
    "round_completion_delay": (5, 8),     # 5-8 seconds between rounds
}


def rate_limit_delay(delay_type: str):
    """Apply a random delay to prevent rate limiting."""
    return 
    if delay_type in RATE_LIMIT_CONFIG:
        min_delay, max_delay = RATE_LIMIT_CONFIG[delay_type]
        delay = random.uniform(min_delay, max_delay)
        print(f"      ⏳ Rate limiting pause: {delay:.1f}s...")
        time.sleep(delay)



def create_diverse_real_agent_pool() -> Tuple[List[Agent], dict]:
    """Create a large pool of real LLM agents using OpenRouter models."""
    
    agents = []
    agent_llms = {}
    
    if not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError("No OPENROUTER_API_KEY found! Please set this environment variable.")
    
    print(f"   🔑 Using OpenRouter for all LLM interactions")
    
    # Create agents using all available models
    agent_configs = [
        # EXPERT DIVISION - High-performance models
        {"name": "ClaudeSonnet4", "model": "anthropic/claude-sonnet-4", "temperature": 0.3, "division": Division.EXPERT},
        {"name": "GeminiFlash", "model": "google/gemini-2.5-flash", "temperature": 0.4, "division": Division.EXPERT},
        {"name": "GPT41Master", "model": "openai/gpt-4.1", "temperature": 0.3, "division": Division.EXPERT},
        {"name": "GPT4oMaster", "model": "openai/gpt-4o", "temperature": 0.3, "division": Division.EXPERT},
        # NOVICE DIVISION - Other models
        {"name": "GPT4Novice", "model": "openai/gpt-4", "temperature": 0.3, "division": Division.NOVICE},
        {"name": "ClaudeSonnet35", "model": "anthropic/claude-3.5-sonnet", "temperature": 0.6, "division": Division.NOVICE},
        {"name": "GeminiFlash2", "model": "google/gemini-2.0-flash-001", "temperature": 0.5, "division": Division.NOVICE},
        {"name": "LlamaInstructor", "model": "meta-llama/llama-3.1-70b-instruct", "temperature": 0.7, "division": Division.NOVICE},
        {"name": "GemmaReasoner", "model": "google/gemma-3-27b-it", "temperature": 0.6, "division": Division.NOVICE},
        {"name": "QwenLogic", "model": "qwen/qwen-2.5-72b-instruct", "temperature": 0.5, "division": Division.NOVICE},
        {"name": "ClaudeSonnet37", "model": "anthropic/claude-3.7-sonnet", "temperature": 0.4, "division": Division.NOVICE},
    ]
    
    for config in agent_configs:
        try:
            # Create real LLM for this agent
            agent_llm = create_agent_llm(
                model_name=config["model"],
                temperature=config["temperature"],
                max_tokens=1500
            )
            
            # Get provider and model info for display
            provider = config["model"].split('/')[0].title()
            model_short = config["model"].split('/')[-1].split('-')[0].title()
            
            # Create agent profile
            profile = AgentProfile(
                name=config["name"],
                description=f"{provider} {model_short} agent (temp: {config['temperature']}) via OpenRouter",
                specializations=["general intelligence", provider.lower()]
            )
            
            # Create agent
            agent = Agent(profile=profile)
            agent.division = config["division"]
            
            # Set initial ELO based on division and model
            base_elo = {
                Division.NOVICE: 1000,
                Division.EXPERT: 1200,
                Division.MASTER: 1400,
                Division.KING: 1600
            }
            
            # Adjust ELO based on model capabilities
            model_bonus = 0
            if "claude-sonnet-4" in config["model"] or "gpt-4" in config["model"]:
                model_bonus = 100
            elif "gemini-2.5" in config["model"]:
                model_bonus = 75
            
            agent.stats.elo_rating = base_elo[config["division"]] + model_bonus + random.randint(-50, 50)
            
            # Store LLM
            agent_llms[agent.profile.agent_id] = agent_llm
            agents.append(agent)
            
            print(f"   ✅ Created: {config['name']} ({config['model']})")
            arena_logger.agent_joined(agent.profile.agent_id, agent.profile.name)
            
        except Exception as e:
            print(f"   ❌ Failed to create {config['name']}: {e}")
    
    if not agents:
        raise ValueError("No agents could be created! Check your OpenRouter API key.")
    
    return agents, agent_llms


def create_dynamic_challenge_pool(challenge_count: int = 8) -> List[Challenge]:
    """Create challenges using real LLM generation."""
    
    print(f"   🎯 Generating {challenge_count} dynamic challenges using real LLMs...")
    print(f"   ⚠️  This will take ~{challenge_count * 3} seconds due to rate limiting...")
    challenges = []
    
    try:
        generator = ChallengeGenerator()
        
        # Generate diverse challenges across types and difficulties
        challenge_specs = [
            (ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.BEGINNER),
            (ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.CREATIVE_PROBLEM_SOLVING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.CREATIVE_PROBLEM_SOLVING, ChallengeDifficulty.ADVANCED),
            (ChallengeType.MATHEMATICAL, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.MATHEMATICAL, ChallengeDifficulty.ADVANCED),
            (ChallengeType.ABSTRACT_THINKING, ChallengeDifficulty.INTERMEDIATE),
            (ChallengeType.ABSTRACT_THINKING, ChallengeDifficulty.EXPERT),
        ]
        
        for i, (challenge_type, difficulty) in enumerate(challenge_specs[:challenge_count]):
            try:
                # Rate limiting delay before each challenge generation
                if i > 0:
                    rate_limit_delay("challenge_generation_delay")
                challenge = generator.generate_challenge(challenge_type, difficulty)
                challenges.append(challenge)
                print(f"      ✅ Generated #{i+1}: {challenge.title} ({challenge_type.value}, {difficulty.name})")
                
            except Exception as e:
                print(f"      ❌ Failed to generate challenge #{i+1}: {e}")
                # Add extra delay after errors
                time.sleep(2)
        
    except Exception as e:
        print(f"   ❌ Challenge generation failed: {e}")
        return []
    
    return challenges


def simulate_realistic_match(
    agent1: Agent, 
    agent2: Agent, 
    challenge: Challenge, 
    agent_llms: dict
) -> Tuple[Optional[str], Dict[str, float]]:
    """Simulate a complete match with real LLM responses and evaluation."""
    
    try:
        # Create actual match object
        match = Match(
            match_type=MatchType.REGULAR_DUEL,
            challenge_id=challenge.challenge_id,
            agent1_id=agent1.profile.agent_id,
            agent2_id=agent2.profile.agent_id,
            division=agent1.division.value
        )
        
        # Start match
        match.start_match()
        
        # Get challenge prompt
        prompt = challenge.get_prompt()
        
        print(f"      🤖 Getting real LLM responses...")
        
        # Generate responses using real LLMs
        agent1_llm = agent_llms[agent1.profile.agent_id]
        start_time = time.time()
        response1_obj = agent1_llm.invoke(prompt)
        response1_text = get_content(response1_obj)
        response1_time = time.time() - start_time
        
        agent2_llm = agent_llms[agent2.profile.agent_id]
        start_time = time.time()
        response2_obj = agent2_llm.invoke(prompt)
        response2_text = get_content(response2_obj)
        response2_time = time.time() - start_time
        
        # Create response objects
        response1 = AgentResponse(
            agent_id=agent1.profile.agent_id,
            response_text=response1_text,
            response_time=response1_time
        )
        
        response2 = AgentResponse(
            agent_id=agent2.profile.agent_id,
            response_text=response2_text,
            response_time=response2_time
        )
        
        # Submit responses
        match.submit_response(agent1.profile.agent_id, response1)
        match.submit_response(agent2.profile.agent_id, response2)
        
        print(f"      ⚖️  Evaluating with real LLM judges...")
        
        # Rate limiting delay before evaluation
        rate_limit_delay("judge_evaluation_delay")
        
        # Create system LLM for evaluation
        judge_llm = create_system_llm(temperature=0.4)
        
        # Evaluate using real LLM judges
        evaluation_result = evaluate_match_with_llm_judges(match, challenge, judge_count=2)
        
        # Extract results
        winner_agent_num = evaluation_result.get("winner")
        final_score_agent1 = evaluation_result.get("agent1_avg", 5.0)
        final_score_agent2 = evaluation_result.get("agent2_avg", 5.0)
        
        # Map winner to agent ID
        if winner_agent_num == "agent1":
            winner_id = agent1.profile.agent_id
        elif winner_agent_num == "agent2":
            winner_id = agent2.profile.agent_id
        else:
            winner_id = None  # Draw
        
        scores = {
            agent1.profile.agent_id: final_score_agent1,
            agent2.profile.agent_id: final_score_agent2
        }
        
        # Rate limiting delay after match completion
        rate_limit_delay("match_completion_delay")
        
        return winner_id, scores
        
    except Exception as e:
        print(f"      ❌ Match simulation failed: {e}")
        # Fallback to simple random for robustness
        if random.random() < 0.5:
            winner_id = agent1.profile.agent_id
        else:
            winner_id = agent2.profile.agent_id
        return winner_id, {agent1.profile.agent_id: 6.0, agent2.profile.agent_id: 5.5}


def update_agent_stats_and_elo(agent1: Agent, agent2: Agent, winner_id: Optional[str], scores: Dict[str, float]):
    """Update agent statistics and ELO ratings after a match."""
    
    # Update match counts
    agent1.stats.total_matches += 1
    agent2.stats.total_matches += 1
    
    # ELO calculation
    k_factor = 32
    agent1_elo = agent1.stats.elo_rating
    agent2_elo = agent2.stats.elo_rating
    
    # Expected scores based on ELO
    expected1 = 1 / (1 + 10 ** ((agent2_elo - agent1_elo) / 400))
    expected2 = 1 / (1 + 10 ** ((agent1_elo - agent2_elo) / 400))
    
    # Actual scores
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
    else:  # Draw
        actual1, actual2 = 0.5, 0.5
        agent1.stats.draws += 1
        agent2.stats.draws += 1
        agent1.stats.current_streak = 0
        agent2.stats.current_streak = 0
    
    # Update ELO ratings
    agent1.stats.elo_rating += k_factor * (actual1 - expected1)
    agent2.stats.elo_rating += k_factor * (actual2 - expected2)
    
    # Update best streaks
    agent1.stats.best_streak = max(agent1.stats.best_streak, agent1.stats.current_streak)
    agent2.stats.best_streak = max(agent2.stats.best_streak, agent2.stats.current_streak)


def apply_realistic_division_changes(agents: List[Agent]) -> List[str]:
    """Apply promotion and demotion rules based on performance metrics."""
    
    changes = []
    
    for agent in agents:
        original_division = agent.division
        
        # More realistic promotion criteria
        win_rate = agent.stats.win_rate
        streak = agent.stats.current_streak
        elo = agent.stats.elo_rating
        matches = agent.stats.total_matches
        
        # Check for promotion (need good performance metrics)
        if matches >= 3:  # Need some match history
            if agent.division == Division.NOVICE and (win_rate >= 60 or streak >= 3) and elo >= 1150:
                agent.promote_division(Division.EXPERT, f"Promoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                changes.append(f"🔺 {agent.profile.name}: NOVICE → EXPERT (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                
            elif agent.division == Division.EXPERT and (win_rate >= 70 or streak >= 4) and elo >= 1350:
                agent.promote_division(Division.MASTER, f"Promoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                changes.append(f"🔺 {agent.profile.name}: EXPERT → MASTER (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                
            elif agent.division == Division.MASTER and (win_rate >= 75 or streak >= 5) and elo >= 1500:
                # Check if there's already a King
                current_kings = [a for a in agents if a.division == Division.KING]
                if not current_kings:
                    agent.promote_division(Division.KING, f"Crowned with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                    changes.append(f"👑 {agent.profile.name}: MASTER → KING (CROWNED! Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
        
        # Check for demotion (poor performance)
        if matches >= 4:  # Need more match history for demotion
            if agent.division == Division.KING and (win_rate <= 40 or streak <= -3) and elo <= 1400:
                agent.demote_division(Division.MASTER, f"Dethroned with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                changes.append(f"🔻 {agent.profile.name}: KING → MASTER (DETHRONED! Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                
            elif agent.division == Division.MASTER and (win_rate <= 35 or streak <= -4) and elo <= 1250:
                agent.demote_division(Division.EXPERT, f"Demoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                changes.append(f"🔻 {agent.profile.name}: MASTER → EXPERT (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
                
            elif agent.division == Division.EXPERT and (win_rate <= 30 or streak <= -4) and elo <= 1100:
                agent.demote_division(Division.NOVICE, f"Demoted with {win_rate:.1f}% win rate and {elo:.0f} ELO")
                changes.append(f"🔻 {agent.profile.name}: EXPERT → NOVICE (Win rate: {win_rate:.1f}%, ELO: {elo:.0f})")
    
    return changes


def run_realistic_tournament_round(agents: List[Agent], challenges: List[Challenge], agent_llms: dict, round_num: int):
    """Run a tournament round with real LLM matches and evaluation."""
    
    print(f"\n🏆 REALISTIC TOURNAMENT ROUND {round_num}")
    print("=" * 60)
    
    # Group agents by division
    divisions = {}
    for agent in agents:
        if agent.division not in divisions:
            divisions[agent.division] = []
        divisions[agent.division].append(agent)
    
    match_count = 0
    
    # Run matches within each division
    for division, division_agents in divisions.items():
        if len(division_agents) < 2:
            continue
            
        print(f"\n📊 {division.value.upper()} DIVISION MATCHES:")
        
        # Pair up agents for matches (shuffle for variety)
        random.shuffle(division_agents)
        for i in range(0, len(division_agents) - 1, 2):
            agent1 = division_agents[i]
            agent2 = division_agents[i + 1]
            
            # Select appropriate challenge based on division level
            if division == Division.NOVICE:
                appropriate_challenges = [c for c in challenges if c.difficulty.value <= 2]
            elif division == Division.EXPERT:
                appropriate_challenges = [c for c in challenges if c.difficulty.value <= 3]
            else:  # Master/King
                appropriate_challenges = [c for c in challenges if c.difficulty.value >= 3]
            
            if not appropriate_challenges:
                appropriate_challenges = challenges  # Fallback to any challenge
            
            challenge = random.choice(appropriate_challenges)
            
            print(f"\n   🥊 Match {match_count + 1}: {agent1.profile.name} vs {agent2.profile.name}")
            print(f"      Challenge: {challenge.title} ({challenge.difficulty.name})")
            print(f"      Agent 1: {agent1.profile.description}")
            print(f"      Agent 2: {agent2.profile.description}")
            
            # Simulate realistic match with real LLMs
            start_time = time.time()
            winner_id, scores = simulate_realistic_match(agent1, agent2, challenge, agent_llms)
            match_duration = time.time() - start_time
            
            # Update stats and ELO
            update_agent_stats_and_elo(agent1, agent2, winner_id, scores)
            
            # Report detailed results
            if winner_id:
                winner_name = agent1.profile.name if winner_id == agent1.profile.agent_id else agent2.profile.name
                print(f"      🏆 Winner: {winner_name}")
            else:
                print(f"      🤝 Draw")
            
            print(f"      📊 Scores: {agent1.profile.name}: {scores.get(agent1.profile.agent_id, 0):.1f}, "
                  f"{agent2.profile.name}: {scores.get(agent2.profile.agent_id, 0):.1f}")
            print(f"      ⏱️  Match duration: {match_duration:.1f}s")
            print(f"      📈 ELO changes: {agent1.profile.name}: {agent1.stats.elo_rating:.0f} ({'+' if agent1.stats.elo_rating >= 1200 else ''}{agent1.stats.elo_rating - 1200:.0f}), "
                  f"{agent2.profile.name}: {agent2.stats.elo_rating:.0f} ({'+' if agent2.stats.elo_rating >= 1200 else ''}{agent2.stats.elo_rating - 1200:.0f})")
            
            match_count += 1
    
    print(f"\n✅ Round {round_num} completed: {match_count} realistic matches")
    
    # Apply division changes
    changes = apply_realistic_division_changes(agents)
    if changes:
        print("\n🔄 DIVISION CHANGES:")
        for change in changes:
            print(f"   {change}")
    else:
        print("\n📋 No division changes this round")


def print_comprehensive_status(agents: List[Agent], round_num: int):
    """Print detailed arena status with enhanced metrics."""
    
    print(f"\n{'='*70}")
    print(f"🏟️  INTELLIGENCE ARENA STATUS - ROUND {round_num}")
    print(f"{'='*70}")
    
    # Group agents by division
    divisions = {
        Division.KING: [],
        Division.MASTER: [],
        Division.EXPERT: [],
        Division.NOVICE: []
    }
    
    for agent in agents:
        divisions[agent.division].append(agent)
    
    # Display each division with enhanced metrics
    for division, division_agents in divisions.items():
        if not division_agents:
            continue
            
        print(f"\n👑 {division.value.upper()} DIVISION:")
        print("-" * 50)
        
        # Sort by ELO rating
        sorted_agents = sorted(division_agents, key=lambda a: a.stats.elo_rating, reverse=True)
        
        for agent in sorted_agents:
            win_rate = agent.stats.win_rate
            streak_indicator = ""
            if agent.stats.current_streak > 0:
                streak_indicator = f"🔥{agent.stats.current_streak}W"
            elif agent.stats.current_streak < 0:
                streak_indicator = f"❄️{abs(agent.stats.current_streak)}L"
            
            # Add crown for King
            crown = "👑 " if division == Division.KING else ""
            
            # Extract provider from description
            provider_info = ""
            if "groq" in agent.profile.description.lower():
                provider_info = "🟢"
            elif "openai" in agent.profile.description.lower():
                provider_info = "🔵"
            elif "anthropic" in agent.profile.description.lower():
                provider_info = "🟠"
            
            print(f"  {crown}{provider_info} {agent.profile.name:15} | "
                  f"ELO: {agent.stats.elo_rating:4.0f} | "
                  f"Matches: {agent.stats.total_matches:2} | "
                  f"W/L/D: {agent.stats.wins:2}/{agent.stats.losses:2}/{agent.stats.draws:2} | "
                  f"Win%: {win_rate:5.1f}% {streak_indicator}")
    
    # Enhanced statistics
    total_matches = sum(agent.stats.total_matches for agent in agents) // 2
    active_agents = sum(1 for agent in agents if agent.profile.is_active)
    king_agents = [a for a in agents if a.division == Division.KING]
    avg_elo = sum(a.stats.elo_rating for a in agents) / len(agents)
    
    print(f"\n📊 ARENA STATISTICS:")
    print(f"   Total Agents: {len(agents)}")
    print(f"   Active Agents: {active_agents}")
    print(f"   Total Matches: {total_matches}")
    print(f"   Average ELO: {avg_elo:.0f}")
    print(f"   King Count: {len(king_agents)}")
    
    if king_agents:
        king = king_agents[0]
        print(f"   👑 Current King: {king.profile.name} (ELO: {king.stats.elo_rating:.0f}, "
              f"Streak: {king.stats.current_streak}, Win Rate: {king.stats.win_rate:.1f}%)")


def main():
    """Run comprehensive realistic arena simulation."""
    
    print("🚀 REALISTIC INTELLIGENCE ARENA SIMULATION")
    print("🎯 100% Real LLMs: Agents, Challenges, and Evaluation!")
    print("="*70)
    
    # Setup
    config = get_development_config()
    setup_logging("WARNING", False)  # Reduce logging noise
    
    
    # Create realistic agent pool
    print("\n1. 🤖 Creating realistic agent pool with diverse LLMs...")
    try:
        agents, agent_llms = create_diverse_real_agent_pool()
        print(f"   ✅ Successfully created {len(agents)} real LLM agents")
        
        for division in [Division.EXPERT, Division.NOVICE]:
            division_agents = [a for a in agents if a.division == division]
            if division_agents:
                print(f"   - {division.value.upper()}: {len(division_agents)} agents")
    except Exception as e:
        print(f"❌ Failed to create agent pool: {e}")
        return
    
    # Create dynamic challenges
    print(f"\n2. 📚 Creating dynamic challenge pool...")
    try:
        challenges = create_dynamic_challenge_pool(6)  # Fewer challenges for speed
        if not challenges:
            print("❌ No challenges could be generated. Exiting...")
            return
        print(f"   ✅ Successfully created {len(challenges)} dynamic challenges")
    except Exception as e:
        print(f"❌ Failed to create challenges: {e}")
        return
    
    # Initial status
    print_comprehensive_status(agents, 0)
    
    # Run realistic tournament
    print(f"\n3. 🏆 RUNNING REALISTIC MULTI-ROUND TOURNAMENT...")
    print("   ⚠️  This may take several minutes due to real LLM processing...")
    
    try:
        for round_num in range(1, 6):  # 2 rounds for reasonable runtime with delays
            print(f"\n⏰ Starting round {round_num}...")
            run_realistic_tournament_round(agents, challenges, agent_llms, round_num)
            print_comprehensive_status(agents, round_num)
            
            if round_num < 3:
                print(f"\n⏸️  Pausing 3 seconds before next round...")
                time.sleep(3)
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Tournament error: {e}")
    
    # Final comprehensive summary
    print(f"\n🎊 REALISTIC TOURNAMENT COMPLETE!")
    print("="*60)
    
    # Show final king
    king_agents = [a for a in agents if a.division == Division.KING]
    if king_agents:
        king = king_agents[0]
        print(f"👑 FINAL KING: {king.profile.name}")
        print(f"   🏆 ELO Rating: {king.stats.elo_rating:.0f}")
        print(f"   📊 Record: {king.stats.wins}W-{king.stats.losses}L-{king.stats.draws}D")
        print(f"   📈 Win Rate: {king.stats.win_rate:.1f}%")
        print(f"   🔥 Current Streak: {king.stats.current_streak}")
        print(f"   🤖 LLM: {king.profile.description}")
    else:
        print("👑 No King emerged - competition continues!")
    
    # Show top performers across all divisions
    print(f"\n🏆 TOP PERFORMERS (All Divisions):")
    all_agents_sorted = sorted(agents, key=lambda a: a.stats.elo_rating, reverse=True)
    for i, agent in enumerate(all_agents_sorted[:7], 1):
        division_icon = {"king": "👑", "master": "🥇", "expert": "🥈", "novice": "🥉"}.get(agent.division.value, "🔹")
        provider_icon = "🟢" if "groq" in agent.profile.description.lower() else "🔵" if "openai" in agent.profile.description.lower() else "🟠"
        print(f"   {i}. {division_icon} {provider_icon} {agent.profile.name} (ELO: {agent.stats.elo_rating:.0f}, "
              f"Division: {agent.division.value.upper()}, Win Rate: {agent.stats.win_rate:.1f}%)")
    
    print(f"\n✨ REALISTIC FEATURES DEMONSTRATED:")
    print("- 🤖 100% Real LLM agents with diverse providers and personalities")
    print("- 🎯 Dynamic challenge generation using real LLMs")
    print("- ⚖️  Real LLM-based multi-judge evaluation system")
    print("- 📈 Realistic ELO rating system with performance-based promotions")
    print("- 👑 Authentic King of the Hill mechanics")
    print("- 📊 Comprehensive performance tracking and statistics")
    print("- 🔄 Fully autonomous LLM-to-LLM competition")


if __name__ == "__main__":
    main() 