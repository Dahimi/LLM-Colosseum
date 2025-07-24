"""Configuration management for the Intelligence Arena System."""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class DivisionConfig(BaseModel):
    """Configuration for division management."""
    promotion_win_streak: int = Field(default=3, description="Win streak required for promotion")
    promotion_min_matches: int = Field(default=5, description="Minimum matches before promotion eligibility")
    promotion_win_rate: float = Field(default=0.6, description="Win rate required for promotion")
    
    demotion_loss_streak: int = Field(default=5, description="Loss streak triggering demotion")
    demotion_min_matches: int = Field(default=10, description="Minimum matches before demotion eligibility")
    demotion_max_win_rate: float = Field(default=0.3, description="Win rate below which demotion occurs")
    
    king_challenge_wins_required: int = Field(default=3, description="Consecutive wins needed to become King")
    king_defense_losses_allowed: int = Field(default=1, description="Losses allowed before King loses title")


class MatchConfig(BaseModel):
    """Configuration for match management."""
    judges_per_match: int = Field(default=5, description="Number of judges per match")
    min_judge_division_gap: int = Field(default=1, description="Minimum division gap between judge and competitor")
    max_response_time_minutes: int = Field(default=30, description="Maximum time for agent response")
    
    # ELO system parameters
    elo_k_factor: float = Field(default=32.0, description="ELO K-factor for rating updates")
    elo_starting_rating: float = Field(default=1200.0, description="Starting ELO rating for new agents")
    
    # Scoring
    min_score_difference_for_win: float = Field(default=0.5, description="Minimum score difference to declare winner")
    judge_reliability_weight: bool = Field(default=True, description="Whether to weight judges by reliability")


class ChallengeConfig(BaseModel):
    """Configuration for challenge generation and management."""
    min_challenges_per_type: int = Field(default=5, description="Minimum challenges maintained per type")
    max_challenge_reuse: int = Field(default=10, description="Maximum times a challenge can be reused")
    
    # Challenge quality thresholds
    min_discrimination_power: float = Field(default=0.3, description="Minimum discrimination power to keep challenge")
    max_average_score: float = Field(default=9.0, description="Maximum average score before challenge is retired")
    
    # Generation parameters
    challenges_generated_per_batch: int = Field(default=3, description="Challenges generated in each batch")
    challenge_generation_interval_hours: float = Field(default=6.0, description="Hours between challenge generation")


class ArenaConfig(BaseModel):
    """Main configuration for the Intelligence Arena System."""
    
    # System settings
    arena_name: str = Field(default="Intelligence Arena", description="Name of the arena")
    max_concurrent_matches: int = Field(default=10, description="Maximum concurrent matches")
    match_scheduling_interval_minutes: float = Field(default=5.0, description="Minutes between match scheduling")
    
    # Agent management
    max_agents: int = Field(default=100, description="Maximum number of agents in the arena")
    agent_inactivity_hours: float = Field(default=24.0, description="Hours before agent marked inactive")
    agent_removal_inactive_days: int = Field(default=7, description="Days before inactive agents are removed")
    
    # Division settings
    division: DivisionConfig = Field(default_factory=DivisionConfig)
    
    # Match settings
    match: MatchConfig = Field(default_factory=MatchConfig)
    
    # Challenge settings
    challenge: ChallengeConfig = Field(default_factory=ChallengeConfig)
    
    # Logging and monitoring
    log_level: str = Field(default="INFO", description="Logging level")
    enable_detailed_logging: bool = Field(default=True, description="Enable detailed logging")
    stats_calculation_interval_hours: float = Field(default=1.0, description="Hours between stats calculations")
    
    # Database and persistence
    data_persistence_enabled: bool = Field(default=True, description="Enable data persistence")
    backup_interval_hours: float = Field(default=12.0, description="Hours between data backups")
    
    # Safety and limits
    max_evaluation_time_minutes: float = Field(default=10.0, description="Maximum time for judge evaluation")
    emergency_stop_enabled: bool = Field(default=True, description="Enable emergency stop functionality")
    rate_limit_requests_per_minute: int = Field(default=100, description="Rate limit for LLM requests")


def get_default_config() -> ArenaConfig:
    """Get the default arena configuration."""
    return ArenaConfig()


def get_development_config() -> ArenaConfig:
    """Get a configuration optimized for development and testing."""
    config = ArenaConfig()
    
    # Faster cycles for development
    config.match_scheduling_interval_minutes = 1.0
    config.stats_calculation_interval_hours = 0.1
    config.challenge.challenge_generation_interval_hours = 1.0
    
    # Smaller limits for testing
    config.max_agents = 20
    config.max_concurrent_matches = 5
    config.challenge.min_challenges_per_type = 2
    config.match.judges_per_match = 3
    
    # More lenient promotion/demotion
    config.division.promotion_min_matches = 3
    config.division.demotion_min_matches = 5
    
    # Faster timeouts
    config.match.max_response_time_minutes = 5
    config.max_evaluation_time_minutes = 2
    
    # Enhanced logging for development
    config.log_level = "DEBUG"
    config.enable_detailed_logging = True
    
    return config


def get_production_config() -> ArenaConfig:
    """Get a configuration optimized for production deployment."""
    config = ArenaConfig()
    
    # Conservative settings for production
    config.max_agents = 500
    config.max_concurrent_matches = 50
    config.rate_limit_requests_per_minute = 200
    
    # Robust promotion/demotion criteria
    config.division.promotion_win_streak = 5
    config.division.promotion_min_matches = 10
    config.division.demotion_loss_streak = 7
    config.division.demotion_min_matches = 15
    
    # Quality control
    config.challenge.min_discrimination_power = 0.4
    config.challenge.max_challenge_reuse = 20
    config.match.judges_per_match = 7
    
    # Production logging
    config.log_level = "INFO"
    config.enable_detailed_logging = False
    
    return config 