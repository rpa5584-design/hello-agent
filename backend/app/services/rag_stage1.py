"""Propose and independently validate SQL, without database execution."""

from collections.abc import Callable

from app.services import openrouter
from app.services.sql_validation import ValidatedSql, validate_sql


def propose_sql(question: str, system_prompt: str, on_proposal: Callable[[str], None] | None = None) -> ValidatedSql:
    proposal = openrouter.complete_messages([
        {"role": "system", "content": system_prompt + "\nStage 1 only: propose one bounded SELECT as plain SQL. Do not produce an answer or Markdown."},
        {"role": "user", "content": question},
    ])
    if on_proposal is not None:
        on_proposal(proposal)
    return validate_sql(proposal)
