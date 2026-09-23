"""
agent/adk_tools.py

JSON-serializable ADK FunctionTool wrappers around all 18 deterministic tool contracts (TC-001..TC-018).
Converts string dates ('YYYY-MM-DD') and enums cleanly so google.adk.agents.Agent can introspect
and invoke every tool without schema or serialization errors.
"""

from dataclasses import asdict, is_dataclass
from datetime import date
from enum import Enum
import json
from typing import Any

from tools import (
    OffsetVerdict,
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


def _to_json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, date):
        return obj.isoformat()
    if is_dataclass(obj):
        return _to_json_safe(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(x) for x in obj]
    return str(obj)


def _parse_date(d_str: str) -> date:
    try:
        return date.fromisoformat(d_str[:10])
    except Exception:
        return date(2026, 9, 23)


def adk_render_well_map(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
    size_by: str = "oil_rate_bopd",
    colour_by: str = "trigger_state",
    include_shut_in: bool = True,
) -> dict:
    """TC-016: Render interactive Vega-Lite map of 142 Geleki wells sized by rate and coloured by status/urgency."""
    res = render_well_map(
        field=field,
        as_of=_parse_date(as_of),
        size_by=size_by,  # type: ignore[arg-type]
        colour_by=colour_by,  # type: ignore[arg-type]
        include_shut_in=include_shut_in,
    )
    return _to_json_safe(res)


def adk_fit_decline_curve(
    well_id: str,
    as_of: str = "2026-09-23",
    lookback_months: int = 36,
) -> dict:
    """TC-001: Fit weighted Arps hyperbolic decline curve (q_i, b, D_i, residual_pct) for a well."""
    res = fit_decline_curve(well_id=well_id, as_of=_parse_date(as_of), lookback_months=lookback_months)
    return _to_json_safe(res)


def adk_chan_diagnostic(
    well_id: str,
    as_of: str = "2026-09-23",
    window_days: int = 90,
) -> dict:
    """TC-002: Run Chan (SPE-30775) log-log WOR and WOR' derivative slope diagnostic with paired-injector check."""
    res = chan_diagnostic(well_id=well_id, as_of=_parse_date(as_of), window_days=window_days)
    return _to_json_safe(res)


def adk_fillage_proxy(
    well_id: str,
    as_of: str = "2026-09-23",
    window_days: int = 30,
) -> dict:
    """TC-003: Compute rod-pump volumetric fillage efficiency and fluid-pound gap (SRP wells only)."""
    res = fillage_proxy(well_id=well_id, as_of=_parse_date(as_of), window_days=window_days)
    return _to_json_safe(res)


def adk_check_offsets(
    well_id: str,
    as_of: str = "2026-09-23",
    k: int = 6,
) -> dict:
    """TC-004: Compare subject well decline residual against k=6 same-zone offsets (WELL_SPECIFIC vs RESERVOIR_DECLINE)."""
    res = check_offsets(well_id=well_id, as_of=_parse_date(as_of), k=k)
    return _to_json_safe(res)


def adk_detect_mechanical_signature(
    well_id: str,
    as_of: str = "2026-09-23",
    window_days: int = 45,
) -> dict:
    """TC-005: Detect mechanical pre-failure signature (PUMP_WEAR, TUBING_LEAK, WAX, SCALE, ROD_PART) checking casing_vented."""
    res = detect_mechanical_signature(well_id=well_id, as_of=_parse_date(as_of), window_days=window_days)
    return _to_json_safe(res)


def adk_predict_failure(
    well_id: str,
    as_of: str = "2026-09-23",
) -> dict:
    """TC-006: Predict expected time-to-failure (ETTF days + 90% CI) using the CoxPH survival model vs Trigger B baseline."""
    res = predict_failure(well_id=well_id, as_of=_parse_date(as_of))
    return _to_json_safe(res)


def adk_trigger_scan(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
) -> dict:
    """TC-007: Run full nightly trigger scan (Triggers A, B, C, D) across active wells in the field."""
    res = trigger_scan(field=field, as_of=_parse_date(as_of))
    return _to_json_safe(res)


def adk_route_intervention(
    well_id: str,
    mechanism: str,
    offset_verdict: str = "WELL_SPECIFIC",
) -> dict:
    """TC-008: Route a diagnosed mechanism and offset verdict to the 28-job catalogue (enforces NO_JOB_JUSTIFIED and rig/rigless invariant)."""
    ov = OffsetVerdict.RESERVOIR_DECLINE if offset_verdict == "RESERVOIR_DECLINE" else OffsetVerdict.WELL_SPECIFIC
    res = route_intervention(well_id=well_id, mechanism=mechanism, offset_verdict=ov)
    return _to_json_safe(res)


