#!/usr/bin/env python3
"""
Temporary script to ingest agents into the database.
This will create fresh agent records with the new model list.
"""

import os
import sys
import random
from typing import List, Dict

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_arena.db import supabase

# List of models to ingest
MODELS = [
    "x-ai/grok-code-fast-1",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-flash",
    "google/gemini-2.0-flash-001",
    "deepseek/deepseek-chat-v3-0324",
    "openai/gpt-4.1-mini",
    "google/gemini-2.5-pro",
    "qwen/qwen3-30b-a3b",
    "openai/gpt-5",
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-3.7-sonnet",
    "z-ai/glm-4.5",
    "qwen/qwen3-coder",
    "openai/gpt-4o-mini",
    "mistralai/mistral-nemo",
    "google/gemma-3-12b-it",
    "deepseek/deepseek-chat-v3.1",
    "x-ai/grok-4",
    "x-ai/grok-3-mini",
    "openai/gpt-5-mini",
    "openai/gpt-oss-120b",
    "openai/gpt-4.1",
    "meta-llama/llama-4-maverick",
    "anthropic/claude-3.5-sonnet",
    "mistralai/mistral-small-24b-instruct-2501",
    "meta-llama/llama-3.2-3b-instruct",
    "qwen/qwen3-32b",
    "google/gemini-flash-1.5-8b",
    "mistralai/mistral-small-3.2-24b-instruct",
    "openai/gpt-4o",
    "mistralai/mixtral-8x7b-instruct",
    "mistralai/mistral-7b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "google/gemma-3-27b-it",
    "qwen/qwen-2.5-72b-instruct",
    "qwen/qwq-32b",
]

# Models that support structured output (for judges/challenge generators)
STRUCTURED_OUTPUT_MODELS = {
    "openai/gpt-4o-mini",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o",
    "openai/gpt-4.1",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "google/gemini-2.0-flash-001",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-sonnet-4",
}

# Coding-focused models
CODING_MODELS = {
    "x-ai/grok-code-fast-1",
    "qwen/qwen3-coder",
    "deepseek/deepseek-chat-v3-0324",
    "deepseek/deepseek-chat-v3.1",
    "meta-llama/llama-4-maverick",
}


def get_agent_name(model: str) -> str:
    """Generate a clean agent name from the model identifier."""
    provider, model_name = model.split("/", 1)

    # Only clean up the truly messy/unreadable names
    name_mappings = {
        "deepseek-chat-v3-0324": "DeepSeek-Chat-V3",
        "deepseek-chat-v3.1": "DeepSeek-Chat-V3.1",
        "mistral-small-24b-instruct-2501": "Mistral-Small-24B",
        "mistral-small-3.2-24b-instruct": "Mistral-Small-3.2-24B",
        "llama-3.2-3b-instruct": "Llama-3.2-3B",
        "llama-3.3-70b-instruct": "Llama-3.3-70B",
        "mixtral-8x7b-instruct": "Mixtral-8x7B",
        "mistral-7b-instruct": "Mistral-7B",
        "qwen-2.5-72b-instruct": "Qwen-2.5-72B",
        "qwen3-30b-a3b": "Qwen3-30B",
        "gemini-flash-1.5-8b": "Gemini-Flash-1.5-8B",
    }

    # Use mapping if available, otherwise just title case the original
    if model_name in name_mappings:
        return name_mappings[model_name]
    else:
        # Title case each word, keeping hyphens
        return "-".join(
            word.title() if len(word) > 3 else word.upper()
            for word in model_name.split("-")
        )


def get_provider(model: str) -> str:
    """Extract provider name from model identifier."""
    return model.split("/", 1)[0]


def get_specializations(model: str) -> List[str]:
    """Get specializations based on the model."""
    provider = get_provider(model)
    specializations = ["general intelligence", provider]

    if model in CODING_MODELS:
        specializations.append("coding")

    return specializations


