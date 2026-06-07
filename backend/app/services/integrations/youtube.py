from app.core.config import get_settings


def competitor_summary(channel_url: str) -> dict[str, object]:
    return {
        "enabled": bool(get_settings().youtube_api_key),
        "channel_url": channel_url,
        "top_patterns": ["жесткие заголовки", "короткие истории", "контраст до/после"],
        "missed_topics": ["дисциплина после срыва", "как не слить неделю", "навык вместо настроения"],
    }


def own_channel_summary(channel_id: str) -> dict[str, object]:
    return {
        "enabled": bool(get_settings().youtube_api_key),
        "channel_id": channel_id,
        "growth": "+12% за 30 дней",
        "best_topics": ["дисциплина", "ответственность", "деньги через навык"],
        "weak_topics": ["абстрактная мотивация"],
    }
