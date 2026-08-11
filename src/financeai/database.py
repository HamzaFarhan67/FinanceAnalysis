from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import DECIMAL, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from .week02_persistence import build_engine
from .settings import AppSettings
from dataclasses import dataclass

config = AppSettings()
engine = build_engine(config.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        try:
            db.close()
        except Exception:
            db.invalidate()

@dataclass
class AgentState:
    db: Session
    current_user_id: int

class Base(DeclarativeBase):
    pass

    access_token: Optional[str] = None  # <-- add this
class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # <--- Added
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)        # <--- Added
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now)
    currency: Mapped[str] = mapped_column(String(3), server_default="USD")

    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (CheckConstraint("type IN ('income', 'expense')", name="ck_categories_type"),)

    category_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="categories")
    
    # FIXED: Changed back_populates from "categories" to "category"
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_type",
        ),
    )

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.category_id", ondelete="SET NULL")
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column()
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    budget_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id", ondelete="CASCADE")
    )
    monthly_limit: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    alert_threshold: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), server_default="0.80")

    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship(back_populates="budgets")