def get_agent_division(model: str) -> str:
    """Determine agent division based on model capability and generation."""

    # MASTER tier - Top flagship models
    master_models = {
        "anthropic/claude-sonnet-4",
        "openai/gpt-5",
        "google/gemini-2.5-pro",
        "x-ai/grok-4",
        "meta-llama/llama-4-maverick",
        "openai/gpt-4.1",
    }

    # EXPERT tier - Advanced models but not flagship
    expert_models = {
        "anthropic/claude-3.7-sonnet",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-5-mini",
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash",
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o",
        "deepseek/deepseek-chat-v3.1",
        "deepseek/deepseek-chat-v3-0324",
        "qwen/qwen3-coder",
        "x-ai/grok-code-fast-1",
        "qwen/qwen3-32b",
        "qwen/qwq-32b",
        "qwen/qwen-2.5-72b-instruct",
    }

    # All others default to NOVICE
    if model in master_models:
        return "MASTER"
    elif model in expert_models:
        return "EXPERT"
    else:
        return "NOVICE"


def create_agent_data(model: str) -> Dict:
    """Create agent data dictionary for database insertion."""
    name = get_agent_name(model)
    provider = get_provider(model)
    specializations = get_specializations(model)

    # Vary temperature slightly for personality differences
    temperature = round(random.uniform(0.3, 0.7), 2)

    # Determine division based on model capability
    division = get_agent_division(model)

    return {
        "name": name,
        "model": model,
        "temperature": 0.5,
        "description": f"AI agent powered by {model}",
        "specializations": specializations,
        "current_division": division.lower(),
        "supports_structured_output": model in STRUCTURED_OUTPUT_MODELS,
        "is_active": True,
    }


def clear_existing_agents():
    """Clear existing agents from the database."""
    try:
        print("🗑️  Clearing existing agents...")

        # Delete ELO history first (foreign key constraint)
        supabase.table("elo_history").delete().neq("id", "").execute()
        print("   ✅ Cleared ELO history")

        # Delete agents
        supabase.table("agents").delete().neq("id", "").execute()
        print("   ✅ Cleared agents")

    except Exception as e:
        print(f"   ⚠️  Error clearing existing data: {e}")


def ingest_agents():
    """Ingest all agents into the database."""
    print(f"🤖 Ingesting {len(MODELS)} agents into the database...")

    agents_to_insert = []

    for model in MODELS:
        try:
            agent_data = create_agent_data(model)
            agents_to_insert.append(agent_data)
            print(
                f"   📝 Prepared: {agent_data['name']} ({model}) - {agent_data['current_division'].upper()}"
            )
        except Exception as e:
            print(f"   ❌ Failed to prepare {model}: {e}")

    if agents_to_insert:
        try:
            # Insert all agents in batch
            result = supabase.table("agents").insert(agents_to_insert).execute()
            print(f"\n✅ Successfully inserted {len(agents_to_insert)} agents!")

            # Show summary
            divisions = {}
            structured_count = 0
            coding_count = 0

            for agent in agents_to_insert:
                div = agent["current_division"]
                divisions[div] = divisions.get(div, 0) + 1
                if agent["supports_structured_output"]:
                    structured_count += 1
                if "coding" in agent["specializations"]:
                    coding_count += 1

            print(f"\n📊 SUMMARY:")
            for div, count in divisions.items():
                print(f"   {div.upper()}: {count} agents")
            print(f"   Structured Output Capable: {structured_count} agents")
            print(f"   Coding Specialists: {coding_count} agents")

        except Exception as e:
            print(f"❌ Failed to insert agents: {e}")
    else:
        print("❌ No agents prepared for insertion")


def main():
    """Main function to run the ingestion process."""
    print("🚀 Starting fresh agent ingestion...")
    print("=" * 60)

    # # Ask for confirmation
    # response = input("This will clear ALL existing agents and ELO history. Continue? (y/N): ")
    # if response.lower() != 'y':
    #     print("❌ Aborted by user")
    #     return

    # Clear existing data
    # clear_existing_agents()

    # Ingest new agents
    ingest_agents()

    print("\n🎉 Agent ingestion complete!")
    print(
        "You can now start the arena and the agents will be loaded with their new configurations."
    )


if __name__ == "__main__":
    main()
