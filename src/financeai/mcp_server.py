from decimal import Decimal
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
import os
from google import genai
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, Text
from .database import Base, engine, SessionLocal
from .settings import AppSettings
# import your Budget / Category / Transaction models from wherever they're defined
from .database import Budget, Category, Transaction, Base

mcp = FastMCP("budget-tools", host="0.0.0.0", port=8001)

# Initialize OpenCode client for embeddings
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values

# SQLAlchemy model for your vector storage table
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(3072), nullable=False)

@mcp.tool()
def get_budget_status(user_id: int, category_id: int) -> dict:
    """Return the monthly limit, amount spent so far, and remaining budget for a category."""
    db = SessionLocal()
    try:
        budget = db.execute(
            select(Budget).where(
                Budget.user_id == user_id, Budget.category_id == category_id
            )
        ).scalar_one_or_none()
        if not budget:
            return {"status": "error", "message": "No budget set for this category."}

        spent = db.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.transaction_type == "expense",
            )
        ).scalars().all()
        total_spent = sum((t.amount for t in spent), Decimal("0"))

        return {
            "status": "success",
            "monthly_limit": float(budget.monthly_limit),
            "spent": float(total_spent),
            "remaining": float(budget.monthly_limit - total_spent),
            "alert_threshold": float(budget.alert_threshold),
        }
    finally:
        db.close()


@mcp.tool()
def list_budgets(user_id: int) -> dict:
    """List all budgets set for a given user."""
    db = SessionLocal()
    try:
        budgets = db.execute(select(Budget).where(Budget.user_id == user_id)).scalars().all()
        return {
            "status": "success",
            "budgets": [
                {
                    "category_id": b.category_id,
                    "monthly_limit": float(b.monthly_limit),
                    "alert_threshold": float(b.alert_threshold),
                }
                for b in budgets
            ],
        }
    finally:
        db.close()


@mcp.tool()
def set_budget(user_id: int, category_id: int, monthly_limit: float, alert_threshold: float = 0.80) -> dict:
    """Create or update a monthly budget limit for a category."""
    db = SessionLocal()
    try:
        budget = db.execute(
            select(Budget).where(
                Budget.user_id == user_id, Budget.category_id == category_id
            )
        ).scalar_one_or_none()

        if budget:
            budget.monthly_limit = Decimal(str(monthly_limit))
            budget.alert_threshold = Decimal(str(alert_threshold))
        else:
            budget = Budget(
                user_id=user_id,
                category_id=category_id,
                monthly_limit=Decimal(str(monthly_limit)),
                alert_threshold=Decimal(str(alert_threshold)),
            )
            db.add(budget)

        db.commit()
        return {"status": "success", "message": "Budget saved."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "error_details": str(e)}
    finally:
        db.close()

@mcp.tool()
def search_financial_docs(user_id: int, query: str, limit: int = 3) -> dict:
    """Performs semantic vector search across knowledge base documents or user notes using pgvector."""
    db = SessionLocal()
    try:
        # 1. Convert incoming user text query into a vector
        query_vec = get_embedding(query)
        
        # 2. Perform cosine distance search in PostgreSQL using pgvector
        results = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.user_id == user_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
            .limit(limit)
            .all()
        )
        
        if not results:
            return {"status": "success", "matches": []}

        return {
            "status": "success",
            "matches": [r.content for r in results]
        }
    except Exception as e:
        return {"status": "error", "error_details": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")