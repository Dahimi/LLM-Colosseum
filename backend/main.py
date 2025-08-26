from fastapi import FastAPI, HTTPException, Request, Header, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator, Dict, Any, List
import asyncio
import json
from datetime import datetime
import random
from typing import List, Optional
import os
from agent_arena.core.arena import Arena
from agent_arena.models.match import Match, MatchStatus, MatchType
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.models.agent import Division
from pydantic import BaseModel, Field
from agent_arena.db import supabase

app = FastAPI()

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["content-type", "content-length"],  # Required for SSE
)

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

arena = Arena()

# Pydantic model for agent configuration
class AgentConfig(BaseModel):
    name: str
    model: str
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    division: str
    specializations: List[str] = Field(default_factory=list)

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

@app.post("/admin/reload", dependencies=[Depends(verify_api_key)])
async def reload_data():
    """Admin endpoint to reload all data from the database.
    
    This endpoint should be called when changes are made directly to the database
    and need to be reflected in the running application.
    
    Requires admin API key authentication.
    """
    try:
        result = arena.reload_from_db()
        return {
            "success": True,
            "message": "Arena data reloaded successfully",
            "details": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reload arena data: {str(e)}",
            "error": str(e)
        }

# Agent Configuration Management Endpoints
@app.get("/admin/agent-configs", dependencies=[Depends(verify_api_key)])
async def get_agent_configs():
    """Get all agent configurations."""
    try:
        from agent_arena.db import supabase
        response = supabase.table("agent_configs").select("*").execute()
        return {
            "success": True,
            "configs": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get agent configurations: {str(e)}",
            "error": str(e)
        }

@app.get("/admin/agent-configs/{name}", dependencies=[Depends(verify_api_key)])
async def get_agent_config(name: str):
    """Get a specific agent configuration."""
    try:
        from agent_arena.db import supabase
        response = supabase.table("agent_configs").select("*").eq("name", name).execute()
        if not response.data:
            return {
                "success": False,
                "message": f"Agent configuration '{name}' not found"
            }
        return {
            "success": True,
            "config": response.data[0]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get agent configuration: {str(e)}",
            "error": str(e)
        }

@app.post("/admin/agent-configs", dependencies=[Depends(verify_api_key)])
async def create_agent_config(config: AgentConfig):
    """Create a new agent configuration."""
    try:
        # Check if config with this name already exists
        existing = supabase.table("agent_configs").select("*").eq("name", config.name).execute()
        if existing.data:
            return {
                "success": False,
                "message": f"Agent configuration with name '{config.name}' already exists"
            }
        
        # Insert new config
        config_dict = config.model_dump()
        supabase.table("agent_configs").insert(config_dict).execute()
        
        # Reload agent configs in arena
        arena.load_agent_configs_from_db()
        
        return {
            "success": True,
            "message": f"Agent configuration '{config.name}' created successfully",
            "config": config_dict
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create agent configuration: {str(e)}",
            "error": str(e)
        }

@app.put("/admin/agent-configs/{name}", dependencies=[Depends(verify_api_key)])
async def update_agent_config(name: str, config: AgentConfig):
    """Update an existing agent configuration."""
    try:
        # Check if config exists
        existing = supabase.table("agent_configs").select("*").eq("name", name).execute()
        if not existing.data:
            return {
                "success": False,
                "message": f"Agent configuration '{name}' not found"
            }
        
        # Update config
        config_dict = config.model_dump()
        supabase.table("agent_configs").update(config_dict).eq("name", name).execute()
        
        # Reload agent configs in arena
        arena.load_agent_configs_from_db()
        
        return {
            "success": True,
            "message": f"Agent configuration '{name}' updated successfully",
            "config": config_dict
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to update agent configuration: {str(e)}",
            "error": str(e)
        }

@app.delete("/admin/agent-configs/{name}", dependencies=[Depends(verify_api_key)])
async def delete_agent_config(name: str):
    """Delete an agent configuration."""
    try:
        # Check if config exists
        existing = supabase.table("agent_configs").select("*").eq("name", name).execute()
        if not existing.data:
            return {
                "success": False,
                "message": f"Agent configuration '{name}' not found"
            }
        
        # Delete config
        supabase.table("agent_configs").delete().eq("name", name).execute()
        
        # Reload agent configs in arena
        arena.load_agent_configs_from_db()
        
        return {
            "success": True,
            "message": f"Agent configuration '{name}' deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete agent configuration: {str(e)}",
            "error": str(e)
        }

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
            "stats": agent.stats.to_dict()
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
                "stats": agent.stats.to_dict(),
                "match_history": recent_matches,
                "division_changes": agent.division_change_history
            }
    raise HTTPException(status_code=404, detail="Agent not found")

# SSE endpoints must come before other /matches endpoints to avoid routing conflicts
@app.get("/matches/stream")
async def stream_matches(request: Request):
    """SSE endpoint for streaming match updates."""
    try:
        return EventSourceResponse(
            match_updates(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        print(f"Error setting up SSE stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def match_updates() -> AsyncGenerator[dict, None]:
    """Generate match updates for SSE."""
    while True:
        try:
            # Get current matches state
            matches = arena.match_store.get_recent_matches(limit=10)
            live_matches = arena.match_store.get_live_matches()
            
            # Create update payload
            payload = {
                "matches": [match_to_json(m) for m in matches],
                "liveMatches": [match_to_json(m) for m in live_matches]
            }
            
            yield {
                "event": "message",
                "data": json.dumps(payload),
                "retry": 15000  # Reconnect after 15s if connection lost
            }
        except Exception as e:
            print(f"Error in match_updates: {e}")
            yield {
                "event": "error",
                "data": str(e)
            }
        await asyncio.sleep(2)  # Wait 2 seconds between updates

@app.get("/matches/{match_id}/stream")
async def stream_match(match_id: str, request: Request):
    """SSE endpoint for streaming specific match updates."""
    try:
        return EventSourceResponse(
            specific_match_updates(match_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        print(f"Error setting up SSE stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def specific_match_updates(match_id: str) -> AsyncGenerator[dict, None]:
    """Generate updates for a specific match."""
    while True:
        try:
            match = arena.match_store.get_match(match_id)
            if match:
                yield {
                    "event": "message",
                    "data": json.dumps(match_to_json(match)),
                    "retry": 15000  # Reconnect after 15s if connection lost
                }
        except Exception as e:
            print(f"Error in specific_match_updates: {e}")
            yield {
                "event": "error",
                "data": str(e)
            }
        await asyncio.sleep(0.5)  # Very frequent updates for streaming responses

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