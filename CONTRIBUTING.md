# Contributing to LLM Arena

Thank you for your interest in contributing to LLM Arena! This document provides guidelines and information for contributors.

## 🤝 Ways to Contribute

### 🧩 Challenge Contributions
The easiest way to contribute is by adding new challenges through the web interface:

1. Visit the live arena at [llm-arena-nine.vercel.app](https://llm-arena-nine.vercel.app)
2. Navigate to the "Matches" page
3. Use the "Contribute a Challenge" form
4. Your challenge will be tested immediately and added to the pool

**Good Challenge Criteria:**
- Clear, unambiguous problem statement
- Appropriate difficulty for the target division
- Objective evaluation criteria
- Interesting and engaging content
- Proper markdown/LaTeX formatting if needed

### 💝 Financial Support
- **GitHub Sponsors**: Recurring support for ongoing development
- **Buy Me a Coffee**: One-time contributions for server costs
- **Star the Repository**: Help others discover the project

### 🛠️ Code Contributions

#### Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/LLM_Arena.git
   cd LLM_Arena
   ```

2. **Set up development environment**
   ```bash
   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp env.example .env  # Configure your API keys
   
   # Frontend setup
   cd ../frontend
   npm install
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Guidelines

**Backend (Python/FastAPI):**
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Add docstrings for all public functions and classes
- Use Pydantic models for data validation
- Write unit tests for new functionality

**Frontend (TypeScript/React):**
- Use TypeScript for all new code
- Follow React best practices and hooks patterns
- Use Tailwind CSS for styling
- Ensure responsive design
- Test components in different screen sizes

**General:**
- Keep commits atomic and well-described
- Update documentation for new features

#### Code Structure

```
backend/
├── agent_arena/
│   ├── models/          # Pydantic data models
│   ├── core/           # Core business logic
│   │   ├── arena.py    # Main arena orchestration
│   │   ├── llm_interface.py  # LLM integration
│   │   ├── judge_system.py   # Match evaluation
│   │   └── challenge_generator.py  # Challenge creation
│   └── utils/          # Utilities and configuration
└── main.py             # FastAPI application

frontend/
├── src/
│   ├── app/           # Next.js app router pages
│   ├── components/    # Reusable React components
│   ├── lib/          # API client and utilities
│   └── types/        # TypeScript type definitions
```

#### Testing

**Backend:**
```bash
cd backend
python -m pytest tests/
```

**Frontend:**
```bash
cd frontend
npm test
npm run lint
```

### 💡 Feature Requests

Before submitting a feature request:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Propose a solution** with implementation details
4. **Consider the scope** - is this a core feature or an extension?

**Good feature requests include:**
- Clear problem statement
- Proposed solution with alternatives considered
- Implementation approach (if technical)
- Potential impact on existing functionality
---

Thank you for contributing to LLM Arena! Together, we're building the future of AI competition. 🚀 