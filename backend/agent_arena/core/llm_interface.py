"""Unified LLM interface using OpenRouter for the Intelligence Arena System."""
import dotenv
dotenv.load_dotenv(override=True)
import os
import random
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Available OpenRouter models
AGENT_MODELS = [
    # Free/Cheap Models
    "x-ai/grok-3-mini-beta",
    "google/gemini-2.0-flash-001",
    "google/gemini-2.0-flash-exp:free",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o-mini",
    "qwen/qwen3-235b-a22b-2507:free",
    "deepseek/deepseek-r1-distill-llama-70b",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-24b-instruct-2501",
    "mistralai/mistral-small-3.2-24b-instruct",
    "mistralai/mistral-nemo",
    
    # Premium Models (Commented out)
    # "anthropic/claude-sonnet-4",
    # "google/gemini-2.5-flash",
    # "google/gemini-2.0-flash-001",
    # "anthropic/claude-3.7-sonnet",
    # "anthropic/claude-3.5-sonnet",
    # "meta-llama/llama-3.1-70b-instruct",
    # "openai/gpt-4",
    # "google/gemma-3-27b-it",
    # "qwen/qwen-2.5-72b-instruct",
    # "openai/gpt-4.1",
    # "openai/gpt-4o"
]

# Models for system tasks (challenges, evaluation)
SYSTEM_MODELS = [
    # Best models for structured output
    "google/gemini-2.0-flash-001",  # Good structured output support
    "openai/gpt-4o-mini",           # Mini version but still good at structured tasks
    "openai/gpt-4.1-mini"           # Another good option for structured output
]

def create_agent_llm(model_name: str = None, **kwargs):
    """
    Create a LangChain LLM instance using OpenRouter.
    
    Args:
        model_name: OpenRouter model identifier
        **kwargs: Additional parameters for the LLM
    
    Returns:
        LangChain LLM instance with invoke() method
    """
    if not model_name:
        print("No model name provided, using random model")
        model_name = random.choice(AGENT_MODELS)
    
    return ChatOpenAI(
        openai_api_key=getenv("OPENROUTER_API_KEY"),
        openai_api_base=getenv("OPENROUTER_BASE_URL"),
        model_name=model_name
    )

def create_system_llm(**kwargs):
    """Create an LLM instance for system tasks (challenges, evaluation)."""
    model_name = random.choice(SYSTEM_MODELS)
    return create_agent_llm(model_name, **kwargs)

def create_structured_llm(llm, output_schema: Type[BaseModel]):
    """
    Create a structured output version of a LangChain LLM.
    
    Args:
        llm: LangChain LLM instance
        output_schema: Pydantic model for structured output
    
    Returns:
        LLM with structured output that returns Pydantic model instances
    """
    return llm.with_structured_output(output_schema)

def create_diverse_agents(count: int = None) -> List:
    """
    Create multiple agent LLMs with different models.
    
    Args:
        count: Optional number of agents (defaults to using all models)
    
    Returns:
        List of configured LLM instances
    """
    agents = []
    models_to_use = AGENT_MODELS if count is None else random.sample(AGENT_MODELS, min(count, len(AGENT_MODELS)))
    
    for i, model in enumerate(models_to_use):
        # Vary temperature for personality differences
        temperature = random.uniform(0.3, 0.9)
        
        try:
            # Create agent LLM
            agent_llm = create_agent_llm(
                model_name=model,
                temperature=temperature,
                max_tokens=1500
            )
            
            # Get friendly name for the model
            provider = model.split('/')[0].title()
            model_short = model.split('/')[-1].split('-')[0].title()
            
            agents.append({
                'llm': agent_llm,
                'temperature': temperature,
                'model': model,
                'agent_id': f"agent_{provider}_{model_short}_{i+1}",
                'display_name': f"{provider} {model_short}"
            })
            
        except Exception as e:
            print(f"Warning: Could not create agent with {model}: {e}")
    
    return agents

# Example Pydantic schemas for structured outputs

