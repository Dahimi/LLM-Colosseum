"""Logging utilities for the Intelligence Arena System."""

import logging
import sys
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    detailed: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for the arena system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        detailed: Whether to include detailed formatting
        log_file: Optional file to write logs to
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("intelligence_arena")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if detailed:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "intelligence_arena") -> logging.Logger:
    """Get a logger instance for the arena system."""
    return logging.getLogger(name)


class ArenaLogger:
    """Enhanced logger for arena-specific events."""
    
    def __init__(self, name: str = "intelligence_arena"):
        self.logger = get_logger(name)
    
    def match_started(self, match_id: str, agent1_id: str, agent2_id: str, challenge_id: str):
        """Log match start."""
        self.logger.info(f"Match {match_id} started: {agent1_id} vs {agent2_id} on challenge {challenge_id}")
    
    def match_completed(self, match_id: str, winner_id: Optional[str], duration: float):
        """Log match completion."""
        winner_info = f"Winner: {winner_id}" if winner_id else "Draw"
        self.logger.info(f"Match {match_id} completed in {duration:.2f}s - {winner_info}")
    
    def agent_promoted(self, agent_id: str, from_division: str, to_division: str):
        """Log agent promotion."""
        self.logger.info(f"Agent {agent_id} promoted from {from_division} to {to_division}")
    
    def agent_demoted(self, agent_id: str, from_division: str, to_division: str):
        """Log agent demotion."""
        self.logger.warning(f"Agent {agent_id} demoted from {from_division} to {to_division}")
    
    def new_king(self, agent_id: str, previous_king: Optional[str]):
        """Log new king coronation."""
        if previous_king:
            self.logger.info(f"New King crowned! {agent_id} defeated {previous_king}")
        else:
            self.logger.info(f"First King crowned! {agent_id} ascends to the throne")
    
    def challenge_created(self, challenge_id: str, creator_id: str, challenge_type: str):
        """Log challenge creation."""
        self.logger.info(f"New challenge {challenge_id} created by {creator_id} (type: {challenge_type})")
    
    def challenge_retired(self, challenge_id: str, reason: str):
        """Log challenge retirement."""
        self.logger.info(f"Challenge {challenge_id} retired: {reason}")
    
    def agent_joined(self, agent_id: str, agent_name: str):
        """Log new agent joining."""
        self.logger.info(f"New agent joined: {agent_name} (ID: {agent_id})")
    
    def agent_left(self, agent_id: str, reason: str):
        """Log agent leaving."""
        self.logger.info(f"Agent {agent_id} left the arena: {reason}")
    
    def system_error(self, component: str, error: str, details: Optional[str] = None):
        """Log system errors."""
        msg = f"System error in {component}: {error}"
        if details:
            msg += f" - Details: {details}"
        self.logger.error(msg)
    
    def performance_warning(self, component: str, metric: str, value: float, threshold: float):
        """Log performance warnings."""
        self.logger.warning(f"Performance warning in {component}: {metric} = {value:.2f} (threshold: {threshold:.2f})")
    
    def stats_summary(self, total_agents: int, active_matches: int, challenges_available: int):
        """Log system statistics summary."""
        self.logger.info(f"Arena stats - Agents: {total_agents}, Active matches: {active_matches}, Challenges: {challenges_available}")


# Global arena logger instance
arena_logger = ArenaLogger() 