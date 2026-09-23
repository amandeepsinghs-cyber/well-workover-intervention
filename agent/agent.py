"""
agent/agent.py

Production Google ADK Agent (google.adk.agents.Agent) for the
ONGC Assam Asset (Geleki Field) Workover & Well Intervention Planner.
"""

from dataclasses import asdict
from datetime import date
from typing import Callable

from google.adk.agents import Agent

from agent.adk_tools import ADK_TOOLS
from agent.prompt import SYSTEM_PROMPT
from tools import (
    chan_diagnostic,
    check_mro,
    check_offsets,
    detect_mechanical_signature,
    estimate_uplift,
    fillage_proxy,
    fit_decline_curve,
    generate_draft_plan,
    generate_report,
    plot_production,
    predict_failure,
    query_wells,
    rank_candidates,
    render_well_map,
    route_intervention,
    schedule_rigs,
    search_well_history,
    trigger_scan,
)

ALL_TOOLS: list[Callable] = [
    render_well_map,              # TC-016
    fit_decline_curve,            # TC-001
    chan_diagnostic,              # TC-002
    fillage_proxy,                # TC-003
    check_offsets,                # TC-004
    detect_mechanical_signature,  # TC-005
    predict_failure,              # TC-006
    trigger_scan,                 # TC-007
    route_intervention,           # TC-008
    estimate_uplift,              # TC-009
    rank_candidates,              # TC-010
    check_mro,                    # TC-011
    search_well_history,          # TC-012
    generate_draft_plan,          # TC-013
    generate_report,              # TC-014
    schedule_rigs,                # TC-015
    plot_production,              # TC-017
    query_wells,                  # TC-018
]


class WorkoverPlannerAgent(Agent):
    """Subclass of google.adk.agents.Agent wired with all 18 deterministic Geleki tools."""

    def execute_demo_turn_1_map(self, as_of: date = date(2026, 9, 23)) -> dict:
        res = render_well_map(field="Geleki", as_of=as_of)
        return {"turn": 1, "tool_trace": ["TC-016:render_well_map"], "result": asdict(res)}

    def execute_demo_turn_2_pushback(self, as_of: date = date(2026, 9, 23)) -> dict:
        r_abs = query_wells(field="Geleki", as_of=as_of, order_by="oil_rate_bopd", direction="ASC", limit=5)
        r_res = query_wells(field="Geleki", as_of=as_of, order_by="decline_residual_pct", direction="ASC", limit=5)
        return {
            "turn": 2,
            "tool_trace": ["TC-018:query_wells(oil_rate_bopd)", "TC-018:query_wells(decline_residual_pct)"],
            "literal_ranking": asdict(r_abs),
            "caveat": r_abs.value.caveat,
            "residual_ranking": asdict(r_res),
        }

    def execute_demo_turn_3_candidates(self, as_of: date = date(2026, 9, 23)) -> dict:
        trace = [
            "TC-001:fit_decline_curve",
            "TC-007:trigger_scan",
            "TC-002:chan_diagnostic",
            "TC-003:fillage_proxy",
            "TC-005:detect_mechanical_signature",
            "TC-004:check_offsets",
            "TC-006:predict_failure",
            "TC-008:route_intervention",
            "TC-009:estimate_uplift",
            "TC-010:rank_candidates",
        ]
        ranked = rank_candidates(field="Geleki", as_of=as_of)
        plan_129 = generate_draft_plan("GK-129", run_date=as_of)
        return {
            "turn": 3,
            "tool_trace": trace,
            "queues": asdict(ranked),
            "draft_plan_gk129": asdict(plan_129),
        }

    def execute_demo_turn_4_reports(self, as_of: date = date(2026, 9, 23)) -> dict:
        rep_d = generate_report(field="Geleki", period="DAILY", as_of=as_of)
        rep_w = generate_report(field="Geleki", period="WEEKLY", as_of=as_of)
        rep_m = generate_report(field="Geleki", period="MONTHLY", as_of=as_of)
        return {
            "turn": 4,
            "tool_trace": ["TC-014:generate_report(DAILY)", "TC-014:generate_report(WEEKLY)", "TC-014:generate_report(MONTHLY)"],
            "daily": asdict(rep_d),
            "weekly": asdict(rep_w),
            "monthly": asdict(rep_m),
        }


root_agent = WorkoverPlannerAgent(
    name="geleki_workover_intervention_agent",
    model="gemini-2.5-pro",
    description="Agentic Workover & Well Intervention Planner for ONGC Assam Asset (Geleki Field).",
    instruction=SYSTEM_PROMPT,
    tools=ADK_TOOLS,
)

from google.adk.apps import App

app = App(root_agent=root_agent, name="agent")
