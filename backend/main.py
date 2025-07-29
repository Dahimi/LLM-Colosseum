from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
import random
from typing import List, Optional
from agent_arena.core.arena import Arena
from agent_arena.models.match import Match, MatchStatus, MatchType
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.models.agent import Division

app = FastAPI()

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize arena
arena = Arena("agents.json", "arena_state.json")

def match_to_json(match: Match) -> dict:
    """Convert a Match object to a JSON-friendly format."""
    match_dict = match.to_dict()
    
    # Convert datetime objects to ISO format strings
    for field in ["created_at", "started_at", "completed_at"]:
        if field in match_dict and hasattr(match_dict[field], 'isoformat'):
            match_dict[field] = match_dict[field].isoformat()
    
    # Convert status to uppercase to match frontend enum
    match_dict["status"] = match_dict["status"].upper()
    
    # Add challenge details
    challenge = next((c for c in arena.challenges if c.challenge_id == match.challenge_id), None)
    if challenge:
        match_dict["challenge"] = {
            "challenge_id": challenge.challenge_id,
            "title": challenge.title,
            "description": challenge.description,
            "type": challenge.challenge_type.value.upper(),
            "difficulty": challenge.difficulty.value
        }
    else:
        # Provide default challenge data if not found
        match_dict["challenge"] = {
            "challenge_id": match.challenge_id,
            "title": "Challenge",
            "description": "Challenge description",
            "type": "LOGICAL_REASONING",
            "difficulty": "INTERMEDIATE"
        }
    
    return match_dict

@app.get("/agents")
async def get_agents():
    """Get all agents with their current stats and divisions."""
    return [
        {
            "profile": {
                "agent_id": agent.profile.name,
                "name": agent.profile.name,
                "description": agent.profile.description,
                "specializations": agent.profile.specializations
            },
            "division": agent.division.value,
            "stats": agent.stats.__dict__
        }
        for agent in arena.agents
    ]

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent."""
    for agent in arena.agents:
        if agent.profile.name == agent_id:
            # Get recent matches for this agent
            recent_matches = [
                match_to_json(match)
                for match in arena.match_store.get_matches_for_agent(agent_id)
            ]
            
            return {
                "profile": {
                    "agent_id": agent.profile.name,
                    "name": agent.profile.name,
                    "description": agent.profile.description,
                    "specializations": agent.profile.specializations
                },
                "division": agent.division.value,
                "stats": agent.stats.__dict__,
                "match_history": recent_matches,
                "division_changes": agent.division_change_history
            }
    raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/matches")
async def get_matches():
    """Get recent matches from the arena state."""
    matches = arena.match_store.get_recent_matches(limit=10)
    return [match_to_json(match) for match in matches]

@app.get("/matches/live")
async def get_live_matches():
    """Get ongoing matches."""
    matches = arena.match_store.get_live_matches()
    return [match_to_json(match) for match in matches]

@app.get("/matches/{match_id}")
async def get_match(match_id: str):
    """Get details for a specific match."""
    match = arena.match_store.get_match(match_id)
    if match:
        return match_to_json(match)
    raise HTTPException(status_code=404, detail="Match not found")

@app.post("/matches/quick")
async def start_quick_match(division: str):
    """Start a quick match between two random agents in the specified division."""
    try:
        # Start the match asynchronously
        match = arena.start_quick_match(division)
        
        # Return immediately with the match info
        return match_to_json(match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tournament/start")
async def start_tournament(num_rounds: int = 1):
    """Start a new tournament round."""
    try:
        arena.run_tournament(num_rounds=num_rounds)
        arena.save_state()
        return {"message": f"Tournament completed with {num_rounds} rounds"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tournament/status")
async def get_tournament_status():
    """Get the current tournament status."""
    return {
        "total_agents": len(arena.agents),
        "divisions": {
            "KING": len([a for a in arena.agents if a.division.value == "king"]),
            "MASTER": len([a for a in arena.agents if a.division.value == "master"]),
            "EXPERT": len([a for a in arena.agents if a.division.value == "expert"]),
            "NOVICE": len([a for a in arena.agents if a.division.value == "novice"])
        },
        "total_matches": sum(a.stats.total_matches for a in arena.agents) // 2,
        "current_king": next((a.profile.name for a in arena.agents if a.division.value == "king"), None)
    } 