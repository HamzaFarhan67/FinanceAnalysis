"""Week 2 reference code: conversation persistence with SQLAlchemy 2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, create_engine, select, Text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from .models import ChatMessage, MessageRole


class Base(DeclarativeBase):
    """Base class for SQLAlchemy mappings in the course examples."""


class ConversationRecord(Base):
    """Conversation header row."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # ADD USER_ID COLUMN:
    user_id: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    messages: Mapped[list[MessageRecord]] = relationship(
        back_populates="conversation", # links this to the conversation attribute defined on MessageRecord
        cascade="all, delete-orphan", 
        order_by="MessageRecord.created_at", # ensures messages always load in chronological order
    )


class MessageRecord(Base):
    """Individual message row."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    conversation: Mapped[ConversationRecord] = relationship(back_populates="messages")


def build_engine(database_url: str) -> Engine:
    """Create a synchronous SQLAlchemy engine for the lesson code."""

    return create_engine(database_url, echo=False, future=True)


class ConversationRepository:
    """Small repository used in the persistence lessons."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # new method to create a conversation with optional user_id
    def create_conversation(self, title: str = "New conversation", user_id: str | None = None) -> ConversationRecord:
        conversation = ConversationRecord(title=title, user_id=user_id)
        self.session.add(conversation)
        self.session.flush()
        return conversation
    

    def append_message(self, conversation_id: UUID, message: ChatMessage) -> MessageRecord:
        record = MessageRecord(
            conversation_id=conversation_id,
            role=message.role.value,
            content=message.content,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def load_transcript(self, conversation_id: UUID) -> list[ChatMessage]:
        statement = (
            select(MessageRecord)
            .where(MessageRecord.conversation_id == conversation_id)
            .order_by(MessageRecord.created_at.asc())
        )
        rows = self.session.scalars(statement).all()
        return [ChatMessage(role=MessageRole(row.role), content=row.content) for row in rows]
