from app.schemas.platform import ProjectMemory


def validate_output(text: str, language_hint: str = "ru") -> dict[str, object]:
    warnings: list[str] = []
    clean = text.strip()

    if not clean:
        warnings.append("empty_output")
    if len(clean) < 80:
        warnings.append("too_short")
    generic_markers = ["10 идей", "хорошая идея", "попробуйте", "может быть полезно"]
    if any(marker.lower() in clean.lower() for marker in generic_markers):
        warnings.append("too_generic")
    if language_hint == "ru" and not any("а" <= char.lower() <= "я" or char == "ё" for char in clean):
        warnings.append("language_mismatch")
    if "**" not in clean and "\n" not in clean and len(clean) > 500:
        warnings.append("formatting_check")
    if any(word in clean.lower() for word in ["просмотры выросли", "гарантирует", "точно наберет"]):
        warnings.append("analytics_claim_warning")

    return {
        "status": "passed" if not warnings else "warning",
        "warnings": warnings,
    }


def memory_context(memory: ProjectMemory) -> str:
    return "\n".join(
        [
            f"Ниша: {memory.niche}",
            f"Аудитория: {memory.audience}",
            f"Тон: {memory.tone}",
            "Правила: " + "; ".join(memory.content_rules),
            "Форматы: " + ", ".join(memory.preferred_formats),
            "Отклоненные идеи: " + "; ".join(memory.rejected_ideas),
            "Лучшие темы: " + ", ".join(memory.best_performing_topics),
            "Успешные сценарии: " + " | ".join(memory.past_successful_scripts),
        ]
    )
