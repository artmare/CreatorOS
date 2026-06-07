from openai import OpenAI

from app.core.config import get_settings
from app.services.events import events


class OpenAIAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: OpenAI | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key)

    @property
    def client(self) -> OpenAI | None:
        if not self.enabled:
            return None
        if self._client is None:
            self._client = OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.openai_timeout_seconds,
                max_retries=self.settings.openai_max_retries,
            )
        return self._client

    def generate(self, system: str, user: str) -> str:
        client = self.client
        if client is None:
            return ""

        try:
            response = client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.output_text
        except Exception as exc:  # pragma: no cover - live provider path
            events.error("openai", str(exc), {"model": self.settings.openai_model})
            return ""
