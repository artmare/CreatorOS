from typing import Any

from fastapi import HTTPException, status

from app.services.seed_store import store


TOKEN_COST_PER_1K = {
    "gpt-5-mini": 0.002,
    "mock-agent": 0.0,
}


def estimate_tokens(*parts: str) -> int:
    joined = " ".join(parts)
    return max(64, len(joined) // 4)


def estimate_cost(model: str, tokens: int) -> float:
    return round((tokens / 1000) * TOKEN_COST_PER_1K.get(model, 0.002), 6)


def assert_usage_available() -> None:
    usage = store.usage_summary()
    if usage.blocked:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Plan limit exceeded. Upgrade or wait for the monthly reset.",
        )


def record_usage(
    workspace_id: str,
    user_id: str,
    generation_type: str,
    model: str,
    token_estimate: int,
    cost_estimate: float,
    blocked: bool = False,
) -> dict[str, Any]:
    record = {
        "id": store.new_id("usage"),
        "workspace_id": workspace_id,
        "user_id": user_id,
        "generation_type": generation_type,
        "model": model,
        "token_estimate": token_estimate,
        "cost_estimate": cost_estimate,
        "blocked": blocked,
    }
    store.usage_ledger.insert(0, record)
    return record
