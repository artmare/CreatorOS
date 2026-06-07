from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "creatoros",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="creatoros.generate_content_pack")
def generate_content_pack_job(topic: str) -> dict[str, str]:
    return {"status": "queued", "topic": topic}
