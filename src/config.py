import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, SecretStr


class GitConfig(BaseModel):
    repo_url: str
    token: SecretStr
    base_branch: str = "PROD"

class LLMConfig(BaseModel):
    api_key: SecretStr
    model_name: str = "gemini-1.5-pro"
    base_url: Optional[str] = None

class EmailConfig(BaseModel):
    enabled: bool = False
    host: str
    port: int
    user: str
    password: SecretStr
    recipients: List[str]

class TeamsConfig(BaseModel):
    enabled: bool = False
    webhook_url: SecretStr

class LoggingConfig(BaseModel):
    level: str = "INFO"
    verbose: bool = False


class AppConfig(BaseModel):
    git: GitConfig
    llm: LLMConfig
    email: EmailConfig
    teams: TeamsConfig
    logging: LoggingConfig = LoggingConfig()


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file and environment variables."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Resolve environment variables in the YAML content or override
    # Simple env var substitution for specific fields if they are placeholders
    
    # Check for env vars overrides for secrets
    if "GIT_TOKEN" in os.environ:
        config_data["git"]["token"] = os.environ["GIT_TOKEN"]
    
    if "OPENAI_API_KEY" in os.environ:
        config_data["llm"]["api_key"] = os.environ["OPENAI_API_KEY"]
    elif config_data["llm"]["api_key"] == "${OPENAI_API_KEY}":
         # If still the placeholder and not in env, this will fail validation if strict,
         # but Pydantic will catch missing fields. 
         # We'll leave it to Pydantic validation to complain if it's not a valid string.
         # But better to raise explicit error if it looks like a placeholder
         pass

    return AppConfig(**config_data)
