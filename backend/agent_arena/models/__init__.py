"""Data models for the Intelligence Arena System."""

from .agent import Agent, Division, AgentProfile, AgentStats
from .challenge import Challenge, ChallengeType, ChallengeDifficulty
from .match import Match, MatchResult, MatchStatus
from .evaluation import Evaluation, JudgeScore, EvaluationCriteria

__all__ = [
    "Agent",
    "Division",
    "AgentProfile",
    "AgentStats",
    "Challenge",
    "ChallengeType",
    "ChallengeDifficulty",
    "Match",
    "MatchResult",
    "MatchStatus",
    "Evaluation",
    "JudgeScore",
    "EvaluationCriteria",
]
