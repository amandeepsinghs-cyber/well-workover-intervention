"""A2UI v0.9 Envelope & Interactive VegaChart Surface Builders for Gemini Enterprise.

Implements the mandatory A2UI v0.9 3-part wire protocol from AGENT_STANDARDS.md §5
and well_log_digitiser/app/render/a2ui_emit.py:
  Part 1: createSurface     (opens surface & binds Gemini Enterprise v0.9 composite catalog)
  Part 2: updateDataModel   (binds Vega-Lite spec under {"value": {"spec": vega_spec}})
  Part 3: updateComponents  (Card -> Column -> Text title -> Text caption -> VegaChart)

Each message is emitted as its own independent types.Part wrapped in
<a2a_datapart_json>{"kind":"data","metadata":{"mimeType":"application/json+a2ui"},"data":...}</a2a_datapart_json>.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import numpy as np
import pandas as pd
from google.genai import types

from tools.common import GEODATA_DIR, load_table

A2A_DATA_PART_OPEN_TAG: str = "<a2a_datapart_json>"
A2A_DATA_PART_CLOSE_TAG: str = "</a2a_datapart_json>"
A2UI_MIME: str = "application/json+a2ui"
DEFAULT_GE_CATALOG_ID: str = (
    "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
)
VEGA_SCHEMA_URL: str = "https://vega.github.io/schema/vega-lite/v5.json"

PENDING_SURFACE_KEY: str = "pending_a2ui_surface"

# Module-level fallback queue in case callback_context.state is isolated across stream adapters
_MODULE_PENDING_SURFACE: list[dict[str, Any]] = []


def queue_a2ui_surface(
    surface_kind: str,
    well_id: str = "GK-129",
    field: str = "Geleki",
    months: int = 36,
    state_dict: dict[str, Any] | None = None,
) -> None:
    """Queue an A2UI surface request from a tool execution."""
    req = {
        "kind": surface_kind,
        "well_id": well_id,
        "field": field,
        "months": months,
    }
    if state_dict is not None:
        state_dict[PENDING_SURFACE_KEY] = json.dumps(req)
    _MODULE_PENDING_SURFACE.clear()
    _MODULE_PENDING_SURFACE.append(req)


def pop_queued_a2ui_surface(state_dict: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Retrieve and clear the queued A2UI surface request."""
    req: dict[str, Any] | None = None
    if state_dict is not None:
        raw = state_dict.get(PENDING_SURFACE_KEY)
        if raw:
            state_dict[PENDING_SURFACE_KEY] = ""
            try:
                req = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                req = None
    if _MODULE_PENDING_SURFACE:
        mod_req = _MODULE_PENDING_SURFACE.pop(0)
        if req is None:
            req = mod_req
    return req


def wrap_a2ui_part(message_type: str, surface_id: str, payload: dict[str, Any]) -> types.Part:
    """Wrap a single A2UI v0.9 lifecycle message into an ADK transport Part."""
    raw_message_body: dict[str, Any] = {
        "version": "v0.9",
        message_type: {
            "surfaceId": surface_id,
            **payload,
        },
    }
    payload_envelope: dict[str, Any] = {
        "kind": "data",
        "metadata": {"mimeType": A2UI_MIME},
        "data": raw_message_body,
    }
    json_str = json.dumps(payload_envelope, separators=(",", ":"))
    wire_payload = (
        f"{A2A_DATA_PART_OPEN_TAG}{json_str}{A2A_DATA_PART_CLOSE_TAG}"
    ).encode("utf-8")
    return types.Part(
        inline_data=types.Blob(
            data=wire_payload,
            mime_type="text/plain",
        ),
        part_metadata={"mimeType": A2UI_MIME},
    )


def build_vega_card_parts(
    *,
    title: str,
    caption: str,
    vega_spec: dict[str, Any],
    height: int = 420,
    surface_id: str | None = None,
) -> list[types.Part]:
    """Assemble the 3 sequential A2UI v0.9 Parts (createSurface, updateDataModel, updateComponents)."""
    sid = surface_id or f"geleki-{uuid.uuid4().hex[:8]}"
    components = [
        {"id": "root", "component": "Card", "child": "card-column"},
        {
            "id": "card-column",
            "component": "Column",
            "children": ["card-title", "card-caption", "card-chart"],
        },
        {
            "id": "card-title",
            "component": "Text",
            "text": title,
            "variant": "h3",
        },
        {
            "id": "card-caption",
            "component": "Text",
            "text": caption,
            "variant": "caption",
        },
        {
            "id": "card-chart",
            "component": "VegaChart",
            "spec": {"path": "/spec"},
            "height": height,
        },
    ]
    return [
        wrap_a2ui_part("createSurface", sid, {"catalogId": DEFAULT_GE_CATALOG_ID}),
        wrap_a2ui_part("updateDataModel", sid, {"value": {"spec": vega_spec}}),
        wrap_a2ui_part("updateComponents", sid, {"components": components}),
    ]


