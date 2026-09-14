from datetime import datetime
from typing import Any, Dict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64, json, os
import pandas as pd
from sqlalchemy import select, text, or_
from sqlalchemy.orm import Session
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPToolset
from pydantic_ai_harness.subagents import SubAgent, SubAgents
from pydantic import BaseModel
from .database import AgentState, Category
from .models import ChartSpec, ChartSeries, DataFrameProfile, VisualizationResult
from fastapi.security import APIKeyHeader
from dataclasses import dataclass


# Move these schema classes here from agents.py cleanup:
class SummarySchema(BaseModel):
    summary: str
    open_questions: list[str]
    recommended_next_actions: list[str]

class VisualizationSchema(BaseModel):
    sql_query: str
    python_code: str
    chart_spec: ChartSpec
    reasoning: str

budget_tools = MCPToolset("http://localhost:8001/mcp")

@dataclass
class AgentState:
    db: Session
    current_user_id: int

# Option 1: Meta Llama 3.3 70B Instruct (Recommended for tool calling & general logic)
opencode_model = OpenAIChatModel(
    "openrouter/free",  # Automatically routes to any available free model
    provider=OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    ),
)

transaction_agent = Agent(
    # 'google:gemini-2.5-flash',
    opencode_model,
    name='transaction_agent',
    description='Queries the database using SQL to check expenses, income, totals, and transaction history.',
    toolsets=[budget_tools]
)
budget_agent = Agent(
    # 'google:gemini-2.5-flash',
    opencode_model,
    name='budget_agent',
    description='Analyzes budget-related data',
    system_prompt="""
    You are a budget management agent. 
    You are explicitly authorized to SELECT, INSERT, and UPDATE rows in the `budgets` table using `execute_sql_query`.
    When a user asks to change or set a budget limit, execute the corresponding SQL UPDATE or INSERT query.,
    """,
    toolsets=[budget_tools]
)
summarizer_agent = Agent(
    'google:gemini-2.5-flash',
    name='summarizer_agent',
    output_type=SummarySchema,
    system_prompt="""
    You are a state-tracking agent for a personal finance system.
    Your task is to produce a factual JSON summary reflecting the CURRENT ACTIVE STATE of the user's account and conversation — not just the most recent topic discussed.

    CRITICAL STATE-TRACKING RULES:
    1. ALWAYS REPORT CURRENT ACTIVE STATE, REGARDLESS OF WHEN IT WAS SET:
       - The `summary` field MUST mention any budgets, limits, or settings that are currently active,
         even if they were set or modified earlier in the conversation and not the most recent topic.
       - Example: if a Groceries budget was set to $500 and later reduced to $450, the summary must
         say the CURRENT budget is $450 — do not omit this just because a different topic (like a
         web search request) was discussed afterward.

    2. OVERWRITE OLD VALUES WITH LATEST TURNS:
       - If a budget or preference was set to $500 earlier, but reduced by $50 later, the active budget MUST be $450.00.
       - Always use the most recent value confirmed in the transcript.

    3. DO NOT LET THE MOST RECENT MESSAGE DOMINATE THE SUMMARY:
       - Summarize the conversation as a whole — key actions taken, current settings, and unresolved
         goals — not just whatever was discussed last.

    4. OPEN QUESTIONS / UNRESOLVED GOALS:
       - `open_questions` should capture active user goals that have NOT been finalized yet.
       - Do NOT leave `open_questions` empty if the user's high-level goal is still pending a decision.

    5. DO NOT INCLUDE RESOLVED REFUSALS:
       - Past tool errors or web search denials that were addressed in previous turns are NOT open questions,
         UNLESS the user's underlying request is still unmet (in which case, note the unmet request itself,
         not the refusal).
    When outputting tables or lists, strictly format markdown tables using proper line breaks (\n) 
    for every row so that GitHub Flavored Markdown table parsers can render them properly.
    Output strictly valid JSON matching the target schema.
    """
)

