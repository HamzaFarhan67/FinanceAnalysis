"""Shared models used by the course reference code."""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — required for server use
import matplotlib.pyplot as plt
import io, base64

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Supported chat roles for the course chat application."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single chat message in a conversation transcript."""

    role: MessageRole
    content: str = Field(min_length=1)


class ConversationSummary(BaseModel):
    """Compressed memory that can be persisted alongside a transcript."""

    conversation_id: UUID = Field(default_factory=uuid4)
    summary: str = Field(min_length=1)
    open_questions: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)


class PersonProfile(BaseModel):
    """Structured output used in Weeks 3 and 4."""

    name: str = Field(min_length=1)
    favorite_color: str = Field(min_length=1)
    birthday_iso: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class AuthenticatedUser(BaseModel):
    """JWT-derived user context used by secured endpoints and tools."""

    user_id: UUID
    email: str
    tenant_id: str = Field(min_length=1)


class DocumentChunk(BaseModel):
    """A single chunk that would later be embedded for retrieval."""

    document_id: UUID = Field(default_factory=uuid4)
    chunk_id: UUID = Field(default_factory=uuid4)
    source_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

class ChartSeries(BaseModel):
    label: str
    values: list[float]

class ChartSpec(BaseModel):
    title: str
    chart_type: str  # "bar", "line", "pie"
    labels: list[str]
    series: list[ChartSeries]

class DataFrameProfile(BaseModel):
    row_count: int
    column_count: int
    numeric_columns: list[str]
    categorical_columns: list[str]

class VisualizationResult(BaseModel):
    sql_query: str
    chart_spec: ChartSpec
    python_code: str        # ← add
    dataframe_json: str     
    chart_base64: str        # PNG encoded as base64 string — send to frontend
    row_count: int
    profile: DataFrameProfile