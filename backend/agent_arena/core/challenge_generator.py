"""Dynamic challenge generation using LLMs for the Intelligence Arena System."""

import random
from typing import List, Optional
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.core.llm_interface import (
    create_system_llm,
    create_structured_llm,
    create_challenge_generator_llm,
    ChallengeResponse,
)


class ChallengeGenerator:
    """Generates challenges dynamically using LLMs."""

    def __init__(self, agents=None, agent_llms=None):
        """Initialize the challenge generator with an LLM."""
        # Create challenge generator LLM using best agents or fallback to system LLM
        llm, creator_name = create_challenge_generator_llm(agents, agent_llms)

        self.llm = llm
        self.creator_name = creator_name
        self.structured_llm = create_structured_llm(self.llm, ChallengeResponse)

    def generate_challenge(
        self,
        challenge_type: ChallengeType,
        difficulty: ChallengeDifficulty,
        creator_id: Optional[str] = None,
    ) -> Challenge:
        """Generate a new challenge of the specified type and difficulty."""

        # Create a detailed prompt for challenge generation
        prompt = self._create_generation_prompt(challenge_type, difficulty)

        response = self.structured_llm.invoke(prompt)
        # Create the Challenge object
        challenge = Challenge(
            title=response.title,
            description=response.description,
            challenge_type=challenge_type,
            difficulty=difficulty,
            creator_id=creator_id or self.creator_name,
            evaluation_criteria=response.evaluation_criteria,
            expected_concepts=response.expected_concepts,
            answer=response.answer,  # Include the answer field from the response
            tags=[challenge_type.value, f"difficulty_{difficulty.value}"],
        )

        return challenge

    def generate_challenge_batch(
        self,
        challenge_types: List[ChallengeType],
        difficulties: List[ChallengeDifficulty],
        creator_ids: Optional[List[str]] = None,
    ) -> List[Challenge]:
        """Generate multiple challenges in batch."""
        if creator_ids is None:
            creator_ids = [self.creator_name] * len(challenge_types)

        # Create prompts for each challenge
        prompts = [
            self._create_generation_prompt(ct, d)
            for ct, d in zip(challenge_types, difficulties)
        ]

        # Generate all challenges in batch
        responses = self.structured_llm.batch(prompts)

        # Create Challenge objects from responses
        challenges = []
        for response, ct, d, cid in zip(
            responses, challenge_types, difficulties, creator_ids
        ):
            challenge = Challenge(
                title=response.title,
                description=response.description,
                challenge_type=ct,
                difficulty=d,
                creator_id=cid,
                evaluation_criteria=response.evaluation_criteria,
                expected_concepts=response.expected_concepts,
                answer=response.answer,
                tags=[ct.value, f"difficulty_{d.value}"],
            )
            challenges.append(challenge)

        return challenges

    def _create_generation_prompt(
        self, challenge_type: ChallengeType, difficulty: ChallengeDifficulty
    ) -> str:
        """Create a detailed prompt for challenge generation."""

        # Base context about the arena
        base_context = """You are a challenge creator for an Intelligence Arena where AI agents compete in intellectual battles. Your job is to create engaging, fair, and challenging problems that test AI capabilities.

The challenge should be:
- Intellectually stimulating and thought-provoking
- Fair but challenging for the specified difficulty level
- Clear and unambiguous in its requirements
- Suitable for evaluation by peer AI judges
- Creative and engaging"""

        # Type-specific guidance
        type_guidance = {
            ChallengeType.LOGICAL_REASONING: """
Focus on: Deductive reasoning, logical consistency, systematic analysis
Examples: Logic puzzles, constraint satisfaction, formal reasoning problems
Requirements: Clear premises, unambiguous logical relationships, step-by-step reasoning needed
Answer: Provide a correct answer or solution for the challenge""",
            ChallengeType.CREATIVE_PROBLEM_SOLVING: """
Focus on: Innovation, out-of-the-box thinking, novel approaches
Examples: Unusual scenarios, constraint-breaking solutions, inventive applications
Requirements: Multiple valid solutions possible, creativity over correctness, practical constraints""",
            ChallengeType.MATHEMATICAL: """
Focus on: Quantitative analysis, optimization, mathematical modeling
Examples: Optimization problems, statistical analysis, computational mathematics
Requirements: Numerical precision, clear mathematical relationships, calculable answers
Answer: Provide the correct numerical answer or mathematical solution""",
            ChallengeType.KNOWLEDGE_INTEGRATION: """
Focus on: Connecting diverse domains, interdisciplinary thinking, synthesis
Examples: Cross-domain problems, knowledge transfer challenges, integrative scenarios
Requirements: Multiple knowledge domains needed, connections between fields, holistic understanding
Answer: For factual questions, provide the correct answer with key details""",
            ChallengeType.ABSTRACT_THINKING: """
Focus on: Conceptual reasoning, pattern recognition, abstraction
Examples: Pattern completion, analogical reasoning, conceptual mapping
Requirements: Looking beyond concrete details, finding underlying patterns, abstract representation
Answer: If there's a definitive pattern or solution, provide it""",
            ChallengeType.DEBATE: """
Focus on: Argumentation quality, evidence-based reasoning, balanced perspectives, intellectual rigor
Examples: Ethical dilemmas, policy debates, philosophical questions, contemporary issues, hypothetical scenarios
Requirements: 
- Controversial topic with legitimate arguments on multiple sides
- No single "correct" answer - quality of argumentation matters most
- Clear framing that allows for substantive debate
- Avoids topics that are purely factual or have objective answers
- Encourages evidence-based reasoning and logical consistency
Answer: Do NOT provide a predetermined correct answer. Instead, provide key considerations, important facts, and evaluation criteria that judges should use to assess the quality of arguments presented by each side""",
        }

        # Difficulty-specific guidance
        difficulty_guidance = {
            ChallengeDifficulty.BEGINNER: "Simple and straightforward. Should be solvable by most AI agents with basic reasoning.",
            ChallengeDifficulty.INTERMEDIATE: "Moderate complexity. Requires solid reasoning skills and some creative thinking.",
            ChallengeDifficulty.ADVANCED: "Complex and challenging. Requires advanced reasoning and sophisticated analysis.",
            ChallengeDifficulty.EXPERT: "Very difficult. Should challenge even highly capable AI agents.",
            ChallengeDifficulty.MASTER: "Extremely challenging. Reserved for the most elite competitions.",
        }

        prompt = f"""{base_context}

**Challenge Type: {challenge_type.value.replace('_', ' ').title()}**
{type_guidance.get(challenge_type, "")}

**Difficulty Level: {difficulty.name} (Level {difficulty.value}/5)**
{difficulty_guidance.get(difficulty, "")}

Create a challenge that fits these specifications. The challenge should be engaging, intellectually stimulating, and appropriate for competitive AI evaluation.

Provide:
1. A compelling title
2. A clear, detailed description of the challenge
3. Specific evaluation criteria for judging responses
4. Key concepts that a good response should demonstrate

Make it interesting and creative while staying true to the challenge type and difficulty level."""

        return prompt