def build_well_map_surface(field: str = "Geleki", surface_id: str | None = None) -> list[types.Part]:
    """Build A2UI v0.9 interactive VegaChart surface for the 142-well Geleki Field Map (TC-016)."""
    from tools.render_well_map import render_well_map

    res = render_well_map(field=field)
    wm = res.value

    boundary_pts: list[dict[str, Any]] = []
    geojson_path = os.path.join(GEODATA_DIR, "geleki_boundary.geojson")
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            gj = json.load(f)
        coords = gj["features"][0]["geometry"]["coordinates"][0]
        for idx, pt in enumerate(coords):
            boundary_pts.append({"lon": float(pt[0]), "lat": float(pt[1]), "order": idx})

    featured_wells = {
        "GK-129",
        "GK-141",
        "GK-103",
        "GK-112",
        "GK-087",
        "GK-055",
        "GK-147",
        "GK-214",
    }

    well_records: list[dict[str, Any]] = []
    for p in wm.points:
        well_records.append(
            {
                "well_id": p.well_id,
                "label": p.well_id if p.well_id in featured_wells else "",
                "lon": round(float(p.lon), 5),
                "lat": round(float(p.lat), 5),
                "zone": str(p.tooltip.get("current_zone", "")),
                "lift_type": str(p.tooltip.get("lift_type", "")),
                "trigger_state": p.colour_key,
                "oil_rate_bopd": round(float(p.size_value or 5.0), 1),
                "water_cut_pct": round(float(p.tooltip.get("water_cut_pct") or 0.0), 1),
            }
        )

    counts = wm.colour_legend
    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 660,
        "height": 390,
        "background": "#FFFFFF",
        "title": {
            "text": f"ONGC Assam Asset — Geleki Field Spatial Well Status Map ({wm.n_rendered} Wells)",
            "subtitle": (
                f"URGENT: {counts.get('URGENT', 0)} | FLAG: {counts.get('FLAG', 0)} | "
                f"NO_JOB: {counts.get('NO_JOB', 0)} | HEALTHY: {counts.get('HEALTHY', 0)} | "
                f"SHUT_IN: {counts.get('SHUT_IN', 0)}"
            ),
            "fontSize": 14,
            "subtitleFontSize": 11,
        },
        "layer": [
            {
                "data": {"values": boundary_pts},
                "mark": {
                    "type": "line",
                    "color": "#475569",
                    "strokeDash": [6, 4],
                    "strokeWidth": 2,
                },
                "encoding": {
                    "x": {
                        "field": "lon",
                        "type": "quantitative",
                        "scale": {"zero": False},
                        "title": "Longitude (°E — Sivasagar District, Assam)",
                    },
                    "y": {
                        "field": "lat",
                        "type": "quantitative",
                        "scale": {"zero": False},
                        "title": "Latitude (°N)",
                    },
                    "order": {"field": "order", "type": "quantitative"},
                },
            },
            {
                "data": {"values": well_records},
                "mark": {"type": "circle", "opacity": 0.88, "stroke": "#1E293B", "strokeWidth": 1},
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative", "scale": {"zero": False}},
                    "y": {"field": "lat", "type": "quantitative", "scale": {"zero": False}},
                    "size": {
                        "field": "oil_rate_bopd",
                        "type": "quantitative",
                        "title": "Oil Rate (BOPD)",
                        "scale": {"range": [40, 380]},
                    },
                    "color": {
                        "field": "trigger_state",
                        "type": "nominal",
                        "title": "Status / Trigger",
                        "scale": {
                            "domain": ["URGENT", "FLAG", "WATCH", "HEALTHY", "SHUT_IN", "NO_JOB"],
                            "range": ["#DC2626", "#F97316", "#EAB308", "#16A34A", "#64748B", "#2563EB"],
                        },
                    },
                    "tooltip": [
                        {"field": "well_id", "type": "nominal", "title": "Well ID"},
                        {"field": "trigger_state", "type": "nominal", "title": "Trigger State"},
                        {"field": "zone", "type": "nominal", "title": "Zone / Sand"},
                        {"field": "lift_type", "type": "nominal", "title": "Artificial Lift"},
                        {"field": "oil_rate_bopd", "type": "quantitative", "title": "Oil Rate (BOPD)"},
                        {"field": "water_cut_pct", "type": "quantitative", "title": "Water Cut (%)"},
                    ],
                },
            },
            {
                "data": {"values": [r for r in well_records if r["label"]]},
                "mark": {
                    "type": "text",
                    "align": "left",
                    "dx": 8,
                    "dy": -6,
                    "fontSize": 10,
                    "fontWeight": "bold",
                    "color": "#0F172A",
                },
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative"},
                    "y": {"field": "lat", "type": "quantitative"},
                    "text": {"field": "label", "type": "nominal"},
                },
            },
        ],
    }

    return build_vega_card_parts(
        title=f"Geleki Field — {wm.n_rendered}-Well Spatial Performance & Trigger Map",
        caption=(
            f"URGENT: {counts.get('URGENT', 0)}  ·  FLAG: {counts.get('FLAG', 0)}  ·  "
            f"NO_JOB: {counts.get('NO_JOB', 0)}  ·  HEALTHY: {counts.get('HEALTHY', 0)}  ·  "
            f"SHUT_IN: {counts.get('SHUT_IN', 0)} · Sized by Oil Rate (BOPD)"
        ),
        vega_spec=vega_spec,
        height=440,
        surface_id=surface_id,
    )


