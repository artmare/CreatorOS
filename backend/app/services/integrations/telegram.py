from typing import Any

from app.core.config import get_settings
from app.services.agents.orchestrator import orchestrator


def handle_telegram_update(update: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    text = update.get("message", {}).get("text", "/help")
    enabled = bool(settings.telegram_bot_token)

    command_map = {
        "/idea": "дай идею",
        "/script": "напиши сценарий",
        "/title": "улучши заголовки и хук",
        "/plan": "сделай контент-план",
        "/score": "оцени Growth Score",
        "/competitor": "проанализируй конкурента",
        "/shorts": "переупакуй в Shorts",
        "/style": "обнови стиль",
    }
    intent = next((mapped for command, mapped in command_map.items() if text.startswith(command)), "помощь")
    result = orchestrator.produce("project_youtube", f"{intent}: {text}")
    return {
        "enabled": enabled,
        "reply": result["runs"][0].result["text"] if result["runs"] else "Команда принята.",
    }
