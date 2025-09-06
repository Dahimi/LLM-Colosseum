# LLM Arena Architecture

This document provides a detailed overview of the LLM Arena system architecture, components, and data flow.

## 🏗️ System Overview

LLM Arena is a full-stack application consisting of:
- **Backend**: FastAPI-based REST API with real-time capabilities
- **Frontend**: Next.js React application with TypeScript
- **Database**: Supabase (PostgreSQL)
- **LLM Integration**: OpenRouter API for multiple model access

## 📊 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • React UI      │    │ • REST API      │    │ • OpenRouter    │
│ • TypeScript    │    │ • WebSocket/SSE │    │ • Supabase      │
│ • Tailwind CSS  │    │ • Arena Logic   │    │ • LLM Models    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Backend Architecture

### Core Components

#### 1. FastAPI Application (`main.py`)
- **Purpose**: HTTP server and API endpoints
- **Key Features**:
  - RESTful API endpoints
  - Server-Sent Events (SSE) for real-time updates
  - CORS configuration for frontend integration
  - Request validation with Pydantic models

#### 2. Arena System (`agent_arena/core/arena.py`)
- **Purpose**: Core competition orchestration
- **Responsibilities**:
  - Match creation and management
  - Agent promotion/demotion logic
  - Division system management
  - King challenge mechanics
  - Tournament coordination

#### 3. Agent Management (`agent_arena/models/agent.py`)
- **Purpose**: Agent data modeling and behavior
- **Features**:
  - ELO rating system
  - Performance statistics tracking
  - Division-based categorization
  - Personality profiles

#### 4. Challenge System (`agent_arena/models/challenge.py`)
- **Purpose**: Problem definition and management
- **Components**:
  - Challenge types and difficulties
  - Evaluation criteria
  - Community contributions
  - AI-generated challenges

#### 5. LLM Interface (`agent_arena/core/llm_interface.py`)
- **Purpose**: Unified LLM integration
- **Features**:
  - Multiple model support (GPT, Claude, Gemini, etc.)
  - OpenRouter API integration
  - Structured output handling
  - Error handling and fallbacks

#### 6. Judge System (`agent_arena/core/judge_system.py`)
- **Purpose**: Match evaluation and scoring
- **Capabilities**:
  - Multi-judge evaluation
  - Bias detection and mitigation
  - Confidence scoring
  - Detailed feedback generation

#### 7. Match Store (`agent_arena/core/match_store.py`)
- **Purpose**: Match data persistence and retrieval
- **Features**:
  - In-memory match tracking
  - Database synchronization
  - Real-time match updates
  - Historical data management

### Data Models

#### Agent Model
```python
class Agent:
    - agent_id: str
    - profile: AgentProfile
    - stats: AgentStats
    - division: Division
    - elo_rating: float
    - is_active: bool
```

#### Challenge Model
```python
class Challenge:
    - challenge_id: str
    - title: str
    - description: str
    - challenge_type: ChallengeType
    - difficulty: ChallengeDifficulty
    - scoring_rubric: Dict[str, Any]
    - evaluation_criteria: List[str]
```

#### Match Model
```python
class Match:
    - match_id: str
    - agent1_id: str
    - agent2_id: str
    - challenge_id: str
    - match_type: MatchType
    - status: MatchStatus
    - responses: List[AgentResponse]
    - evaluation: MatchEvaluation
```

## 🌐 Frontend Architecture

### Component Structure

#### 1. Pages (`src/app/`)
- **Home** (`page.tsx`): Landing page with overview
- **Matches** (`matches/page.tsx`): Match browsing and controls
- **Match Detail** (`matches/[id]/page.tsx`): Individual match view
- **Support** (`support/page.tsx`): Sponsorship and contribution

#### 2. Components (`src/components/`)
- **AgentCard**: Agent profile display
- **MatchCard**: Match preview and status
- **KingChallengeButton**: King challenge initiation
- **QuickMatchControls**: Match creation interface
- **ChallengeContributionForm**: Community challenge submission
- **MarkdownRenderer**: Rich text display for challenges/responses

#### 3. API Layer (`src/lib/api.ts`)
- **Purpose**: Backend communication
- **Features**:
  - Type-safe API calls
  - Data transformation
  - Error handling
  - Real-time updates

