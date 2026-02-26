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

    def validate_api(self) -> None:
        """
        Verify that the API key is valid and the provider is reachable.
        Performs a minimal API call. Raises on failure.
        """
        if not self.api_key:
            raise ValueError("API key is not set")
        try:
            if self.provider == "openai":
                try:
                    import openai
                except ImportError:
                    raise ValueError("openai package not installed. Run: pip install openai") from None
                client = openai.OpenAI(api_key=self.api_key)
                client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5,
                )
            elif self.provider == "anthropic":
                try:
                    import anthropic
                except ImportError:
                    raise ValueError("anthropic package not installed. Run: pip install anthropic") from None
                client = anthropic.Anthropic(api_key=self.api_key)
                client.messages.create(
                    model=self.model,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Say OK"}],
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except ValueError:
            raise
        except Exception as e:
            err = str(e).lower()
            if "invalid" in err or "401" in str(e) or "authentication" in err or "api_key" in err:
                raise ValueError(f"Invalid API key for {self.provider}. Check your key.") from e
            if "quota" in err or "429" in err or "rate" in err:
                raise ValueError(f"API quota exceeded or rate limited ({self.provider}).") from e
            if "model" in err and ("not found" in err or "404" in str(e)):
                raise ValueError(f"Model '{self.model}' not found or not available for {self.provider}.") from e
            raise ValueError(f"API check failed ({self.provider}): {e}") from e


@dataclass
class SimulationConfig:
    """Simulation configuration."""
    max_rounds: int = os.environ.get("SIMULATION_MAX_ROUNDS", 4)
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
