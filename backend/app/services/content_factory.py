from datetime import datetime, timezone

from app.schemas.platform import ContentPack, ContentPackRequest, IdeaStatus
from app.services.agents.orchestrator import orchestrator
from app.services.growth_score import score_content
from app.services.seed_store import store


def generate_content_pack(request: ContentPackRequest) -> ContentPack:
    idea_run = orchestrator.run_agent("strategist", request.project_id, request.topic, "content_pack")
    script_run = orchestrator.run_agent("scriptwriter", request.project_id, request.topic, "content_pack")
    hook_run = orchestrator.run_agent("hook_doctor", request.project_id, request.topic, "content_pack")
    repurpose_run = orchestrator.run_agent("repurposer", request.project_id, request.topic, "content_pack")

    idea = store.add_idea(
        title=f"{request.topic}: почему это ломает рост канала",
        description=idea_run.result["text"],
        format="Content Pack",
        score=89,
        status=IdeaStatus.approved,
    )
    titles = [
        f"Почему {request.topic} сильнее, чем мотивация",
        f"Ты проигрываешь не из-за лени. Вот настоящая причина",
        f"Одна ошибка, которая убивает дисциплину",
        f"Как собрать себя, когда никто не контролирует",
        f"Перестань ждать настрой. Поставь правило",
    ]
    shorts = [
        "Ты не ленивый. Ты просто каждый день повторяешь слабый сценарий.",
        "Дисциплина начинается не утром. Она начинается вечером, когда ты убираешь соблазн.",
        "Если цель не записана в календарь, это фантазия.",
        "Слабая привычка всегда просит еще один день.",
        "Не ищи мотивацию. Сделай среду, где провалиться сложнее.",
    ]
    script = script_run.result["text"]
    telegram_post = f"{repurpose_run.result['text']}\n\nЗадание: выбери одно правило по теме «{request.topic}» и держи его 7 дней."
    growth_score = score_content(titles[0], f"{script}\n{hook_run.result['text']}")
    calendar_item = None
    if request.add_to_calendar:
        calendar_item = {
            "id": store.new_id("calendar"),
            "title": titles[0],
            "platform": "YouTube",
            "date": str(request.publish_date) if request.publish_date else None,
            "status": "script_ready",
            "script_id": None,
        }

    pack = ContentPack(
        id=store.new_id("pack"),
        project_id=request.project_id,
        topic=request.topic,
        idea=idea,
        youtube_script=script,
        titles=titles,
        shorts=shorts,
        telegram_post=telegram_post,
        growth_score=growth_score,
        calendar_item=calendar_item,
        created_at=datetime.now(timezone.utc),
    )
    store.add_notification("Content Pack готов", f"Пак по теме «{request.topic}» создан.", "generation_completed")
    return pack