def adk_estimate_uplift(
    well_id: str,
    job_code: str,
    as_of: str = "2026-09-23",
) -> dict:
    """TC-009: Estimate post-intervention oil rate uplift and 12-month deferred barrels avoided."""
    res = estimate_uplift(well_id=well_id, job_code=job_code, as_of=_parse_date(as_of))
    return _to_json_safe(res)


def adk_rank_candidates(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
    realisation_per_bbl: float = 6200.0,
) -> dict:
    """TC-010: Rank flagged intervention candidates into separate RIG and RIGLESS queues by net value per rig-day."""
    res = rank_candidates(field=field, as_of=_parse_date(as_of), realisation_per_bbl=realisation_per_bbl)
    return _to_json_safe(res)


def adk_check_mro(
    job_code: str,
    required_date: str = "2026-09-25",
    primary_base: str = "NAZIRA",
) -> dict:
    """TC-011: Check MRO material stock at Nazira and Sivasagar bases, transit days, and earliest feasible start date."""
    res = check_mro(job_code=job_code, required_date=_parse_date(required_date), primary_base=primary_base)
    return _to_json_safe(res)


def adk_search_well_history(
    well_id: str,
    query: str = "water shutoff history",
    top_k: int = 5,
) -> dict:
    """TC-012: Search scanned completion and workover PDF reports for a well with document date and GCS URI citations."""
    res = search_well_history(well_id=well_id, query=query, top_k=top_k)
    return _to_json_safe(res)


def adk_generate_draft_plan(
    well_id: str,
    run_date: str = "2026-09-23",
) -> dict:
    """TC-013: Assemble structured draft intervention plan (status always AWAITING REVIEW) with numeric provenance."""
    res = generate_draft_plan(well_id=well_id, run_date=_parse_date(run_date))
    return _to_json_safe(res)


def adk_generate_report(
    field: str = "Geleki",
    period: str = "WEEKLY",
    as_of: str = "2026-09-23",
) -> dict:
    """TC-014: Generate DAILY, WEEKLY, or MONTHLY executive workover report from well_run (includes Where the system was wrong)."""
    res = generate_report(field=field, period=period, as_of=_parse_date(as_of))  # type: ignore[arg-type]
    return _to_json_safe(res)


def adk_schedule_rigs(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
    horizon_days: int = 30,
) -> dict:
    """TC-015: Optimize workover rig schedule across Assam rig fleet while routing rigless jobs to surface crews."""
    res = schedule_rigs(field=field, as_of=_parse_date(as_of), horizon_days=horizon_days)
    return _to_json_safe(res)


def adk_plot_production(
    well_id: str,
    months: int = 36,
    overlay_decline_fit: bool = True,
    overlay_interventions: bool = True,
) -> dict:
    """TC-017: Plot multi-year daily oil, water, liquid, and water-cut series (preserving NULL gaps on shut-in days)."""
    res = plot_production(
        well_id=well_id,
        months=months,
        overlay_decline_fit=overlay_decline_fit,
        overlay_interventions=overlay_interventions,
    )
    return _to_json_safe(res)


def adk_query_wells(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
    order_by: str = "decline_residual_pct",
    direction: str = "ASC",
    limit: int = 5,
) -> dict:
    """TC-018: Query and rank active wells by oil_rate_bopd (with mandatory push-back caveat) or decline_residual_pct."""
    res = query_wells(
        field=field,
        as_of=_parse_date(as_of),
        order_by=order_by,  # type: ignore[arg-type]
        direction=direction,  # type: ignore[arg-type]
        limit=limit,
    )
    return _to_json_safe(res)


ADK_TOOLS = [
    adk_render_well_map,
    adk_fit_decline_curve,
    adk_chan_diagnostic,
    adk_fillage_proxy,
    adk_check_offsets,
    adk_detect_mechanical_signature,
    adk_predict_failure,
    adk_trigger_scan,
    adk_route_intervention,
    adk_estimate_uplift,
    adk_rank_candidates,
    adk_check_mro,
    adk_search_well_history,
    adk_generate_draft_plan,
    adk_generate_report,
    adk_schedule_rigs,
    adk_plot_production,
    adk_query_wells,
]
