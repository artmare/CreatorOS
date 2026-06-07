from app.schemas.platform import GrowthScore


CRITERIA = {
    "hook": "Есть конфликт, боль или неожиданный тезис в первых секундах.",
    "title": "Заголовок понятен, конкретен и вызывает желание кликнуть.",
    "retention": "Структура держит внимание через напряжение, примеры и смену ритма.",
    "emotion": "Материал вызывает злость, надежду, стыд, азарт или облегчение.",
    "virality": "Тема легко обсуждается, спорится или пересылается.",
    "clarity": "Зритель сразу понимает, о чем ролик и что делать дальше.",
}


def score_content(title: str, body: str) -> GrowthScore:
    text = f"{title} {body}".lower()

    hook = 90 if any(x in text for x in ["почему", "ты не", "ошибка", "слаб"]) else 68
    title_score = 88 if len(title) <= 80 and any(x in title.lower() for x in ["почему", "как", "ты"]) else 72
    retention = 86 if any(x in text for x in ["история", "конфликт", "шаг"]) else 70
    emotion = 90 if any(x in text for x in ["боль", "стыд", "злость", "победа", "страх"]) else 74
    virality = 84 if any(x in text for x in ["спор", "правда", "никто"]) else 70
    clarity = 88 if len(body) > 300 and "\n" in body else 75
    overall = round((hook + title_score + retention + emotion + virality + clarity) / 6)

    improvements = []
    if hook < 85:
        improvements.append("Добавь конфликт в первые 10 секунд.")
    if title_score < 85:
        improvements.append("Сделай заголовок короче и конкретнее.")
    if retention < 85:
        improvements.append("Разбей сценарий на поворотные точки каждые 30-45 секунд.")
    if virality < 80:
        improvements.append("Добавь спорный тезис, который хочется обсудить.")

    return GrowthScore(
        hook=hook,
        title=title_score,
        retention=retention,
        emotion=emotion,
        virality=virality,
        clarity=clarity,
        overall=overall,
        criteria=CRITERIA,
        improvements=improvements or ["Материал уже сильный. Усиль примеры и финальный CTA."],
    )
