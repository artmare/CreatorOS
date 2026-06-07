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
        title=f"{request.topic}: why this blocks channel growth",
        description=idea_run.result["text"],
        format="Content Pack",
        score=89,
        status=IdeaStatus.approved,
    )
    titles = [
        f"Why {request.topic} beats motivation",
        "You are not losing because you are lazy. Here is the real reason",
        "One mistake that quietly kills discipline",
        "How to rebuild control when nobody is watching",
        "Stop waiting for the mood. Set the rule",
    ]
    shorts = [
        "You are not lazy. You keep repeating a weak script.",
        "Discipline starts the night before, when you remove the easiest excuse.",
        "If the goal is not on the calendar, it is still a fantasy.",
        "A weak habit always asks for one more day.",
        "Do not chase motivation. Build an environment where failure is harder.",
    ]
    script = script_run.result["text"]
    telegram_post = f"{repurpose_run.result['text']}\n\nChallenge: choose one rule about '{request.topic}' and hold it for 7 days."
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
    store.add_notification("Content pack ready", f"The pack for '{request.topic}' is ready.", "generation_completed")
    store.content_packs[pack.id] = pack
    return pack
