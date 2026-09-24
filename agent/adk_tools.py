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


from google.adk.tools.tool_context import ToolContext
from agent.render.a2ui_surfaces import queue_a2ui_surface


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
    focus_well_id: str = "",
    cluster: str = "",
    radius_deg: float = 0.018,
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-016: Render interactive A2UI v0.9 satellite GIS + VegaChart map of Geleki wells.
    Supports full-field view or zooming into a specific well (`focus_well_id`, e.g. 'GK-141', 'GK-129')
    or fault-block cluster (`cluster`, e.g. 'NE', 'CENTRAL', 'SW', 'URGENT').
    """
    res = render_well_map(
        field=field,
        as_of=_parse_date(as_of),
        size_by=size_by,  # type: ignore[arg-type]
        colour_by=colour_by,  # type: ignore[arg-type]
        include_shut_in=include_shut_in,
    )
    queue_a2ui_surface(
        "map",
        field=field,
        focus_well_id=focus_well_id,
        cluster=cluster,
        radius_deg=radius_deg,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        # Remove raw vega_lite_spec from LLM text context so the model does not echo JSON
        out["value"].pop("vega_lite_spec", None)
        out["value"]["a2ui_surface_attached"] = True
        out["value"]["focus_well_id"] = focus_well_id.strip().upper() if focus_well_id else ""
        out["value"]["cluster"] = cluster.strip().upper() if cluster else ""
        out["value"]["ui_instruction"] = (
            "The interactive A2UI v0.9 spatial map card (with satellite crop zoom and mouse-wheel pan/zoom) "
            "is automatically attached below your prose reply. Confirm in one sentence that the interactive map "
            "is rendered below and summarize the visible wells. "
            "NEVER write bracketed placeholder text like [The user is presented with...]."
        )
    return out


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
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-002: Run Chan (SPE-30775) log-log WOR and WOR' derivative slope diagnostic with paired-injector check and A2UI plot."""
    res = chan_diagnostic(well_id=well_id, as_of=_parse_date(as_of), window_days=window_days)
    queue_a2ui_surface(
        "chan",
        well_id=well_id,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        out["value"]["a2ui_surface_attached"] = True
    return out


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
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-010: Rank flagged intervention candidates into separate RIG and RIGLESS queues by net value per rig-day and attach A2UI priority bar chart."""
    res = rank_candidates(field=field, as_of=_parse_date(as_of), realisation_per_bbl=realisation_per_bbl)
    queue_a2ui_surface(
        "ranking",
        field=field,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        out["value"]["a2ui_surface_attached"] = True
    return out


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
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-014: Generate DAILY, WEEKLY, or MONTHLY executive workover report from well_run (includes Where the system was wrong)."""
    res = generate_report(field=field, period=period, as_of=_parse_date(as_of))  # type: ignore[arg-type]
    queue_a2ui_surface(
        "report",
        field=field,
        period=period,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        out["value"]["a2ui_surface_attached"] = True
    return out


def adk_schedule_rigs(
    field: str = "Geleki",
    as_of: str = "2026-09-23",
    horizon_days: int = 30,
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-015: Optimize workover rig schedule across Assam rig fleet while routing rigless jobs to surface crews."""
    res = schedule_rigs(field=field, as_of=_parse_date(as_of), horizon_days=horizon_days)
    queue_a2ui_surface(
        "report",
        field=field,
        period="WEEKLY",
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        out["value"]["a2ui_surface_attached"] = True
    return out


def adk_plot_production(
    well_id: str,
    months: int = 36,
    overlay_decline_fit: bool = True,
    overlay_interventions: bool = True,
    tool_context: ToolContext | None = None,
) -> dict:
    """TC-017: Plot multi-year daily oil, water, liquid, and water-cut series as an interactive A2UI v0.9 dual-panel chart."""
    res = plot_production(
        well_id=well_id,
        months=months,
        overlay_decline_fit=overlay_decline_fit,
        overlay_interventions=overlay_interventions,
    )
    queue_a2ui_surface(
        "production",
        well_id=well_id,
        months=months,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    out = _to_json_safe(res)
    if isinstance(out.get("value"), dict):
        out["value"]["a2ui_surface_attached"] = True
        out["value"]["ui_instruction"] = (
            "The interactive A2UI v0.9 dual-panel production and water-cut chart is automatically attached below your prose reply. "
            "Confirm in one sentence that the interactive chart is displayed below and summarize the key trends and failed 2019 WSO intervention. "
            "NEVER write bracketed stage directions like [A line chart is displayed...]."
        )
    return out


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


def adk_open_google_maps(
    field: str = "Geleki",
    well_id: str = "",
    cluster: str = "",
    tool_context: ToolContext | None = None,
) -> dict:
    """Open live Google Maps Satellite 3D view for the Geleki field, a specific wellhead (`well_id`, e.g. 'GK-129', 'GK-055', 'GK-141'), or fault-block cluster.
    Use this tool whenever a user asks to see/open Google Maps, view live satellite imagery, navigate to a well on Google Maps, or switch to Google Maps.
    """
    queue_a2ui_surface(
        "gmaps",
        field=field,
        well_id=well_id,
        cluster=cluster,
        state_dict=tool_context.state if tool_context is not None else None,
    )
    from tools.render_well_map import render_well_map

    res = render_well_map(field=field)
    wm = res.value
    target_name = f"{field} Field (Assam)"
    lat, lon, zoom = 26.9634, 94.8105, 14
    fw_upper = (well_id or "").strip().upper()
    well_meta: dict[str, Any] = {}
    if fw_upper:
        for p in wm.points:
            if p.well_id.upper() == fw_upper:
                lat, lon, zoom = float(p.lat), float(p.lon), 17
                target_name = f"Well {p.well_id}"
                well_meta = {
                    "well_id": p.well_id,
                    "status": p.colour_key,
                    "oil_rate_bopd": p.size_value or 0.0,
                    "zone": p.tooltip.get("current_zone"),
                    "lift_type": p.tooltip.get("lift_type"),
                    "water_cut_pct": p.tooltip.get("water_cut_pct"),
                }
                break

    sat_url = f"https://www.google.com/maps/@{lat:.5f},{lon:.5f},{zoom}z/data=!3m1!1e3"
    pin_url = f"https://www.google.com/maps/search/?api=1&query={lat:.5f},{lon:.5f}"
    return {
        "status": "SUCCESS",
        "target": target_name,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "zoom_level": zoom,
        "google_maps_satellite_url": sat_url,
        "google_maps_pin_url": pin_url,
        "well_metadata": well_meta,
        "a2ui_surface_attached": True,
        "ui_instruction": (
            f"An interactive Google Maps launch card has been attached below. "
            f"Confirm in one sentence that the live Google Maps Satellite card is attached, summarize the coordinates ({lat:.5f}°N, {lon:.5f}°E), "
            f"and invite the user to click the launch link to explore in live 3D satellite view."
        ),
    }


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
    adk_open_google_maps,
]
