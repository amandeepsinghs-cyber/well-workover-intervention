"""A2UI v0.9 runtime extension negotiating executor for Gemini Enterprise and A2A."""

from __future__ import annotations

import logging
from typing import Any, Optional

from a2a.server.events import EventQueue
from a2a.types import AgentCard
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
    RequestContext,
)

from agent.integration.agent_card import A2UI_V09_EXTENSION_URI

logger = logging.getLogger(__name__)

A2UI_EXTENSION_PREFIX: str = "https://a2ui.org/a2a-extension/a2ui/"
A2UI_STATE_KEY: str = "active_a2ui_version"


class A2uiNegotiatingExecutor(A2aAgentExecutor):
    """Subclass of ADK A2aAgentExecutor that performs runtime A2UI v0.9 negotiation."""

    def __init__(
        self,
        *,
        runner: Any,
        agent_card: AgentCard | None = None,
        config: Optional[A2aAgentExecutorConfig] = None,
    ):
        super().__init__(runner=runner, config=config)
        self._agent_card = agent_card

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            if hasattr(context, "call_context") and hasattr(context.call_context, "state"):
                context.call_context.state[A2UI_STATE_KEY] = "v0.9"
            if hasattr(context, "add_activated_extension") and callable(context.add_activated_extension):
                context.add_activated_extension(A2UI_V09_EXTENSION_URI)
        except Exception as exc:
            logger.debug("A2UI extension activation warning: %s", exc)
        await super().execute(context, event_queue)
