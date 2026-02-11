"""Configuration settings for the Cloud Migration Simulation."""

import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional


@dataclass
class CompletionConditions:
    """Completion conditions for the simulation."""
    MIN_PERSONAS: int = 2
    MIN_CONSTRAINTS: int = 3
    REQUIRE_STRATEGY: bool = True


@dataclass
class LLMConfig:
    """LLM API configuration."""
    provider: str = "openai"  # "openai" or "anthropic"
    model: str = "gpt-4o-mini"  # Default model
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")


@dataclass
class SimulationConfig:
    """Simulation configuration."""
    max_rounds: int = 8
    completion_conditions: CompletionConditions = None
    llm_config: LLMConfig = None

    def __post_init__(self):
        """Initialize defaults if not provided."""
        if self.completion_conditions is None:
            self.completion_conditions = CompletionConditions()
        if self.llm_config is None:
            self.llm_config = LLMConfig()


# Global configuration instance
config = SimulationConfig()