DATAFRAME_SUMMARY_THRESHOLD = 30
dataframe_agent = Agent(
    'google:gemini-2.5-flash',
    # opencode_model,
    name='dataframe_agent',
    system_prompt="""
    You are a financial data summarization agent.
    You receive raw transaction rows and must produce a clear, concise summary.
    
    Include in your summary:
    - Total number of transactions
    - Date range of transactions
    - Total income vs total expenses
    - Top 3-5 spending categories with amounts
    - Largest single transactions (top 3)
    - Average transaction amount
    - Any notable patterns or anomalies
    When outputting tables or lists, strictly format markdown tables using proper line breaks (\n) 
    for every row so that GitHub Flavored Markdown table parsers can render them properly.
    Be specific with numbers and currency amounts.
    Do NOT list individual rows — summarize the data meaningfully.
    """
)

forecast_agent = Agent(
    # 'google:gemini-2.5-flash',
    opencode_model,
    name='forecast_agent',
    description='Predicts future financial trends',
    system_prompt="""
    You analyze historical financial transactions to forecast future spending.
    1. First, query past monthly or total expense sums using standard SQL SELECT queries:
       SELECT SUM(amount) FROM transactions WHERE transaction_type = 'expense' AND user_id = 2;
    2. Do NOT use complex date math functions that might fail in SQL.
    3. Calculate estimated future expenses based on average past spending and summarize your forecast clearly.
    4. When outputting tables or lists, strictly format markdown tables using proper line breaks (\n)
    for every row so that GitHub Flavored Markdown table parsers can render them properly.
    """,
    toolsets=[budget_tools]
)


visualization_agent = Agent(
    'google:gemini-2.5-flash',
    name='visualization_agent',
    output_type=VisualizationSchema,
    system_prompt="""
    You are a financial data visualization agent.
    Given a user question, you must return:

    1. sql_query: A valid PostgreSQL query using:
       SELECT c.name as category, SUM(t.amount) as total
       FROM transactions t
       LEFT JOIN categories c ON t.category_id = c.category_id
       WHERE t.user_id = {user_id}
         AND t.transaction_type = 'expense'
         AND c.name IS NOT NULL
       GROUP BY c.name ORDER BY total DESC
       Always alias transactions as t, categories as c.
       Always filter by the user_id provided.

    2. python_code: A Python code string using pandas and matplotlib
       that assumes a variable `df` already exists as a DataFrame
       with columns matching the SQL output. Example:
       
       import matplotlib.pyplot as plt
       fig, ax = plt.subplots(figsize=(8, 4))
       ax.pie(df['total'], labels=df['category'], autopct='%1.1f%%')
       ax.set_title('Spending by Category')
       plt.tight_layout()

       Do NOT include df definition or plt.show() in the code.
       Do NOT include fig.savefig() — that is handled externally.

    3. chart_spec: title, chart_type ("bar"/"line"/"pie"), 
       labels and series will be populated from real data externally
       so leave labels=[] and series=[].

    4. reasoning: why you chose this chart type.
    """
)


orchestrator = Agent(
    opencode_model,
    system_prompt="""
    You route financial requests. 
    - Route transaction creation/modification to `transaction_agent`.
    - Route budget updates/creations/queries to `budget_agent`.
    - Route forecasting to `forecast_agent`.
    - Do NOT handle chart or visualization requests — these are handled externally.
    IMPORTANT: If the user asks for a chart, graph, visualization, or anything visual,
    respond with ONLY this exact sentence: 
    "Generating your chart now."
    Do NOT query any data. Do NOT delegate to any agent. Just return that sentence.
    When a sub-agent returns summarized: true, present the data field directly.
    Do not refuse database modification requests.
    """,
    capabilities=[
        SubAgents(agents=[
            SubAgent(transaction_agent),
            SubAgent(budget_agent),
            SubAgent(forecast_agent),
            # SubAgent(visualization_agent),
        ])
    ],
    deps_type=AgentState
)


all_subagents = [transaction_agent, budget_agent, forecast_agent]

