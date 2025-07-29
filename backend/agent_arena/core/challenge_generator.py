"""Dynamic challenge generation using LLMs for the Intelligence Arena System."""

import random
from typing import List, Optional
from agent_arena.models.challenge import Challenge, ChallengeType, ChallengeDifficulty
from agent_arena.core.llm_interface import create_system_llm, create_structured_llm, ChallengeResponse


class ChallengeGenerator:
    """Generates challenges dynamically using LLMs."""
    
    def __init__(self):
        """Initialize the challenge generator with an LLM."""
        self.llm = create_system_llm()
        self.structured_llm = create_structured_llm(self.llm, ChallengeResponse)
    
    def generate_challenge(
        self, 
        challenge_type: ChallengeType, 
        difficulty: ChallengeDifficulty,
        creator_id: Optional[str] = None
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
            creator_id=creator_id,
            evaluation_criteria=response.evaluation_criteria,
            expected_concepts=response.expected_concepts,
            tags=[challenge_type.value, f"difficulty_{difficulty.value}"]
        )
        
        return challenge
    
    def generate_multiple_challenges(
        self, 
        count: int = 5,
        challenge_types: Optional[List[ChallengeType]] = None,
        difficulties: Optional[List[ChallengeDifficulty]] = None
    ) -> List[Challenge]:
        """Generate multiple challenges with varied types and difficulties."""
        
        if challenge_types is None:
            challenge_types = list(ChallengeType)
        
        if difficulties is None:
            difficulties = list(ChallengeDifficulty)
        
        challenges = []
        
        for _ in range(count):
            challenge_type = random.choice(challenge_types)
            difficulty = random.choice(difficulties)
            
            try:
                challenge = self.generate_challenge(challenge_type, difficulty)
                challenges.append(challenge)
            except Exception as e:
                print(f"Warning: Failed to generate challenge: {e}")
                continue
        
        return challenges
    
    def _create_generation_prompt(self, challenge_type: ChallengeType, difficulty: ChallengeDifficulty) -> str:
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
Requirements: Clear premises, unambiguous logical relationships, step-by-step reasoning needed""",
            
            ChallengeType.CREATIVE_PROBLEM_SOLVING: """
Focus on: Innovation, out-of-the-box thinking, novel approaches
Examples: Unusual scenarios, constraint-breaking solutions, inventive applications
Requirements: Multiple valid solutions possible, creativity over correctness, practical constraints""",
            
            ChallengeType.MATHEMATICAL: """
Focus on: Quantitative analysis, optimization, mathematical modeling
Examples: Optimization problems, statistical analysis, computational mathematics
Requirements: Numerical precision, clear mathematical relationships, calculable answers""",
            
            ChallengeType.ABSTRACT_THINKING: """
Focus on: Pattern recognition, conceptual relationships, symbolic reasoning
Examples: Pattern completion, analogical reasoning, conceptual mapping
Requirements: Abstract concepts, transferable patterns, symbolic manipulation""",
            
            ChallengeType.KNOWLEDGE_INTEGRATION: """
Focus on: Cross-domain synthesis, information integration, comprehensive analysis
Examples: Multi-disciplinary problems, synthesis tasks, comprehensive evaluations
Requirements: Multiple knowledge domains, integration skills, holistic thinking""",
            
            ChallengeType.META_COGNITION: """
Focus on: Reasoning about reasoning, strategy evaluation, self-reflection
Examples: Strategy analysis, cognitive process evaluation, reasoning methodology
Requirements: Meta-level thinking, process awareness, strategic reasoning""",
            
            ChallengeType.DEBATE: """
Focus on: Argumentation, rebuttal, and synthesis of complex topics. The goal is not to find a "correct" answer, but to see which agent can build a more coherent, persuasive, and well-supported case.
Examples: "Is consciousness an emergent property or fundamental to the universe?", "Should AI development be open-source or regulated?", "Does free will exist in a deterministic universe?"
Requirements: A clear, controversial, and debatable resolution. The topic should have sufficient depth for a multi-turn debate. The description should set the stage for the debate, but not take a side."""
        }
        
        # Difficulty-specific guidance
        difficulty_guidance = {
            ChallengeDifficulty.BEGINNER: "Simple and straightforward. Should be solvable by most AI agents with basic reasoning.",
            ChallengeDifficulty.INTERMEDIATE: "Moderate complexity. Requires solid reasoning skills and some creative thinking.",
            ChallengeDifficulty.ADVANCED: "Complex and challenging. Requires advanced reasoning and sophisticated analysis.",
            ChallengeDifficulty.EXPERT: "Very difficult. Should challenge even highly capable AI agents.",
            ChallengeDifficulty.MASTER: "Extremely challenging. Reserved for the most elite competitions."
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


def create_challenge_pool(generator: ChallengeGenerator, pool_size: int = 20) -> List[Challenge]:
    """Create a diverse pool of challenges for the arena."""
    
    print(f"🎯 Generating {pool_size} dynamic challenges using LLM...")
    
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
            print(f"   ✅ Generated: {challenge.title} ({challenge_type.value}, {difficulty.name})")
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
            ChallengeType.LOGICAL_REASONING, 
            ChallengeDifficulty.INTERMEDIATE
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