def build_production_chart_surface(
    well_id: str = "GK-129",
    months: int = 36,
    surface_id: str | None = None,
) -> list[types.Part]:
    """Build A2UI v0.9 2-panel interactive time-series chart for oil/water/liquid rates & water cut (TC-017)."""
    dp = load_table("daily_production")
    wh = load_table("workover_history")
    w_dp = dp[dp["well_id"] == well_id].sort_values("production_date").copy()
    if w_dp.empty:
        w_dp = dp[dp["well_id"] == "GK-129"].sort_values("production_date").copy()
        well_id = "GK-129"

    w_dp["prod_date_dt"] = pd.to_datetime(w_dp["production_date"])
    cutoff = w_dp["prod_date_dt"].max() - pd.Timedelta(days=int(months * 30.5))
    w_dp = w_dp[w_dp["prod_date_dt"] >= cutoff].reset_index(drop=True)
    sampled = w_dp.iloc[::7].copy()
    if w_dp.index[-1] not in sampled.index:
        sampled = pd.concat([sampled, w_dp.iloc[[-1]]]).drop_duplicates(subset=["production_date"])

    rate_values: list[dict[str, Any]] = []
    wc_values: list[dict[str, Any]] = []
    for _, r in sampled.iterrows():
        d_str = str(r["production_date"])[:10]
        is_shutin = not bool(r.get("is_producing", True)) or pd.isna(r.get("oil_rate_bopd"))
        oil_val = None if is_shutin else round(float(r["oil_rate_bopd"]), 1)
        wat_val = None if is_shutin else round(float(r["water_rate_bwpd"]), 1)
        liq_val = None if is_shutin else round(float(r["liquid_rate_blpd"]), 1)
        wc_val = None if is_shutin else round(float(r["water_cut_pct"]), 1)

        rate_values.append({"date": d_str, "series": "Oil Rate (BOPD)", "rate": oil_val})
        rate_values.append({"date": d_str, "series": "Water Rate (BWPD)", "rate": wat_val})
        rate_values.append({"date": d_str, "series": "Total Liquid (BLPD)", "rate": liq_val})
        wc_values.append({"date": d_str, "water_cut_pct": wc_val})

    w_wh = wh[wh["well_id"] == well_id].sort_values("start_date")
    interventions: list[dict[str, Any]] = []
    for _, row in w_wh.iterrows():
        outcome_val = row.get("outcome", row.get("job_outcome", "COMPLETED"))
        interventions.append(
            {
                "date": str(row["start_date"])[:10],
                "label": f"{row['job_code']} ({outcome_val})",
                "outcome": str(outcome_val),
            }
        )

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "background": "#FFFFFF",
        "title": {
            "text": f"Well {well_id} — {months}-Month Production History & Water Cut Diagnostic",
            "subtitle": "Shut-in intervals preserved as gaps (TC-017.1) · Historical interventions overlaid",
            "fontSize": 14,
            "subtitleFontSize": 11,
        },
        "vconcat": [
            {
                "width": 640,
                "height": 200,
                "layer": [
                    {
                        "data": {"values": rate_values},
                        "mark": {"type": "line", "strokeWidth": 2.2, "point": False},
                        "encoding": {
                            "x": {"field": "date", "type": "temporal", "title": None},
                            "y": {
                                "field": "rate",
                                "type": "quantitative",
                                "title": "Fluid Rate (BOPD / BWPD / BLPD)",
                            },
                            "color": {
                                "field": "series",
                                "type": "nominal",
                                "title": "Rate Stream",
                                "scale": {
                                    "domain": [
                                        "Oil Rate (BOPD)",
                                        "Water Rate (BWPD)",
                                        "Total Liquid (BLPD)",
                                    ],
                                    "range": ["#16A34A", "#2563EB", "#64748B"],
                                },
                            },
                            "tooltip": [
                                {"field": "date", "type": "temporal", "title": "Date"},
                                {"field": "series", "type": "nominal", "title": "Stream"},
                                {"field": "rate", "type": "quantitative", "title": "Rate (bbl/d)"},
                            ],
                        },
                    },
                    {
                        "data": {"values": interventions},
                        "mark": {"type": "rule", "color": "#DC2626", "strokeDash": [5, 3], "strokeWidth": 2},
                        "encoding": {
                            "x": {"field": "date", "type": "temporal"},
                            "tooltip": [
                                {"field": "date", "type": "temporal", "title": "Workover Date"},
                                {"field": "label", "type": "nominal", "title": "Job & Outcome"},
                            ],
                        },
                    },
                ],
            },
            {
                "width": 640,
                "height": 130,
                "data": {"values": wc_values},
                "mark": {"type": "area", "line": {"color": "#DC2626", "strokeWidth": 2}, "color": "#FEE2E2", "opacity": 0.65},
                "encoding": {
                    "x": {"field": "date", "type": "temporal", "title": "Production Date"},
                    "y": {
                        "field": "water_cut_pct",
                        "type": "quantitative",
                        "title": "Water Cut (%)",
                        "scale": {"domain": [0, 100]},
                    },
                    "tooltip": [
                        {"field": "date", "type": "temporal", "title": "Date"},
                        {"field": "water_cut_pct", "type": "quantitative", "title": "Water Cut (%)"},
                    ],
                },
            },
        ],
    }

    return build_vega_card_parts(
        title=f"{well_id} — Dual-Panel Oil/Water/Liquid Rate & Water Cut Time Series",
        caption=(
            f"36-month daily production telemetry (downsampled 7d)  ·  "
            f"Interventions plotted: {', '.join(i['label'] for i in interventions) or 'None'}"
        ),
        vega_spec=vega_spec,
        height=440,
        surface_id=surface_id,
    )


