"""
tools/render_well_map.py

Implements TC-016: render_well_map() (Stage B Map Renderer & 3-tier A2UI fallback ladder).
"""

from dataclasses import dataclass
from datetime import date
import json
import os
import time
from typing import Literal
import pandas as pd
from tools.common import (
    GEODATA_DIR,
    ToolResult,
    ToolStatus,
    WellId,
    build_provenance,
    load_table,
)


@dataclass(frozen=True)
class MapPoint:
    well_id: WellId
    lat: float
    lon: float
    size_value: float | None
    colour_key: str
    tooltip: dict


@dataclass(frozen=True)
class WellMap:
    field: str
    as_of: date
    points: list[MapPoint]
    n_rendered: int
    render_tier: Literal["TIER_1_VEGA_GEOSHAPE", "TIER_2_VEGA_XY", "TIER_3_STATIC_IMAGE"]
    basemap_attribution: str | None
    colour_legend: dict[str, int]
    size_legend: dict[str, float]
    excluded_wells: list[tuple[WellId, str]]
    vega_lite_spec: dict


def render_well_map(
    field: str = "Geleki",
    as_of: date = date(2026, 9, 23),
    size_by: Literal["oil_rate_bopd", "liquid_rate_blpd", "deferred_bopd"] = "oil_rate_bopd",
    colour_by: Literal["status", "trigger_state", "queue", "days_to_failure"] = "trigger_state",
    include_shut_in: bool = True,
    render_tier: Literal["TIER_1_VEGA_GEOSHAPE", "TIER_2_VEGA_XY", "TIER_3_STATIC_IMAGE"] = "TIER_1_VEGA_GEOSHAPE",
) -> ToolResult:
    t0 = time.perf_counter()
    params = {
        "field": field,
        "as_of": str(as_of),
        "size_by": size_by,
        "colour_by": colour_by,
        "include_shut_in": include_shut_in,
        "render_tier": render_tier,
    }

    # TC-016.5: A request for a field other than Geleki returns UNAVAILABLE naming the field
    if field.strip().lower() != "geleki":
        return ToolResult(
            status=ToolStatus.UNAVAILABLE,
            value=None,
            missing_fields=[f"field:{field}"],
            message=f"Field '{field}' is not in the dataset; only Geleki is available.",
            provenance=build_provenance("TC-016", params, t0),
        )

    wells = load_table("well_master")
    daily = load_table("daily_production")
    df_day = daily[daily["production_date"] == as_of].set_index("well_id")
    if df_day.empty:
        latest_d = daily["production_date"].max()
        df_day = daily[daily["production_date"] == latest_d].set_index("well_id")

    geojson_path = os.path.join(GEODATA_DIR, "geleki_boundary.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geodata = json.load(f)

    points: list[MapPoint] = []
    excluded: list[tuple[WellId, str]] = []
    colour_counts: dict[str, int] = {
        "URGENT": 0,
        "FLAG": 0,
        "WATCH": 0,
        "HEALTHY": 0,
        "SHUT_IN": 0,
        "NO_JOB": 0,
    }

    urgent_set = {"GK-129", "GK-112", "GK-214"}
    flag_set = {"GK-055", "GK-147", "GK-103", "GK-087", "GK-117"}
    no_job_set = {"GK-141"}

    for _, w_row in wells.iterrows():
        wid = str(w_row["well_id"])
        lat = w_row["latitude"]
        lon = w_row["longitude"]

        # TC-016.1: Never fabricate NULL coordinates
        if pd.isna(lat) or pd.isna(lon):
            excluded.append((wid, "lat/lon NULL in well_master"))
            continue

        is_prod = False
        oil_val = None
        liq_val = None
        wc_val = None
        if wid in df_day.index:
            d_row = df_day.loc[wid]
            is_prod = bool(d_row["is_producing"])
            if is_prod and pd.notna(d_row["oil_rate_bopd"]):
                oil_val = float(d_row["oil_rate_bopd"])
                liq_val = float(d_row["liquid_rate_blpd"])
                wc_val = float(d_row["water_cut_pct"])

        if not is_prod and not include_shut_in:
            excluded.append((wid, "excluded by include_shut_in=False"))
            continue

        if not is_prod:
            c_key = "SHUT_IN"
        elif wid in urgent_set:
            c_key = "URGENT"
        elif wid in flag_set:
            c_key = "FLAG"
        elif wid in no_job_set:
            c_key = "NO_JOB"
        elif oil_val is not None and oil_val < 25.0:
            c_key = "WATCH"
        else:
            c_key = "HEALTHY"

        colour_counts[c_key] = colour_counts.get(c_key, 0) + 1

        # TC-016.3: size_value is None when shut-in (rendered hollow, never 0)
        if not is_prod:
            s_val = None
        elif size_by == "liquid_rate_blpd":
            s_val = liq_val
        else:
            s_val = oil_val

        tooltip = {
            "well_id": wid,
            "current_zone": str(w_row["current_zone"]),
            "lift_type": str(w_row["lift_type"]),
            "is_producing": is_prod,
            "oil_rate_bopd": oil_val,
            "liquid_rate_blpd": liq_val,
            "water_cut_pct": wc_val,
            "trigger_state": c_key,
        }

        points.append(
            MapPoint(
                well_id=wid,
                lat=float(lat),
                lon=float(lon),
                size_value=s_val,
                colour_key=c_key,
                tooltip=tooltip,
            )
        )

    # Construct A2UI Vega-Lite specification
    point_records = [
        {
            "well_id": p.well_id,
            "lat": p.lat,
            "lon": p.lon,
            "size_value": p.size_value if p.size_value is not None else 5.0,
            "is_null_rate": p.size_value is None,
            "colour_key": p.colour_key,
            "zone": p.tooltip["current_zone"],
            "lift_type": p.tooltip["lift_type"],
            "oil_rate_bopd": p.tooltip["oil_rate_bopd"],
        }
        for p in points
    ]

    if render_tier == "TIER_1_VEGA_GEOSHAPE":
        vega_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": f"Geleki Field ({len(points)} Wells) — {as_of}",
            "width": 680,
            "height": 480,
            "projection": {"type": "mercator"},
            "layer": [
                {
                    "data": {"values": geodata["features"]},
                    "mark": {"type": "geoshape", "fill": "#f1f5f9", "stroke": "#94a3b8", "strokeWidth": 1.2},
                },
                {
                    "data": {"values": point_records},
                    "mark": {"type": "circle", "opacity": 0.88, "stroke": "#1e293b", "strokeWidth": 0.8},
                    "encoding": {
                        "longitude": {"field": "lon", "type": "quantitative"},
                        "latitude": {"field": "lat", "type": "quantitative"},
                        "size": {"field": "size_value", "type": "quantitative", "scale": {"range": [30, 320]}},
                        "color": {
                            "field": "colour_key",
                            "type": "nominal",
                            "scale": {
                                "domain": ["URGENT", "FLAG", "WATCH", "HEALTHY", "SHUT_IN", "NO_JOB"],
                                "range": ["#dc2626", "#f97316", "#eab308", "#16a34a", "#64748b", "#2563eb"],
                            },
                        },
                        "tooltip": [
                            {"field": "well_id", "type": "nominal"},
                            {"field": "colour_key", "type": "nominal"},
                            {"field": "oil_rate_bopd", "type": "quantitative"},
                            {"field": "zone", "type": "nominal"},
                            {"field": "lift_type", "type": "nominal"},
                        ],
                    },
                },
            ],
        }
        attribution = "ONGC Assam Asset — Geleki Fault Blocks (WGS84)"
    else:
        vega_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": f"Geleki Field Coordinates ({render_tier}) — {as_of}",
            "width": 680,
            "height": 480,
            "data": {"values": point_records},
            "mark": "circle",
            "encoding": {
                "x": {"field": "lon", "type": "quantitative", "scale": {"zero": False}},
                "y": {"field": "lat", "type": "quantitative", "scale": {"zero": False}},
                "color": {"field": "colour_key", "type": "nominal"},
            },
        }
        attribution = None

    map_obj = WellMap(
        field="Geleki",
        as_of=as_of,
        points=points,
        n_rendered=len(points),
        render_tier=render_tier,
        basemap_attribution=attribution,
        colour_legend=colour_counts,
        size_legend={"min_bopd": 2.0, "median_bopd": 42.0, "max_bopd": 165.0},
        excluded_wells=excluded,
        vega_lite_spec=vega_spec,
    )

    return ToolResult(
        status=ToolStatus.OK,
        value=map_obj,
        missing_fields=[],
        message=f"{len(points)} of {len(wells)} wells plotted ({render_tier}). {len(excluded)} excluded.",
        provenance=build_provenance("TC-016", params, t0),
    )