SCHEMA_CONTEXT = """
You are working with the following PostgreSQL schema:
TABLE users (
user_id SERIAL PRIMARY KEY,
email VARCHAR(100) UNIQUE NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
currency VARCHAR(3) DEFAULT 'USD'
)

TABLE categories (
category_id SERIAL PRIMARY KEY,
user_id INT REFERENCES users(user_id) ON DELETE CASCADE, -- NULL = system global default
name VARCHAR(50) NOT NULL,
type VARCHAR(10) CHECK (type IN ('income', 'expense'))
)

TABLE transactions (
transaction_id SERIAL PRIMARY KEY,
user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
category_id INT REFERENCES categories(category_id) ON DELETE SET NULL,
amount DECIMAL(12, 2) NOT NULL,
transaction_type VARCHAR(10) CHECK (transaction_type IN ('income', 'expense', 'transfer')),
description TEXT,
transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)

TABLE budgets (
budget_id SERIAL PRIMARY KEY,
user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
category_id INT REFERENCES categories(category_id) ON DELETE CASCADE,
monthly_limit DECIMAL(12, 2) NOT NULL,
alert_threshold DECIMAL(3,2) DEFAULT 0.80)
""".strip()

SYSTEM_INSTRUCTIONS = """
You are a database querying assistant. 
Your ONLY task is to answer user financial questions by querying the PostgreSQL database using the `execute_sql_query` tool.

RULES:
1. NEVER perform a web search or external API calls.
2. ALWAYS generate a valid SQL SELECT query to find answers from the database tables (`transactions`, `categories`, `budgets`, `users`).
3. NEVER guess or hallucinate financial numbers.
""".strip()


def build_schema_context(ctx: RunContext[AgentState]) -> str:
    user_id = ctx.deps.current_user_id
    
    # Fetch both global system categories (user_id IS NULL) AND user custom categories
    stmt = select(Category).where(
        or_(Category.user_id == user_id, Category.user_id.is_(None))
    )
    categories = ctx.deps.db.execute(stmt).scalars().all()

    if categories:
        category_lines = "\n".join(
            f"- id={c.category_id}, name={c.name!r}, type={c.type}, scope={'Global' if c.user_id is None else 'Custom'}"
            for c in categories
        )
    else:
        category_lines = "(no categories available)"

    return (
        f"{SCHEMA_CONTEXT}\n\n"
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"STRICT SECURITY RULE: You are operating strictly on user_id={user_id}. "
        f"EVERY SQL query you run MUST include 'WHERE user_id = {user_id}' (or AND user_id = {user_id}). "
        f"Never perform queries without filtering by user_id={user_id}.\n\n"
        f"Available categories for user_id={user_id}:\n{category_lines}"
    )

# 2. Attach instructions to all 3 sub-agents dynamically
for subagent in all_subagents:
    subagent.instructions(build_schema_context)

def execute_sql_query(ctx: RunContext[AgentState], query: str) -> Dict[str, Any]:
    clean_query = query.strip().rstrip(";")
    try:
        result = ctx.deps.db.execute(text(clean_query))

        if result.returns_rows:
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

            # ← NEW: check threshold and summarize if needed
            if len(rows) >= DATAFRAME_SUMMARY_THRESHOLD:
                summary = summarize_dataframe_if_large(
                    rows=rows,
                    query_context=query,
                    threshold=DATAFRAME_SUMMARY_THRESHOLD,
                )
                return {
                    "status": "success",
                    "row_count": len(rows),
                    "summarized": True,
                    "data": summary,  # agent gets a text summary instead of raw rows
                }

            return {
                "status": "success",
                "row_count": len(rows),
                "summarized": False,
                "data": rows,
            }

        ctx.deps.db.commit()
        return {
            "status": "success",
            "affected_rows": result.rowcount,
            "message": "Query executed successfully.",
        }

    except Exception as e:
        try:
            ctx.deps.db.rollback()
        except Exception:
            pass

        return {
            "status": "error",
            "error_details": f"SQL Error: {e!s}.",
        }

for subagent in all_subagents:
    subagent.tool(execute_sql_query)

