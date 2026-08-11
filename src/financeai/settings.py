"""Shared application settings for the backend examples."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Environment-driven configuration shared across weekly examples."""

    app_name: str = "Modern Agentic AI Course"
    environment: str = Field(default="development", pattern="^(development|test|production)$")
    database_url: str = "postgresql+psycopg://postgres:hamza123@localhost:5432/agent_course"
    openai_model: str = "llama-3.3-70b-versatile"
    jwt_secret: str = "replace-me-in-production"
    logfire_service_name: str = "agent-ai-course"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COURSE_",
        extra="ignore",
    )
