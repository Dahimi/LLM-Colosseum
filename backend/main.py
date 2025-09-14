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
from agent_arena.models.match import Match
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
import uuid
from agent_arena.models.agent import Division
from pydantic import BaseModel, Field
from agent_arena.db import supabase
from fastapi.responses import JSONResponse
from agent_arena.utils.logging import setup_logging
import logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Colosseum API",
    description="""
# LLM Colosseum API

A competitive platform where LLM models battle in intellectual challenges using AI-powered evaluation.

## Features

* **Model Management**: View models, their stats, and division rankings
* **Match System**: Start quick matches, king challenges, and view match history  
* **Real-time Updates**: Server-Sent Events (SSE) for live match streaming
* **Challenge Contributions**: Submit custom challenges for models to solve
* **Tournament Status**: Track the kingdom hierarchy and current king

## Authentication

Most endpoints are public. Admin endpoints require an API key via `X-API-Key` header.

## Rate Limits

- Maximum 2 concurrent live matches
- SSE connections have automatic reconnection with 15s retry

## Model Divisions

1. **Novice** → **Expert** → **Master** → **King**
2. Models are promoted/demoted based on performance
3. Only Master models can challenge the King

## Match Types

- **Quick Match**: Random models from same division
- **King Challenge**: Master vs current King
- **Community Challenge**: Test user-contributed challenges
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "LLM Colosseum",
        "url": "https://github.com/Dahimi/LLM-Colosseum",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/Dahimi/LLM-Colosseum/blob/main/LICENSE",
    },
)

# Define allowed origins
ALLOWED_ORIGINS = [
    "https://llmcolosseum.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["content-type", "content-length"],  # Required for SSE
)

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")


async def verify_access(request: Request, x_api_key: Optional[str] = Header(None)):
    """
    Dependency to verify access via API key or Origin header.

    This function checks two conditions:
    1. If a valid `X-API-Key` is present.
    2. If the request's `Origin` header is in the `ALLOWED_ORIGINS` list.

    Access is granted if either condition is met. This secures the API
    from unauthorized scripts while allowing the frontend to operate
    without an API key.
    """
    # Grant access if a valid, non-empty API key is provided
    if x_api_key and x_api_key == ADMIN_API_KEY:
        return

    # Grant access if the request is from an allowed origin
    origin = request.headers.get("origin")
    if origin and origin in ALLOWED_ORIGINS:
        return

    # If neither condition is met, deny access
    raise HTTPException(
        status_code=403,
        detail="Access denied. Provide a valid API key or access from an allowed origin.",
    )


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
        if field in match_dict and hasattr(match_dict[field], "isoformat"):
            match_dict[field] = match_dict[field].isoformat()

    # Convert status to uppercase to match frontend enum
    match_dict["status"] = match_dict["status"].upper()

    # Add challenge details from the match store's cache
    challenge = arena.match_store.get_challenge_for_match(match.challenge_id)
    if challenge:
        match_dict["challenge"] = {
            "challenge_id": challenge.challenge_id,
            "title": challenge.title,
            "description": challenge.description,
            "type": challenge.challenge_type.value.upper(),
            "difficulty": challenge.difficulty.value,
            "source": challenge.source,
            "answer": challenge.answer,
            "tags": challenge.tags,
        }
    else:
        # Provide default challenge data if not found
        match_dict["challenge"] = {
            "challenge_id": match.challenge_id,
            "title": "Challenge",
            "description": "Challenge description",
            "type": "LOGICAL_REASONING",
            "difficulty": "INTERMEDIATE",
            "source": "unknown",
            "answer": None,
            "tags": [],
        }

    # Ensure evaluation_details is included
    if hasattr(match, "evaluation_details") and match.evaluation_details:
        match_dict["evaluation_details"] = match.evaluation_details

    return match_dict


@app.post(
    "/admin/reload",
    dependencies=[Depends(verify_access)],
    tags=["Admin"],
    summary="Reload data",
)
async def reload_data():
    """
    Admin endpoint to reload all data from the database.

    **Requires admin API key** via X-API-Key header.

    Use this when changes are made directly to the database
    and need to be reflected in the running application.
    """
    try:
        result = arena.reload_from_db()
        return {
            "success": True,
            "message": "Arena data reloaded successfully",
            "details": result,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reload arena data: {str(e)}",
            "error": str(e),
        }


@app.get(
    "/agents",
    tags=["Models"],
    summary="Get all models",
    dependencies=[Depends(verify_access)],
)
async def get_agents():
    """
    Get all models with their current stats and divisions.

    Returns a list of all models in the colosseum with:
    - Profile information (name, description, specializations)
    - Current division (Novice, Expert, Master, King)
    - Performance statistics (ELO, wins, losses, streaks)
    """
    return [
        {
            "profile": {
                "agent_id": agent.profile.name,
                "name": agent.profile.name,
                "description": agent.profile.description,
                "specializations": agent.profile.specializations,
            },
            "division": agent.division.value,
            "stats": agent.stats.to_dict(),
        }
        for agent in arena.agents
    ]


@app.get(
    "/agents/{agent_id}",
    tags=["Models"],
    summary="Get model details",
    dependencies=[Depends(verify_access)],
)
async def get_agent(agent_id: str):
    """
    Get detailed information for a specific model.

    Includes:
    - Complete profile and stats
    - Recent match history
    - Division change history
    """
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
                    "specializations": agent.profile.specializations,
                },
                "division": agent.division.value,
                "stats": agent.stats.to_dict(),
                "match_history": recent_matches,
                "division_changes": agent.division_change_history,
            }
    raise HTTPException(status_code=404, detail="Agent not found")


# SSE endpoints must come before other /matches endpoints to avoid routing conflicts
@app.get("/matches/stream", tags=["Real-time"], summary="Stream match updates")
async def stream_matches(request: Request):
    """
    Server-Sent Events endpoint for real-time match updates.

    Streams:
    - Recent matches (last 100)
    - Currently live matches
    - Updates every 2 seconds

    Use EventSource in JavaScript to connect to this endpoint.
    """
    try:
        # Get the origin from the request headers or use the first allowed origin as default
        origin = request.headers.get("origin", ALLOWED_ORIGINS[0])
        # Ensure the origin is in our allowed list
        if origin not in ALLOWED_ORIGINS:
            origin = ALLOWED_ORIGINS[0]

        return EventSourceResponse(
            match_updates(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "X-Accel-Buffering": "no",  # Prevent proxy buffering
            },
        )
    except Exception as e:
        logger.error(f"Error setting up SSE stream: {e}")
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
                "liveMatches": [match_to_json(m) for m in live_matches],
            }

            yield {
                "event": "message",
                "data": json.dumps(payload),
                "retry": 15000,  # Reconnect after 15s if connection lost
            }
        except Exception as e:
            logger.error(f"Error in match_updates: {e}")
            yield {"event": "error", "data": str(e)}
        await asyncio.sleep(2)  # Wait 2 seconds between updates


@app.get(
    "/matches/{match_id}/stream", tags=["Real-time"], summary="Stream specific match"
)
async def stream_match(match_id: str, request: Request):
    """
    Server-Sent Events endpoint for streaming a specific match.

    Provides real-time updates for a single match including:
    - Match status changes
    - Model responses as they're generated
    - Evaluation results

    Updates every 0.5 seconds for responsive streaming.
    """
    try:
        # Get the origin from the request headers or use the first allowed origin as default
        origin = request.headers.get("origin", ALLOWED_ORIGINS[0])
        # Ensure the origin is in our allowed list
        if origin not in ALLOWED_ORIGINS:
            origin = ALLOWED_ORIGINS[0]

        return EventSourceResponse(
            specific_match_updates(match_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "X-Accel-Buffering": "no",  # Prevent proxy buffering
            },
        )
    except Exception as e:
        logger.error(f"Error setting up SSE stream: {e}")
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
                    "retry": 15000,  # Reconnect after 15s if connection lost
                }
        except Exception as e:
            logger.error(f"Error in specific_match_updates: {e}")
            yield {"event": "error", "data": str(e)}
        await asyncio.sleep(0.5)  # Very frequent updates for streaming responses


@app.get(
    "/matches",
    tags=["Matches"],
    summary="Get recent matches",
    dependencies=[Depends(verify_access)],
)
async def get_matches():
    """Get the 10 most recent matches from the colosseum."""
    matches = arena.match_store.get_recent_matches(limit=10)
    return [match_to_json(match) for match in matches]


@app.get(
    "/matches/live",
    tags=["Matches"],
    summary="Get live matches",
    dependencies=[Depends(verify_access)],
)
async def get_live_matches():
    """Get all currently ongoing matches."""
    matches = arena.match_store.get_live_matches()
    return [match_to_json(match) for match in matches]


@app.get(
    "/matches/{match_id}",
    tags=["Matches"],
    summary="Get match details",
    dependencies=[Depends(verify_access)],
)
async def get_match(match_id: str):
    """
    Get detailed information for a specific match.

    Includes:
    - Match participants and challenge
    - Current status and responses
    - Evaluation details if completed
    """
    match = arena.match_store.get_match(match_id)
    if match:
        return match_to_json(match)
    raise HTTPException(status_code=404, detail="Match not found")


@app.post(
    "/matches/quick",
    tags=["Matches"],
    summary="Start quick match",
    dependencies=[Depends(verify_access)],
)
async def start_quick_match(
    division: str,
    agent1_id: Optional[str] = None,
    agent2_id: Optional[str] = None
):
    """
    Start a quick match between models in the specified division.

    **Parameters:**
    - division: "novice", "expert", "master", or "king"
    - agent1_id: (Optional) Specific model ID for first participant
    - agent2_id: (Optional) Specific model ID for second participant
    
    **Behavior:**
    - If both agent IDs provided: Start match between those specific models
    - If no agent IDs provided: Random selection (default behavior)
    - Both agents must be in the specified division

    **Rate Limits:**
    - Maximum 20 concurrent live matches
    - Returns 429 if limit exceeded
    """
    try:
        # Check if we've reached the maximum number of live matches
        if arena.match_store.has_reached_live_match_limit():
            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_matches",
                    "message": f"Maximum number of live matches ({arena.match_store.max_live_matches}) reached. Please wait for some matches to complete.",
                    "live_match_count": len(arena.match_store.live_matches),
                    "max_live_matches": arena.match_store.max_live_matches,
                },
            )

        # Start the match asynchronously (with optional agent selection)
        match = arena.start_quick_match(division, agent1_id, agent2_id)

        # Return immediately with the match info
        return match_to_json(match)
    except ValueError as e:
        if "Maximum number of live matches" in str(e):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_matches",
                    "message": str(e),
                    "live_match_count": len(arena.match_store.live_matches),
                    "max_live_matches": arena.match_store.max_live_matches,
                },
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/matches/king-challenge",
    tags=["Matches"],
    summary="Start king challenge",
    dependencies=[Depends(verify_access)],
)
async def start_king_challenge():
    """
    Start a king challenge match between the current king and the best performing master.

    **Requirements:**
    - Must have a current king
    - Must have eligible master models
    - Respects live match limits
    """
    try:
        # Check if we've reached the maximum number of live matches
        if arena.match_store.has_reached_live_match_limit():
            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_matches",
                    "message": f"Maximum number of live matches ({arena.match_store.max_live_matches}) reached. Please wait for some matches to complete.",
                    "live_match_count": len(arena.match_store.live_matches),
                    "max_live_matches": arena.match_store.max_live_matches,
                },
            )

        # Start the king challenge match
        match = arena.start_king_challenge()

        # Return immediately with the match info
        return match_to_json(match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Challenge Contribution Endpoint
@app.post(
    "/challenges/contribute",
    tags=["Challenges"],
    summary="Contribute a challenge",
    dependencies=[Depends(verify_access)],
)
async def contribute_challenge(challenge_data: dict = Body(...)):
    """
    Accept a user-contributed challenge and start a test match.

    **Request Body:**
    ```json
    {
        "title": "Challenge title",
        "description": "Detailed challenge description",
        "type": "LOGICAL_REASONING",
        "difficulty": "INTERMEDIATE",
        "division": "expert",
        "answer": "Expected answer (optional)",
        "tags": ["logic", "reasoning"],
        "agent1_id": "Optional specific model for test match",
        "agent2_id": "Optional specific model for test match",
        "metadata": {
            "contributor_name": "Your name",
            "contributor_email": "your@email.com"
        }
    }
    ```

    **Challenge Types:**
    - LOGICAL_REASONING
    - DEBATE
    - CREATIVE_PROBLEM_SOLVING
    - MATHEMATICAL
    - ABSTRACT_THINKING

    **Difficulties:**
    - BEGINNER, INTERMEDIATE, ADVANCED, EXPERT, MASTER

    **Test Match:**
    - If agent1_id and agent2_id provided: Uses specific models
    - If not provided: Random selection from division
    - Automatically starts a test match if possible.
    """
    try:

        # Validate required fields
        required_fields = ["title", "description", "type", "difficulty", "division"]
        for field in required_fields:
            if field not in challenge_data or not challenge_data[field]:
                raise HTTPException(
                    status_code=400, detail=f"Missing required field: {field}"
                )

        # Create challenge object
        challenge_id = str(uuid.uuid4())

        # Map difficulty string to enum
        difficulty_mapping = {
            "BEGINNER": ChallengeDifficulty.BEGINNER,
            "INTERMEDIATE": ChallengeDifficulty.INTERMEDIATE,
            "ADVANCED": ChallengeDifficulty.ADVANCED,
            "EXPERT": ChallengeDifficulty.EXPERT,
            "MASTER": ChallengeDifficulty.MASTER,
        }

        # Map challenge type string to enum
        type_mapping = {
            "LOGICAL_REASONING": ChallengeType.LOGICAL_REASONING,
            "DEBATE": ChallengeType.DEBATE,
            "CREATIVE_PROBLEM_SOLVING": ChallengeType.CREATIVE_PROBLEM_SOLVING,
            "MATHEMATICAL": ChallengeType.MATHEMATICAL,
            "ABSTRACT_THINKING": ChallengeType.ABSTRACT_THINKING,
        }

        challenge_type = type_mapping.get(challenge_data["type"])
        difficulty = difficulty_mapping.get(challenge_data["difficulty"])

        if not challenge_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid challenge type: {challenge_data['type']}",
            )
        if not difficulty:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid difficulty: {challenge_data['difficulty']}",
            )

        challenge = Challenge(
            challenge_id=challenge_id,
            title=challenge_data["title"],
            description=challenge_data["description"],
            challenge_type=challenge_type,
            difficulty=difficulty,
            scoring_rubric={
                "criteria": "Standard evaluation criteria",
                "max_score": 10,
                "dimensions": ["correctness", "completeness", "clarity", "creativity"],
            },
            tags=challenge_data.get("tags", []),
            source=challenge_data.get("source", "community"),
            is_active=True,
            metadata=challenge_data.get("metadata", {}),
            answer=challenge_data.get("answer", ""),
        )

        # Save challenge to database
        try:
            challenge_dict = {
                "challenge_id": challenge.challenge_id,
                "title": challenge.title,
                "description": challenge.description,
                "challenge_type": challenge.challenge_type.value,
                "difficulty": challenge.difficulty.value,
                "scoring_rubric": challenge.scoring_rubric,
                "tags": challenge.tags,
                "source": challenge.source,
                "is_active": challenge.is_active,
                "metadata": challenge.metadata,
                "answer": challenge.answer,
            }
            supabase.table("challenges").insert(challenge_dict).execute()
            logger.info(f"Saved contributed challenge to database: {challenge.title}")
        except Exception as e:
            logger.error(f"Error saving challenge to database: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to save challenge to database"
            )

        # Add challenge to arena's cache
        arena.match_store.add_challenge(challenge)

        # Start a test match with the contributed challenge
        division = challenge_data.get("division", "expert").lower()

        # Check if we've reached the maximum number of live matches
        if arena.match_store.has_reached_live_match_limit():
            return JSONResponse(
                status_code=200,  # Still success since challenge was saved
                content={
                    "success": True,
                    "message": f"Challenge '{challenge.title}' saved successfully! Test match will start when slots are available.",
                    "challenge_id": challenge.challenge_id,
                    "match_id": None,
                    "note": "Maximum live matches reached - test match queued",
                },
            )

        # Get active agents in the specified division
        division_agents = [
            agent
            for agent in arena.agents
            if agent.division.value.lower() == division and agent.profile.is_active
        ]

        if len(division_agents) < 2:
            return JSONResponse(
                status_code=200,  # Still success since challenge was saved
                content={
                    "success": True,
                    "message": f"Challenge '{challenge.title}' saved successfully! Not enough agents in {division} division for test match.",
                    "challenge_id": challenge.challenge_id,
                    "match_id": None,
                    "note": f"Need at least 2 active agents in {division} division",
                },
            )

        # Agent selection for test match
        agent1_id = challenge_data.get("agent1_id")
        agent2_id = challenge_data.get("agent2_id")
        
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
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": f"Agent '{agent1_id}' not found in {division} division or not active",
                        "challenge_id": challenge.challenge_id,
                    },
                )
            if not agent2:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": f"Agent '{agent2_id}' not found in {division} division or not active",
                        "challenge_id": challenge.challenge_id,
                    },
                )
            if agent1_id == agent2_id:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "Cannot start a test match between the same agent",
                        "challenge_id": challenge.challenge_id,
                    },
                )
        else:
            # Random selection (default behavior)
            import random
            agent1, agent2 = random.sample(division_agents, 2)

        # Create and start the test match
        match = arena.start_match_async(agent1, agent2, challenge)

        return {
            "success": True,
            "message": f"Challenge '{challenge.title}' submitted and test match started!",
            "challenge_id": challenge.challenge_id,
            "match_id": match.match_id,
            "test_match": match_to_json(match),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in challenge contribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/tournament/start",
    tags=["Tournament"],
    summary="Start tournament",
    dependencies=[Depends(verify_access)],
)
async def start_tournament(num_rounds: int = 1):
    """
    Start a new tournament round.

    **Admin endpoint** - requires API key authentication.
    """
    try:
        arena.run_tournament(num_rounds=num_rounds)
        arena.save_state()
        return {"message": f"Tournament completed with {num_rounds} rounds"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/tournament/status",
    tags=["Tournament"],
    summary="Get tournament status",
    dependencies=[Depends(verify_access)],
)
async def get_tournament_status():
    """
    Get the current tournament status and kingdom hierarchy.

    Returns:
    - Total models and division distribution
    - Current king and their stats
    - Top eligible challengers (Master models)
    - Total matches played
    """
    # Find the current king
    king = next((a for a in arena.agents if a.division.value == "king"), None)

    # Find eligible challengers (Masters with high ratings)
    eligible_challengers = []
    if king:
        masters = [
            a
            for a in arena.agents
            if a.division.value == "master" and a.profile.is_active
        ]
        # Sort by ELO rating
        masters.sort(key=lambda a: a.stats.elo_rating, reverse=True)
        eligible_challengers = [
            {
                "name": a.profile.name,
                "elo_rating": a.stats.elo_rating,
                "win_rate": a.stats.win_rate,
                "current_streak": a.stats.current_streak,
            }
            for a in masters[:3]  # Top 3 challengers
        ]

    return {
        "total_agents": len(arena.agents),
        "divisions": {
            "KING": len([a for a in arena.agents if a.division.value == "king"]),
            "MASTER": len([a for a in arena.agents if a.division.value == "master"]),
            "EXPERT": len([a for a in arena.agents if a.division.value == "expert"]),
            "NOVICE": len([a for a in arena.agents if a.division.value == "novice"]),
        },
        "total_matches": sum(a.stats.total_matches for a in arena.agents) // 2,
        "current_king": king.profile.name if king else None,
        "king_stats": (
            {
                "elo_rating": king.stats.elo_rating,
                "win_rate": king.stats.win_rate,
                "total_matches": king.stats.total_matches,
                "current_streak": king.stats.current_streak,
            }
            if king
            else None
        ),
        "eligible_challengers": eligible_challengers,
    }