API_KEY_NAME = "X-API-Key"
VALID_API_KEY = os.getenv("INGESTION_API_KEY", "my-super-secret-ingestion-key-123")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def summarize_dataframe_if_large(
    rows: list[dict],
    query_context: str = "",
    threshold: int = DATAFRAME_SUMMARY_THRESHOLD,
) -> str:
    if len(rows) < threshold:
        # Small enough — just return raw rows as formatted text
        lines = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in rows]
        return "\n".join(lines)

    # Too large — summarize with the dataframe agent
    rows_text = "\n".join(
        [", ".join(f"{k}: {v}" for k, v in row.items()) for row in rows]
    )
    prompt = f"""
    The user asked: {query_context}
    Here are {len(rows)} transaction rows:
    {rows_text}
    Summarize this data clearly and concisely.
    """
    result = dataframe_agent.run_sync(prompt)
    return result.output

def summarize_dataframe_profile(df: pd.DataFrame) -> DataFrameProfile:
    """Instructor pattern: reduce df to facts safe to send to an agent."""
    numeric_cols = list(df.select_dtypes(include=["number"]).columns)
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    return DataFrameProfile(
        row_count=len(df),
        column_count=len(df.columns),
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
    )

def build_chart_from_spec(spec: ChartSpec) -> str:
    """Render a ChartSpec to a base64 PNG string."""
    fig, ax = plt.subplots(figsize=(8, 4))

    if spec.chart_type == "bar":
        x = range(len(spec.labels))
        for series in spec.series:
            ax.bar(x, series.values, label=series.label)
        ax.set_xticks(list(x))
        ax.set_xticklabels(spec.labels, rotation=30, ha="right")

    elif spec.chart_type == "line":
        x = range(len(spec.labels))
        for series in spec.series:
            ax.plot(list(x), series.values, marker="o", label=series.label)
        ax.set_xticks(list(x))
        ax.set_xticklabels(spec.labels, rotation=30, ha="right")

    elif spec.chart_type == "pie":
        values = spec.series[0].values if spec.series else []
        ax.pie(values, labels=spec.labels, autopct="%1.1f%%")

    ax.set_title(spec.title)
    if spec.chart_type != "pie":
        ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def run_visualization(
    user_question: str,
    user_id: int,
    db: Session,
) -> VisualizationResult:
    prompt = f"""
        User question: {user_question}
        User ID: {user_id}
        Generate SQL, Python visualization code, and chart spec.
        Always include WHERE user_id = {user_id} in your SQL.
        """
    agent_result = visualization_agent.run_sync(prompt)
    schema: VisualizationSchema = agent_result.output

    # Execute SQL
    db.rollback()
    result = db.execute(text(schema.sql_query.strip().rstrip(";")))
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result.fetchall()]

    if not rows:
        raise ValueError("SQL query returned no rows.")

    df = pd.DataFrame(rows)
    label_col, value_col = columns[0], columns[1]

    # Build ECharts config instead of matplotlib figure
    echarts_option = {
        "title": {"text": schema.chart_spec.title},
        "tooltip": {},
        "xAxis": {"data": [str(r[label_col]) for r in rows]},
        "yAxis": {},
        "series": [{
            "type": schema.chart_spec.chart_type,  # "bar", "line", "pie"
            "data": [float(r[value_col]) for r in rows],
        }]
    }

    # For pie charts, format is different
    if schema.chart_spec.chart_type == "pie":
        echarts_option = {
            "title": {"text": schema.chart_spec.title},
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "pie",
                "data": [
                    {"name": str(r[label_col]), "value": float(r[value_col])}
                    for r in rows
                ]
            }]
        }

    return VisualizationResult(
        sql_query=schema.sql_query,
        python_code=schema.python_code,
        dataframe_json=df.to_json(orient="records"),
        chart_spec=schema.chart_spec,
        chart_base64=json.dumps(echarts_option),  # ← send echarts config as JSON string
        row_count=len(rows),
        profile=summarize_dataframe_profile(df),
    )


CHART_KEYWORDS = [
    "pie chart", "bar chart", "line chart", "chart", "graph", "plot",
    "visualize", "visual", "breakdown", "compare", "distribution",
    "trend", "over time", "by category", "show me a", "top 5", "top 3"
]

def classify_intent(user_message: str) -> bool:
    msg = user_message.lower()
    return any(kw in msg for kw in CHART_KEYWORDS)
