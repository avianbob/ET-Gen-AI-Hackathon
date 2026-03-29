# backend/app/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..schemas.analysis import AnalysisRequest, AgentResult


class BaseAgent(ABC):
    """
    Base class for all domain agents.
    Every agent returns an AgentResult.
    """

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def run(self, request: AnalysisRequest) -> AgentResult:
        ...

    @staticmethod
    def _clamp_score(score: float) -> float:
        """Keep heuristic scores in a 0-1 range."""
        return max(0.0, min(1.0, score))

    def _apply_complexity(self, score: float, complexity: str | None) -> float:
        """
        Adjust a base score based on request complexity.
        Higher complexity nudges scores down slightly; low complexity bumps them up.
        """
        adjustments = {"low": 0.05, "normal": 0.0, "high": -0.05}
        delta = adjustments.get((complexity or "normal").lower(), 0.0)
        return self._clamp_score(score + delta)

    def _result(self, summary: str, raw_data: Dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            raw_data=raw_data or {},
        )