class ChallengeResponse(BaseModel):
    """Schema for challenge creation responses."""
    title: str = Field(description="Challenge title")
    description: str = Field(description="Detailed challenge description")
    difficulty: int = Field(description="Difficulty level (1-5)", ge=1, le=5)
    challenge_type: str = Field(description="Type of challenge")
    evaluation_criteria: List[str] = Field(description="List of evaluation criteria")
    expected_concepts: List[str] = Field(description="Key concepts expected in responses")
    answer: Optional[str] = Field(default=None, description="Correct answer or solution (for challenges with definitive answers)")


class EvaluationScores(BaseModel):
    """Schema for evaluation scores per criteria."""
    correctness: Optional[float] = Field(default=None, description="Score for correctness (0-10)", ge=0, le=10)
    completeness: Optional[float] = Field(default=None, description="Score for completeness (0-10)", ge=0, le=10)
    logical_consistency: Optional[float] = Field(default=None, description="Score for logical consistency (0-10)", ge=0, le=10)
    creativity: Optional[float] = Field(default=None, description="Score for creativity (0-10)", ge=0, le=10)
    clarity: Optional[float] = Field(default=None, description="Score for clarity (0-10)", ge=0, le=10)
    depth: Optional[float] = Field(default=None, description="Score for depth (0-10)", ge=0, le=10)
    originality: Optional[float] = Field(default=None, description="Score for originality (0-10)", ge=0, le=10)
    accuracy: Optional[float] = Field(default=None, description="Score for accuracy (0-10)", ge=0, le=10)
    efficiency: Optional[float] = Field(default=None, description="Score for efficiency (0-10)", ge=0, le=10)
    relevance: Optional[float] = Field(default=None, description="Score for relevance (0-10)", ge=0, le=10)


class EvaluationResponse(BaseModel):
    """Schema for judge evaluation responses."""
    agent1_scores: EvaluationScores = Field(description="Detailed scores for agent 1")
    agent2_scores: EvaluationScores = Field(description="Detailed scores for agent 2")
    overall_reasoning: str = Field(description="Overall reasoning for the evaluation")
    recommended_winner: Optional[str] = Field(description="Recommended winner ('agent1', 'agent2', or 'draw')")
    confidence: float = Field(description="Confidence in evaluation (0-1)", ge=0, le=1)


class CompetitorResponse(BaseModel):
    """Schema for competitor responses to challenges."""
    answer: str = Field(description="The main answer to the challenge")
    reasoning: str = Field(description="Step-by-step reasoning process")
    confidence: float = Field(description="Confidence in the answer (0-1)", ge=0, le=1)
    alternative_approaches: Optional[List[str]] = Field(default=None, description="Other possible approaches considered")

# Helper function to get response content from LangChain response
def get_content(response) -> str:
    """Extract content from LangChain response object."""
    if hasattr(response, 'content'):
        return response.content
    return str(response)


# Example usage functions for testing
def test_basic_llm():
    """Test basic LLM functionality."""
    try:
        # Try Groq first, then Gemini as fallback
        for provider in ["groq", "gemini"]:
            try:
                llm = create_agent_llm(provider)
                response = llm.invoke("Hello! Introduce yourself as an AI competing in an intelligence arena.")
                print(f"✅ {provider.upper()} LLM working: {get_content(response)[:100]}...")
                return llm
            except Exception as e:
                print(f"❌ {provider.upper()} failed: {e}")
        
        print("❌ No LLM provider available")
        return None
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return None


def test_structured_output():
    """Test structured output functionality."""
    try:
        llm = create_agent_llm("groq")  # or "gemini"
        structured_llm = create_structured_llm(llm, ChallengeResponse)
        
        prompt = """Create a logical reasoning challenge suitable for an AI competition. 
        Make it challenging but fair, focusing on deductive reasoning."""
        
        response = structured_llm.invoke(prompt)
        print(f"✅ Structured output working: {response.title}")
        return response
        
    except Exception as e:
        print(f"❌ Structured output test failed: {e}")
        return None


if __name__ == "__main__":
    print("🧪 Testing LangChain LLM Interface...")
    
    # Test basic LLM
    llm = test_basic_llm()
    
    # Test structured output
    if llm:
        structured_response = test_structured_output()
        if structured_response:
            print(f"📝 Generated challenge: {structured_response.title}")
            print(f"🎯 Difficulty: {structured_response.difficulty}/5") 