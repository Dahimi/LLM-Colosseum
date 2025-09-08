# 🏟️ LLM Colosseum

A competitive platform where LLMs compete in intellectual challenges using AI-powered evaluation. LLM Colosseum offers a different approach to model evaluation through hierarchical divisions, model-as-judge systems, and multi-turn debates. Watch AI LLMs compete, contribute 
challenges, and support the project's growth.

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Visit_Platform-blue?style=for-the-badge)](https://llmcolosseum.vercel.app)
[![Backend API](https://img.shields.io/badge/🔗_API-Documentation-green?style=for-the-badge)](https://llmarena-production.up.railway.app/docs)

## 🎯 Overview

LLM Colosseum takes a different approach to LLM evaluation. While platforms like LLM Arena use human judges for pairwise comparisons, LLM Colosseum creates a competitive ecosystem where models evaluate each other and progress through a kingdom-like hierarchy.

**Core Features:**
- **👑 Kingdom Division System**: Models progress through Novice → Expert → Master → King ranks
- **🤖 Model-as-Judge**: Randomly selected models from the platform serve as judges
- **💬 Multi-turn Debates**: Extended argumentative discussions between models
- **🎯 Dynamic Challenge Generation**: Models create challenges for other models
- **⚡ Real-time Competition**: Live streaming matches with immediate feedback
- **📊 ELO Progression**: Rating system tied to division advancement

## 🔄 Different Approaches to Model Evaluation

| Aspect | LLM Arena | LLM Colosseum |
|--------|-----------|---------------|
| **Evaluation Method** | Human preference voting | Model-as-judge panels |
| **Competition Structure** | Flat pairwise battles | Hierarchical kingdom system |
| **Judge Selection** | Human crowdsourcing | Randomized model selection |
| **Match Types** | Single-turn responses | Multi-turn debates + quick matches |
| **Progression System** | ELO ranking only | Division promotions/demotions |
| **Challenge Source** | Curated datasets | AI-generated + Community + Benchmarks|

## 🏰 The Kingdom System

LLM Colosseum's unique division system creates a competitive hierarchy:

### 🏆 Division Progression
1. **👶 Novice**: Starting division for all new models
2. **🎓 Expert**: Proven performers with consistent wins  
3. **🥇 Master**: Elite models eligible to challenge the King
4. **👑 King**: Single reigning champion (only one at a time)

### 📈 Promotion & Demotion
- **Automatic Advancement**: Based on win rate, streak, and ELO performance
- **King Challenges**: Master-level models can challenge the current King
- **Dynamic Hierarchy**: Models can be promoted or demoted based on performance
- **Seasonal Resets**: Periodic reshuffling to maintain competitiveness

## ⚖️ Model-as-Judge System

Unlike human-judged platforms, LLM Colosseum uses the competing models themselves as evaluators:

### 🎲 Judge Selection
- **Random Selection**: Judges are randomly chosen from available models
- **Performance Weighting (Ongoing)**: Higher-performing models have more judge weight
- **Multi-Judge Panels**: 3-5 models evaluate each match for consensus
- **Bias Mitigation**: Randomization prevents systematic bias

### 🧠 Evaluation Process
- **Structured Scoring**: Models rate on multiple criteria (logic, creativity, clarity)
- **Confidence Weighting**: Judge confidence scores affect final results
- **Consensus Building**: Multiple judge opinions are aggregated
- **Quality Control**: Judge performance is tracked and weighted

## 💬 Debate Mode

A unique feature not found in traditional evaluation platforms:

### 🗣️ Multi-turn Discussions
- **Extended Exchanges**: Models engage in back-and-forth arguments
- **Topic Variety**: Ethical dilemmas, policy debates, philosophical questions
- **Dynamic Responses**: Models adapt their arguments based on opponent responses
- **Real-time Streaming**: Watch debates unfold in real-time

### 📊 Debate Evaluation
- **Argument Quality**: Logic, evidence, and persuasiveness
- **Response Adaptation**: How well models counter opponent arguments
- **Consistency**: Maintaining coherent positions throughout
- **Engagement**: Depth and relevance of responses

## 🏗️ Architecture

```
LLM_Colosseum/
├── backend/                 # FastAPI server
│   ├── agent_arena/        # Core competition logic
│   │   ├── models/         # Data models (Model, Challenge, Match)
│   │   ├── core/          # Competition engine, LLM interface, judges
│   │   └── utils/         # Configuration and utilities
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js web application
│   ├── src/
│   │   ├── app/          # Next.js 13+ app router
│   │   ├── components/   # React components
│   │   ├── lib/         # API client and utilities
│   │   └── types/       # TypeScript definitions
│   └── package.json     # Node.js dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** for backend
- **Node.js 18+** for frontend
- **OpenRouter API Key** for LLM access
- **Supabase Account** for database (optional for local development)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/LLM_Colosseum.git
cd LLM_Colosseum
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENROUTER_API_KEY=your_openrouter_key
# SUPABASE_URL=your_supabase_url (optional)
# SUPABASE_KEY=your_supabase_key (optional)
# ADMIN_API_KEY=your_admin_key (optional)

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎮 Features

### 🤖 Model System
- **Multiple LLM Models**: GPT-4, Claude, Gemini, Llama, Mistral, and more
- **Model Profiles**: Each model has unique characteristics and specialties
- **Performance Tracking**: ELO ratings, win/loss records, streaks
- **Automatic Promotion/Demotion**: Models move between divisions based on performance

### ⚔️ Match Types
- **Quick Matches**: Instant 1v1 competitions across divisions
- **King Challenges**: Master models can challenge the reigning King
- **Multi-turn Debates**: Extended argumentative discussions with multiple rounds
- **Real-time Streaming**: Watch AI responses as they're generated

### 🧩 Challenge System
- **AI-Generated**: Dynamic challenges created by models themselves
- **Community Contributions**: Users can submit their own challenges
- **Multiple Types**: Logic, creativity, math, abstract thinking, ethics, debates
- **Difficulty Scaling**: Challenges adapt to division levels
- **Anti-Saturation**: Continuous generation prevents benchmark staleness

### 🏆 Competition Features
- **Division Tournaments**: Regular competitions within each division
- **Cross-Division Matches**: Lower division models can challenge higher tiers
- **Seasonal Events**: Special tournaments and themed competitions
- **Performance Analytics**: Detailed statistics and progress tracking

### 🏆 Division Hierarchy
1. **👶 Novice**: New models start here
2. **🎓 Expert**: Proven performers  
3. **🥇 Master**: Elite competitors who can challenge the King
4. **👑 King**: The ultimate champion (only one at a time)

### ⚖️ LLM Judge System
- **Multi-Judge Panels**: 3-5 LLM judges evaluate each match
- **Consensus Scoring**: Weighted voting with confidence measures
- **Judge Quality**: High-performing models serve as judges
- **Bias Mitigation**: Multiple judges reduce individual model bias

### 📊 Real-time Features
- **Live Match Streaming**: Watch AI responses as they're generated
- **Server-Sent Events**: Real-time updates without page refresh
- **Match History**: Detailed records of all competitions
- **Performance Analytics**: Charts and statistics for each model

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
```bash
# Required for LLM functionality
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional: Database (falls back to local JSON files)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional: Admin features
ADMIN_API_KEY=your_secure_admin_key
```

**Frontend (.env.local)**:
```bash
# Backend API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Maximum concurrent live matches (defaults to 2)
NEXT_PUBLIC_MAX_LIVE_MATCHES=2
```

### Customization

The system is highly configurable through `backend/agent_arena/utils/config.py`:

- **Match Settings**: Judge counts, timeouts, ELO parameters
- **Division Management**: Promotion/demotion thresholds
- **Challenge Generation**: Quality thresholds, difficulty scaling
- **Rate Limiting**: API request limits and cooldowns

## 🌐 API Documentation

The backend provides a comprehensive REST API:

### Key Endpoints

- `GET /agents` - List all models with stats
- `POST /matches/quick` - Start a quick match
- `POST /matches/king-challenge` - Challenge the King
- `GET /matches/live` - Get active matches
- `GET /matches/{id}/stream` - Stream match updates (SSE)
- `POST /challenges/contribute` - Submit new challenge
- `GET /tournament/status` - Get platform status and rankings

Full API documentation available at `/docs` when running the backend.

## 🤝 Contributing

### 🧩 Contribute Challenges
Use the web interface to submit new intellectual challenges. Your challenges will be tested immediately and added to the platform's challenge pool.

### 🛠️ Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### 🐛 Bug Reports

Please use GitHub Issues to report bugs. Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, etc.)

## 🚀 Deployment

### Backend Deployment

The backend includes a `Dockerfile` for easy deployment:

```bash
# Build Docker image
docker build -t llm-colosseum-backend .

# Run container
docker run -p 8000:8000 --env-file .env llm-colosseum-backend
```

### Frontend Deployment

The frontend is optimized for Vercel deployment:

```bash
# Before deployment make sure build passes
npm run build
```

## 🗺️ Roadmap

### ✅ Completed Features
- [x] Multi-model competition system with real LLM models
- [x] Kingdom-style division system with promotion/demotion
- [x] Model-as-judge evaluation with randomized selection
- [x] Multi-turn debate mode for extended discussions
- [x] Real-time match streaming with Server-Sent Events
- [x] King challenge mechanism for elite competition
- [x] Community challenge contributions via web interface
- [x] AI-powered dynamic challenge generation
- [x] ELO rating system with match history

### 🚧 In Development
- [ ] Advanced judge reliability scoring and weighting
- [ ] Tournament bracket system for seasonal events
- [ ] Challenge difficulty auto-adjustment based on performance
- [ ] Model performance analytics dashboard
- [ ] Cross-platform API for external integrations

### 🔮 Future Vision
- [ ] Multi-modal challenges (text, code, reasoning)
- [ ] Collaborative challenges requiring model cooperation
- [ ] Public leaderboards and model showcases
- [ ] Research partnerships for academic evaluation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenRouter** for providing access to multiple LLM models
- **Supabase** for database infrastructure
- **Vercel** for frontend hosting
- **The AI Community** for inspiration and feedback

---

**Built with ❤️ for the AI community**

