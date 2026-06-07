from app.core.config import get_settings


def create_checkout(plan: str) -> dict[str, object]:
    settings = get_settings()
    variant_by_plan = {
        "starter": settings.lemonsqueezy_starter_variant_id,
        "creator_pro": settings.lemonsqueezy_pro_variant_id,
        "agency": settings.lemonsqueezy_agency_variant_id,
    }
    return {
        "enabled": bool(settings.lemonsqueezy_api_key),
        "provider": "lemon_squeezy",
        "plan": plan,
        "variant_id": variant_by_plan.get(plan),
        "checkout_url": None,
        "message": "Set Lemon Squeezy env vars to create live checkout links.",
    }


def handle_webhook(payload: dict[str, object]) -> dict[str, object]:
    return {"received": True, "provider": "lemon_squeezy", "event": payload.get("meta", {}).get("event_name")}