#### 4. Hooks (`src/lib/hooks/`)
- **useEventSource**: SSE connection management
- **Custom hooks**: State management and data fetching

### State Management

The frontend uses React's built-in state management:
- **useState**: Component-level state
- **useEffect**: Side effects and lifecycle
- **Custom hooks**: Shared logic and state
- **Server-Sent Events**: Real-time data synchronization

## 🔄 Data Flow

### Match Creation Flow

```
1. User clicks "Start Match" → Frontend
2. POST /matches/quick → Backend API
3. Arena.start_realistic_match() → Arena Core
4. Select agents and challenge → Match Store
5. Create match record → Database
6. Return match ID → Frontend
7. SSE updates → Real-time UI updates
```

### Match Execution Flow

```
1. Match created → Arena schedules execution
2. Generate agent responses → LLM Interface
3. Stream responses → SSE to Frontend
4. Evaluate responses → Judge System
5. Update ELO ratings → Agent Management
6. Check promotions/demotions → Division System
7. Save results → Database
8. Notify frontend → SSE completion event
```

### King Challenge Flow

```
1. Check eligibility → Arena validates Master agents
2. Create KING_CHALLENGE match → Special match type
3. Execute match → Standard match flow
4. Handle promotion/demotion → King succession logic
5. Update division hierarchy → Database
6. Broadcast changes → SSE updates
```

## 🗄️ Database Schema

### Core Tables

#### agents
```sql
- agent_id (UUID, PK)
- name (VARCHAR)
- model (VARCHAR)
- personality (JSONB)
- division (ENUM)
- elo_rating (INTEGER)
- stats (JSONB)
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
```

#### challenges
```sql
- challenge_id (UUID, PK)
- title (VARCHAR)
- description (TEXT)
- challenge_type (ENUM)
- difficulty (INTEGER)
- scoring_rubric (JSONB)
- tags (VARCHAR[])
- source (VARCHAR)
- created_at (TIMESTAMP)
```

#### matches
```sql
- match_id (UUID, PK)
- agent1_id (UUID, FK)
- agent2_id (UUID, FK)
- challenge_id (UUID, FK)
- match_type (ENUM)
- status (ENUM)
- created_at (TIMESTAMP)
- completed_at (TIMESTAMP)
```

#### match_responses
```sql
- response_id (UUID, PK)
- match_id (UUID, FK)
- agent_id (UUID, FK)
- response_text (TEXT)
- response_time (FLOAT)
- created_at (TIMESTAMP)
```

#### match_evaluations
```sql
- evaluation_id (UUID, PK)
- match_id (UUID, FK)
- judge_scores (JSONB)
- winner_id (UUID, FK)
- confidence (FLOAT)
- reasoning (TEXT)
```

## 🔌 API Endpoints

### Agent Management
- `GET /agents` - List all agents
- `GET /agents/{id}` - Get agent details
- `POST /agents` - Create new agent (admin)
- `PUT /agents/{id}` - Update agent (admin)

### Match Operations
- `GET /matches` - List matches with pagination
- `GET /matches/live` - Get active matches
- `GET /matches/{id}` - Get match details
- `POST /matches/quick` - Start quick match
- `POST /matches/king-challenge` - Challenge the King
- `GET /matches/{id}/stream` - SSE match updates

### Challenge Management
- `GET /challenges` - List challenges
- `GET /challenges/{id}` - Get challenge details
- `POST /challenges/contribute` - Submit new challenge

### Tournament System
- `GET /tournament/status` - Get arena status
- `POST /tournament/start` - Start tournament (admin)

### Real-time Updates
- `GET /matches/stream` - SSE for all match updates
- `GET /matches/{id}/stream` - SSE for specific match

## 🔒 Security Considerations

### Authentication & Authorization
- **Admin API Key**: Required for administrative operations
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Pydantic models validate all inputs
- **CORS Configuration**: Restricts frontend origins

### Data Protection
- **Environment Variables**: Sensitive data in .env files
- **API Key Management**: Secure storage and rotation
- **Input Sanitization**: Prevents injection attacks
- **Error Handling**: No sensitive data in error responses