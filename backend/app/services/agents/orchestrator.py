from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.schemas.platform import AgentRun
from app.services.agents.openai_adapter import OpenAIAdapter
from app.services.agents.prompts import AGENT_PROMPTS
from app.services.quality import memory_context, validate_output
from app.services.seed_store import store
from app.services.usage import assert_usage_available, estimate_cost, estimate_tokens, record_usage


class ProducerOrchestrator:
    def __init__(self) -> None:
        self.openai = OpenAIAdapter()
        self.settings = get_settings()

    def choose_agents(self, message: str) -> list[str]:
        normalized = message.lower()
        agents = []
        if any(word in normalized for word in ["стратег", "план", "что снять", "strategy"]):
            agents.append("strategist")
        if any(word in normalized for word in ["сценар", "script", "youtube"]):
            agents.append("scriptwriter")
        if any(word in normalized for word in ["хук", "hook", "заголов"]):
            agents.append("hook_doctor")
        if any(word in normalized for word in ["конкур", "competitor"]):
            agents.append("competitor_analyst")
        if any(word in normalized for word in ["рост", "score", "growth"]):
            agents.append("growth_coach")
        if any(word in normalized for word in ["shorts", "telegram", "переупак"]):
            agents.append("repurposer")
        return agents or ["strategist"]

    def run_agent(self, agent_name: str, project_id: str, prompt: str, intent: str = "generate") -> AgentRun:
        assert_usage_available()
        memory = store.memories[project_id]
        system = f"{AGENT_PROMPTS[agent_name]}\n\nКонтекст проекта:\n{memory_context(memory)}"
        live_text = self.openai.generate(system, prompt)
        result_text = live_text or self._mock_result(agent_name, prompt)
        validation = validate_output(result_text)
        model = self.settings.openai_model if live_text else "mock-agent"
        tokens = estimate_tokens(system, prompt, result_text)
        cost = estimate_cost(model, tokens)

        run = AgentRun(
            id=store.new_id("run"),
            workspace_id="ws_creatoros_demo",
            project_id=project_id,
            agent_name=agent_name,
            intent=intent,
            input={"prompt": prompt},
            memory_used=memory,
            model=model,
            result={"text": result_text, "validation": validation},
            cost_estimate=cost,
            validation_status=str(validation["status"]),
            status="completed",
            created_at=datetime.now(timezone.utc),
        )
        store.agent_runs[run.id] = run
        record_usage(run.workspace_id, "system", f"agent:{agent_name}", model, tokens, cost)
        store.add_activity("запустил агента", "agent_run", run.id)
        return run

    def produce(self, project_id: str, message: str) -> dict[str, Any]:
        agents = self.choose_agents(message)
        runs = [self.run_agent(agent, project_id, message, "orchestrated") for agent in agents]
        store.add_notification(
            "AI Producer завершил работу",
            f"Готово: {', '.join(agent.replace('_', ' ') for agent in agents)}.",
            "generation_completed",
        )
        return {
            "intent": message,
            "agents": agents,
            "runs": runs,
            "summary": "AI Producer собрал ответ из specialist-agent runs.",
        }

    def _mock_result(self, agent_name: str, prompt: str) -> str:
        variants = {
            "strategist": f"**Стратегия:** тема «{prompt}» должна идти через конфликт: зритель уже знает, что надо делать, но защищает слабую привычку.\n\n1. Начни с жесткого тезиса.\n2. Покажи цену бездействия.\n3. Дай одно задание на 24 часа.",
            "scriptwriter": f"**Хук:** Ты не устал. Ты просто слишком долго живешь без правил.\n\n**Сцена 1:** короткая пауза, темный фон, взгляд в камеру.\n**Конфликт:** герой хочет роста, но каждый вечер продает цель за комфорт.\n**Шаги:** убрать один триггер, поставить дедлайн, отчитаться публично.\n**CTA:** выбери одно правило и держи его 7 дней.",
            "hook_doctor": "**Диагноз:** слабый хук слишком общий.\n\n1. Ты не ленивый. Ты тренируешь слабую версию себя.\n2. Дисциплина не приходит. Ее ставят как замок на дверь.\n3. Если день начинается без правила, он уже принадлежит чужим желаниям.",
            "competitor_analyst": "**Радар:** конкуренты часто говорят про привычки, но редко показывают цену одной сорванной недели.\n\nУпущенные темы: дисциплина после провала, стыд без самоуничтожения, деньги как результат навыка.",
            "growth_coach": "**Задание недели:** 3 идеи, 1 сценарий, 5 хуков.\n\nКритерий: каждая идея должна иметь боль, конфликт и действие. Без этого она идет в rejected.",
            "repurposer": "**Shorts:** 5 коротких углов из темы.\n\n**Telegram:** Пост с тезисом, личным наблюдением и заданием на вечер.",
        }
        return variants[agent_name]


orchestrator = ProducerOrchestrator()
