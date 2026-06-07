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
        raise RuntimeError("Plan limit exceeded. Upgrade or wait for the monthly reset.")
