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
from agent_arena.core.arena import Arena, print_comprehensive_status
from agent_arena.utils.logging import setup_logging
import logging

logger = logging.getLogger(__name__)


def main():
    """Run comprehensive realistic arena simulation."""
    print("🚀 REALISTIC INTELLIGENCE ARENA SIMULATION")
    print("🎯 100% Real LLMs: Agents, Challenges, and Evaluation!")
    print("=" * 70)

    # Setup
    setup_logging("WARNING", False)  # Reduce logging noise

    # Initialize the Arena
    agents_file = "agents.json"
    state_file = "arena_state.json"

    if not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError(
            "No OPENROUTER_API_KEY found! Please set this environment variable."
        )

    try:
        arena = Arena(agents_file=agents_file, state_file=state_file)
        print(f"   ✅ Successfully loaded arena with {len(arena.agents)} agents.")
    except Exception as e:
        print(f"❌ Failed to initialize arena: {e}")
        return

    # Initial status
    print_comprehensive_status(arena.agents, 0)

    # Run realistic tournament
    print(f"\n3. 🏆 RUNNING REALISTIC MULTI-ROUND TOURNAMENT...")
    print("   ⚠️  This may take several minutes due to real LLM processing...")

    try:
        arena.run_tournament(num_rounds=5)
    except KeyboardInterrupt:
        print(f"\n⏹️  Simulation interrupted by user")
        arena.save_state()
    except Exception as e:
        logger.error(f"Tournament error: {e}", exc_info=True)
        print(f"\n❌ Tournament error: {e}")
        arena.save_state()

    # Final comprehensive summary
    print(f"\n🎊 REALISTIC TOURNAMENT COMPLETE!")
    print("=" * 60)
    print_comprehensive_status(arena.agents, -1)  # -1 for final status


if __name__ == "__main__":
    main()