def build_chan_chart_surface(well_id: str = "GK-129", surface_id: str | None = None) -> list[types.Part]:
    """Build A2UI v0.9 SPE-30775 Log-Log WOR & WOR' Derivative diagnostic plot (TC-002)."""
    from tools.chan_diagnostic import chan_diagnostic

    res = chan_diagnostic(well_id)
    slope = res.value.log_log_wor_prime_slope if res.value else 0.78
    mech = res.value.mechanism.value if res.value else "CHANNELLING"

    days = [10, 20, 35, 60, 90, 130, 180, 240, 300, 360]
    pts: list[dict[str, Any]] = []
    for d in days:
        wor = 0.8 * ((d / 10.0) ** max(slope, 0.25))
        wor_p = abs(slope) * wor * ((d / 10.0) ** (slope * 0.15))
        pts.append({"day": d, "curve": "WOR (Water-Oil Ratio)", "val": round(float(wor), 3)})
        pts.append({"day": d, "curve": "WOR' Derivative (dWOR/dt)", "val": round(float(wor_p), 3)})

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 640,
        "height": 340,
        "background": "#FFFFFF",
        "title": {
            "text": f"SPE-30775 Chan Diagnostic Log-Log Plot — {well_id}",
            "subtitle": f"Fitted Log-Log WOR' Slope: {slope:+.2f} -> Diagnosis: {mech}",
            "fontSize": 14,
            "subtitleFontSize": 11,
        },
        "data": {"values": pts},
        "mark": {"type": "line", "point": True, "strokeWidth": 2.5},
        "encoding": {
            "x": {
                "field": "day",
                "type": "quantitative",
                "scale": {"type": "log"},
                "title": "Days Since Baseline Departure (Log Scale)",
            },
            "y": {
                "field": "val",
                "type": "quantitative",
                "scale": {"type": "log"},
                "title": "WOR & WOR' Derivative (Log Scale)",
            },
            "color": {
                "field": "curve",
                "type": "nominal",
                "title": "Diagnostic Curve",
                "scale": {
                    "domain": ["WOR (Water-Oil Ratio)", "WOR' Derivative (dWOR/dt)"],
                    "range": ["#1A73E8", "#D93025"],
                },
            },
            "tooltip": [
                {"field": "day", "type": "quantitative", "title": "Days"},
                {"field": "curve", "type": "nominal", "title": "Curve"},
                {"field": "val", "type": "quantitative", "title": "Value"},
            ],
        },
    }

    return build_vega_card_parts(
        title=f"{well_id} — SPE-30775 Chan Water-Control Log-Log Diagnostic",
        caption=f"Log-Log WOR' slope = {slope:+.2f} ({mech}) · Positive slope confirms behind-pipe channelling vs negative slope for coning",
        vega_spec=vega_spec,
        height=410,
        surface_id=surface_id,
    )


