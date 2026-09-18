"""Agent orchestration + observability models (spec §17, §18, §37).

agent_runs   → one orchestration run (mission or request)
agent_tasks  → one agent's step within a run
agent_events → granular events the UI streams (progress, tool calls, results)
"""

from sqlalchemy import (
    BigInteger,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base, TimestampMixin


class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mission_id: Mapped[int | None] = mapped_column(ForeignKey("scouting_missions.id"), nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    request: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending | running | completed | failed | cancelled
    mission_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # §17 orchestrated plan
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class AgentTask(Base, TimestampMixin):
    __tablename__ = "agent_tasks"
    __table_args__ = (Index("ix_at_status", "status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(60), nullable=False, index=True)  # scout|data|research|market|tactical|comparison|verification|report
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)  # UI headline, e.g. "Analyzed 18,421 players"
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentEvent(Base, TimestampMixin):
    __tablename__ = "agent_events"
    __table_args__ = (Index("ix_ae_run", "run_id", "seq"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("agent_tasks.id"), nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    # task_started | task_completed | tool_call | tool_result | message | verification_flag | error
    action: Mapped[str | None] = mapped_column(String(160), nullable=True)
    tool: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)