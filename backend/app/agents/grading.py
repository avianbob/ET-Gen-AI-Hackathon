# backend/app/agents/grading.py
from dataclasses import dataclass
from typing import List, Dict
from ..schemas.analysis import AgentResult, GradingBreakdown


@dataclass
class GradingWeights:
    """
    Weightage for each group, reflecting your concept note.
    Fine-Tuned for "Commercial Viability" focus - prioritizing Market Demand and Patents.
    Adjust these numbers to tune the final grade.
    """
    market_demand: float = 0.35        # Increased from 0.25 (Sales matter most)
    production_feasibility: float = 0.15  # Decreased from 0.25 (We can outsource production)
    demographics: float = 0.10          # Decreased from 0.15
    patents_and_trials: float = 0.25   # Increased from 0.2 (High importance - Legal risk is fatal)
    competition: float = 0.15          # Unchanged


class GradingAgent:
    """
    Converts agent outputs into a single composite grade (0–1).
    """

    def __init__(self, weights: GradingWeights | None = None) -> None:
        self.weights = weights or GradingWeights()

    def _extract_scores(self, results: List[AgentResult]) -> Dict[str, float]:
        """
        Reads raw_data fields from agents and computes average scores per dimension.
        This is where your 'beautiful mathematical formula' can become sophisticated.
        """

        market_scores = []
        production_scores = []
        demo_scores = []
        patents_scores = []
        competition_scores = []

        for r in results:
            rd = r.raw_data
            name = r.agent_name.lower()

            # Market, Sales & Demand group
            if "iqvia" in name or "exim" in name:
                if "market_demand_score" in rd:
                    market_scores.append(rd["market_demand_score"])
                if "overall_market_demand_score" in rd:
                    market_scores.append(rd["overall_market_demand_score"])

            # Production / Chemical Engineering group
            if "processdesign" in name or "process design" in name:
                if "production_feasibility_score" in rd:
                    production_scores.append(rd["production_feasibility_score"])
            if "techno" in name:
                if "production_feasibility_score" in rd:
                    production_scores.append(rd["production_feasibility_score"])

            # Demographic group
            if "demographic" in name:
                if "demographic_overall_score" in rd:
                    demo_scores.append(rd["demographic_overall_score"])

            # Patent & Trials group
            if "patent" in name:
                if "patent_overall_score" in rd:
                    patents_scores.append(rd["patent_overall_score"])
            if "clinical" in name:
                if "patents_and_trials_score" in rd:
                    patents_scores.append(rd["patents_and_trials_score"])

            # Competition group
            if "competition" in name:
                if "competition_overall_score" in rd:
                    competition_scores.append(rd["competition_overall_score"])

        def avg(lst: List[float], default: float = 0.5) -> float:
            return sum(lst) / len(lst) if lst else default

        scores = {
            "market_demand": avg(market_scores),
            "production_feasibility": avg(production_scores),
            "demographics": avg(demo_scores),
            "patents_and_trials": avg(patents_scores),
            "competition": avg(competition_scores),
        }

        return scores

    def grade(self, results: List[AgentResult]) -> GradingBreakdown:
        scores = self._extract_scores(results)

        overall = (
            scores["market_demand"] * self.weights.market_demand
            + scores["production_feasibility"] * self.weights.production_feasibility
            + scores["demographics"] * self.weights.demographics
            + scores["patents_and_trials"] * self.weights.patents_and_trials
            + scores["competition"] * self.weights.competition
        )

        return GradingBreakdown(
            market_demand=scores["market_demand"],
            production_feasibility=scores["production_feasibility"],
            demographics=scores["demographics"],
            patents_and_trials=scores["patents_and_trials"],
            competition=scores["competition"],
            overall_score=overall,
        )