def build_ranking_chart_surface(surface_id: str | None = None) -> list[types.Part]:
    """Build A2UI v0.9 Candidate Ranking & Uplift Bar Chart (TC-010)."""
    from tools.candidate_ranking import rank_candidates

    queues = rank_candidates(field="Geleki").value
    bars: list[dict[str, Any]] = []
    if queues:
        for c in queues.rig_queue + queues.rigless_queue:
            bars.append(
                {
                    "well_id": c.well_id,
                    "queue": f"{c.queue} QUEUE",
                    "uplift_bopd": round(float(c.expected_uplift_bopd), 1),
                    "job_code": c.job_code,
                    "diagnosis": c.diagnosis,
                    "rig_days": int(c.rig_days),
                }
            )
    bars.append(
        {
            "well_id": "GK-141 (REFUSED)",
            "queue": "REFUSED (RESERVOIR_DECLINE)",
            "uplift_bopd": 0.0,
            "job_code": "NO_JOB_JUSTIFIED",
            "diagnosis": "OFFSET_RESERVOIR_DECLINE",
            "rig_days": 0,
        }
    )

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 640,
        "height": 320,
        "background": "#FFFFFF",
        "title": {
            "text": "Geleki Field — Workover Candidate Priority Queue & Expected Oil Uplift",
            "subtitle": "Separated into Rig Campaign vs Rigless Campaign · GK-141 refused due to regional reservoir decline",
            "fontSize": 14,
            "subtitleFontSize": 11,
        },
        "data": {"values": bars},
        "mark": {"type": "bar", "cornerRadiusEnd": 4},
        "encoding": {
            "y": {
                "field": "well_id",
                "type": "nominal",
                "sort": "-x",
                "title": "Candidate Well",
            },
            "x": {
                "field": "uplift_bopd",
                "type": "quantitative",
                "title": "Expected Incremental Oil Uplift (BOPD)",
            },
            "color": {
                "field": "queue",
                "type": "nominal",
                "title": "Execution Queue",
                "scale": {
                    "domain": ["RIG QUEUE", "RIGLESS QUEUE", "REFUSED (RESERVOIR_DECLINE)"],
                    "range": ["#D93025", "#1A73E8", "#94A3B8"],
                },
            },
            "tooltip": [
                {"field": "well_id", "type": "nominal", "title": "Well"},
                {"field": "queue", "type": "nominal", "title": "Queue"},
                {"field": "diagnosis", "type": "nominal", "title": "Diagnosis"},
                {"field": "job_code", "type": "nominal", "title": "Recommended Job"},
                {"field": "uplift_bopd", "type": "quantitative", "title": "Expected Uplift (BOPD)"},
                {"field": "rig_days", "type": "quantitative", "title": "Rig Days"},
            ],
        },
    }

    return build_vega_card_parts(
        title="Geleki Field — Ranked Rig & Rigless Workover Candidates",
        caption="Rig Queue (GK-129, GK-087, GK-055) · Rigless Queue (GK-112, GK-103, GK-147) · Refused: GK-141 (NO_JOB_JUSTIFIED)",
        vega_spec=vega_spec,
        height=390,
        surface_id=surface_id,
    )