def create_challenge_pool(
    generator: ChallengeGenerator = None,
    pool_size: int = 20,
    agents=None,
    agent_llms=None,
) -> List[Challenge]:
    """Create a diverse pool of challenges for the arena."""

    print(f"🎯 Generating {pool_size} dynamic challenges using LLM...")

    # Create generator if not provided
    if generator is None:
        generator = ChallengeGenerator(agents=agents, agent_llms=agent_llms)

    # Ensure good distribution across types and difficulties
    challenge_types = list(ChallengeType)
    difficulties = list(ChallengeDifficulty)

    challenges = []

    # Generate challenges with balanced distribution
    for i in range(pool_size):
        challenge_type = challenge_types[i % len(challenge_types)]
        difficulty = difficulties[i % len(difficulties)]

        try:
            challenge = generator.generate_challenge(challenge_type, difficulty)
            challenges.append(challenge)
            print(
                f"   ✅ Generated: {challenge.title} ({challenge_type.value}, {difficulty.name})"
            )
        except Exception as e:
            print(f"   ❌ Failed to generate challenge: {e}")

    print(f"   🎯 Successfully generated {len(challenges)} challenges")
    return challenges


# Example usage and testing
def test_challenge_generation():
    """Test the challenge generation system."""
    generator = ChallengeGenerator()

    # Test single challenge generation
    print("🧪 Testing Challenge Generation...")

    try:
        challenge = generator.generate_challenge(
            ChallengeType.LOGICAL_REASONING, ChallengeDifficulty.INTERMEDIATE
        )
        print(f"✅ Generated Challenge: {challenge.title}")
        print(f"   Type: {challenge.challenge_type.value}")
        print(f"   Difficulty: {challenge.difficulty.name}")
        print(f"   Description: {challenge.description[:200]}...")

        return challenge
    except Exception as e:
        print(f"❌ Challenge generation failed: {e}")
        return None


if __name__ == "__main__":
    test_challenge_generation()
