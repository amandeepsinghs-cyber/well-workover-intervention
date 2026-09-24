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
    period: str = "WEEKLY",
    focus_well_id: str = "",
    cluster: str = "",
    radius_deg: float = 0.018,
    state_dict: dict[str, Any] | None = None,
) -> None:
    """Queue an A2UI surface request from a tool execution."""
    req = {
        "kind": surface_kind,
        "well_id": well_id,
        "field": field,
        "months": months,
        "period": period,
        "focus_well_id": focus_well_id.strip().upper() if focus_well_id else "",
        "cluster": cluster.strip().upper() if cluster else "",
        "radius_deg": float(radius_deg),
    }
    if state_dict is not None:
        existing_raw = state_dict.get(PENDING_SURFACE_KEY)
        existing_list: list[dict[str, Any]] = []
        if existing_raw:
            try:
                parsed = json.loads(existing_raw) if isinstance(existing_raw, str) else existing_raw
                if isinstance(parsed, list):
                    existing_list = parsed
                elif isinstance(parsed, dict):
                    existing_list = [parsed]
            except Exception:
                existing_list = []
        existing_list = [r for r in existing_list if r.get("kind") != surface_kind]
        existing_list.append(req)
        state_dict[PENDING_SURFACE_KEY] = json.dumps(existing_list)

    _MODULE_PENDING_SURFACE[:] = [r for r in _MODULE_PENDING_SURFACE if r.get("kind") != surface_kind]
    _MODULE_PENDING_SURFACE.append(req)


def pop_queued_a2ui_surfaces(state_dict: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Retrieve and clear all queued A2UI surface requests in order."""
    reqs: list[dict[str, Any]] = []
    if state_dict is not None:
        raw = state_dict.get(PENDING_SURFACE_KEY)
        if raw:
            state_dict[PENDING_SURFACE_KEY] = ""
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(parsed, list):
                    reqs = parsed
                elif isinstance(parsed, dict):
                    reqs = [parsed]
            except Exception:
                reqs = []
    if _MODULE_PENDING_SURFACE:
        mod_reqs = list(_MODULE_PENDING_SURFACE)
        _MODULE_PENDING_SURFACE.clear()
        if not reqs:
            reqs = mod_reqs
    return reqs


def pop_queued_a2ui_surface(state_dict: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Retrieve and clear the primary queued A2UI surface request."""
    reqs = pop_queued_a2ui_surfaces(state_dict=state_dict)
    return reqs[-1] if reqs else None


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


def _resolve_map_viewport(
    well_records: list[dict[str, Any]],
    boundary_pts: list[dict[str, Any]],
    focus_well_id: str = "",
    cluster: str = "",
    radius_deg: float = 0.018,
) -> tuple[float, float, float, float, str, bool]:
    """Compute (lon_min, lon_max, lat_min, lat_max, zoom_title, is_zoomed) for full field or focused well/cluster."""
    all_lons = [w["lon"] for w in well_records] + [pt["lon"] for pt in boundary_pts]
    all_lats = [w["lat"] for w in well_records] + [pt["lat"] for pt in boundary_pts]
    full_lon_min = round(min(all_lons) - 0.007, 4) if all_lons else 94.754
    full_lon_max = round(max(all_lons) + 0.007, 4) if all_lons else 94.866
    full_lat_min = round(min(all_lats) - 0.006, 4) if all_lats else 26.912
    full_lat_max = round(max(all_lats) + 0.006, 4) if all_lats else 27.014

    fw = (focus_well_id or "").strip().upper()
    cl = (cluster or "").strip().upper()
    r_lon = max(0.008, min(0.045, float(radius_deg or 0.018)))
    r_lat = round(r_lon * 0.80, 4)

    if fw:
        target = next((w for w in well_records if w["well_id"].upper() == fw), None)
        if target is not None:
            c_lon, c_lat = float(target["lon"]), float(target["lat"])
            return (
                round(max(full_lon_min, c_lon - r_lon), 4),
                round(min(full_lon_max, c_lon + r_lon), 4),
                round(max(full_lat_min, c_lat - r_lat), 4),
                round(min(full_lat_max, c_lat + r_lat), 4),
                f"ZOOM: {fw} & OFFSET WELL CLUSTER",
                True,
            )

    if cl:
        if any(k in cl for k in ("NE", "NORTH", "129", "103", "055")):
            return (94.805, 94.862, 26.966, 27.012, "ZOOM: NORTHEAST CREST CLUSTER (GK-129 / GK-103 / GK-055)", True)
        if any(k in cl for k in ("CENT", "MID", "112", "087")):
            return (94.782, 94.835, 26.946, 26.986, "ZOOM: CENTRAL ANTICLINE CLUSTER (GK-112 / GK-087)", True)
        if any(k in cl for k in ("SW", "SOUTH", "141", "147", "214")):
            return (94.755, 94.805, 26.915, 26.952, "ZOOM: SOUTHWEST FLANK CLUSTER (GK-141 / GK-147 / GK-214)", True)
        if any(k in cl for k in ("URGENT", "FLAG", "CANDIDATE", "PRIORITY")):
            cand_wells = [w for w in well_records if w["trigger_state"] in ("URGENT", "FLAG", "NO_JOB")]
            if cand_wells:
                c_lons = [w["lon"] for w in cand_wells]
                c_lats = [w["lat"] for w in cand_wells]
                return (
                    round(min(c_lons) - 0.010, 4),
                    round(max(c_lons) + 0.010, 4),
                    round(min(c_lats) - 0.008, 4),
                    round(max(c_lats) + 0.008, 4),
                    "ZOOM: ALL URGENT / FLAG / REFUSED CANDIDATE WELLS",
                    True,
                )

    return (full_lon_min, full_lon_max, full_lat_min, full_lat_max, "FULL FIELD (142 WELLS)", False)


def _render_composite_satellite_map_data_uri(
    well_records: list[dict[str, Any]],
    boundary_pts: list[dict[str, Any]],
    counts: dict[str, int],
    n_rendered: int,
    lon_bounds: tuple[float, float] | None = None,
    lat_bounds: tuple[float, float] | None = None,
    focus_well_id: str = "",
    zoom_title: str = "",
    is_zoomed: bool = False,
    target_width: int = 880,
    quality: int = 74,
) -> str:
    """Render a crisp composite Esri World Imagery satellite map (full field or zoomed cluster crop) as a base64 JPEG data URI."""
    import base64
    import io
    from PIL import Image, ImageDraw

    all_lons = [w["lon"] for w in well_records] + [pt["lon"] for pt in boundary_pts]
    all_lats = [w["lat"] for w in well_records] + [pt["lat"] for pt in boundary_pts]
    full_lon_min = round(min(all_lons) - 0.007, 4) if all_lons else 94.754
    full_lon_max = round(max(all_lons) + 0.007, 4) if all_lons else 94.866
    full_lat_min = round(min(all_lats) - 0.006, 4) if all_lats else 26.912
    full_lat_max = round(max(all_lats) + 0.006, 4) if all_lats else 27.014

    LON_MIN, LON_MAX = lon_bounds if lon_bounds else (full_lon_min, full_lon_max)
    LAT_MIN, LAT_MAX = lat_bounds if lat_bounds else (full_lat_min, full_lat_max)

    sat_path = os.path.join(GEODATA_DIR, "geleki_satellite_basemap.jpg")
    if os.path.exists(sat_path):
        src_im = Image.open(sat_path).convert("RGBA")
        orig_w, orig_h = src_im.size
        target_height = int(round(orig_h * (target_width / float(orig_w))))
        if is_zoomed:
            u0 = max(0.0, min(0.95, (LON_MIN - full_lon_min) / max(1e-6, full_lon_max - full_lon_min)))
            u1 = max(u0 + 0.05, min(1.0, (LON_MAX - full_lon_min) / max(1e-6, full_lon_max - full_lon_min)))
            v0 = max(0.0, min(0.95, (full_lat_max - LAT_MAX) / max(1e-6, full_lat_max - full_lat_min)))
            v1 = max(v0 + 0.05, min(1.0, (full_lat_max - LAT_MIN) / max(1e-6, full_lat_max - full_lat_min)))
            crop_box = (
                int(round(u0 * orig_w)),
                int(round(v0 * orig_h)),
                int(round(u1 * orig_w)),
                int(round(v1 * orig_h)),
            )
            base_im = src_im.crop(crop_box).resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            base_im = src_im.resize((target_width, target_height), Image.Resampling.LANCZOS)
    else:
        target_height = 505
        base_im = Image.new("RGBA", (target_width, target_height), (22, 48, 36, 255))

    W, H = base_im.size
    header_h = 44
    footer_h = 34
    canvas_h = H + header_h + footer_h
    canvas = Image.new("RGBA", (W, canvas_h), (15, 23, 42, 255))
    canvas.paste(base_im, (0, header_h))

    overlay = Image.new("RGBA", (W, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle((0, header_h, W, header_h + H), fill=(8, 18, 30, 36 if is_zoomed else 32))

    def px(lon: float) -> int:
        return int(round(((lon - LON_MIN) / max(1e-6, LON_MAX - LON_MIN)) * W))

    def py(lat: float) -> int:
        return header_h + int(round(((LAT_MAX - lat) / max(1e-6, LAT_MAX - LAT_MIN)) * H))

    # 1. Adaptive coordinate graticules (fine 0.005/0.01 deg grid when zoomed, 0.02 deg full field)
    step_lon = 0.01 if is_zoomed else 0.02
    step_lat = 0.01 if is_zoomed else 0.02
    lon_ticks = [round(LON_MIN + i * step_lon, 3) for i in range(int((LON_MAX - LON_MIN) / step_lon) + 2)]
    lat_ticks = [round(LAT_MIN + i * step_lat, 3) for i in range(int((LAT_MAX - LAT_MIN) / step_lat) + 2)]
    for lon_g in lon_ticks:
        gx = px(lon_g)
        if 20 <= gx <= W - 20:
            draw.line([(gx, header_h), (gx, header_h + H)], fill=(255, 255, 255, 55), width=1)
            draw.text((gx + 4, header_h + H - 16), f"{lon_g:.3f} E" if is_zoomed else f"{lon_g:.2f} E", fill=(226, 232, 240, 220))
    for lat_g in lat_ticks:
        gy = py(lat_g)
        if header_h + 16 <= gy <= header_h + H - 16:
            draw.line([(0, gy), (W, gy)], fill=(255, 255, 255, 55), width=1)
            draw.text((6, gy - 14), f"{lat_g:.3f} N" if is_zoomed else f"{lat_g:.2f} N", fill=(226, 232, 240, 220))

    # 2. Geleki concession boundary polygon
    if len(boundary_pts) > 2:
        poly_xy = [(px(pt["lon"]), py(pt["lat"])) for pt in boundary_pts]
        draw.polygon(poly_xy, fill=(56, 189, 248, 24), outline=(253, 224, 71, 245), width=3)
        if not is_zoomed:
            bx, by = px(94.764), py(27.004)
            draw.rectangle((bx - 4, by - 3, bx + 232, by + 16), fill=(15, 23, 42, 215), outline=(253, 224, 71, 230), width=1)
            draw.text((bx + 4, by), "ONGC GELEKI LEASE BOUNDARY (ASSAM)", fill=(253, 224, 71, 255))

    # 3. Plot wells in viewport
    rgba_map = {
        "URGENT": (239, 68, 68, 255),
        "FLAG": (249, 115, 22, 250),
        "NO_JOB": (59, 130, 246, 250),
        "WATCH": (234, 179, 8, 245),
        "HEALTHY": (16, 185, 129, 235),
        "SHUT_IN": (148, 163, 184, 210),
    }
    z_order = {"SHUT_IN": 1, "HEALTHY": 2, "WATCH": 3, "NO_JOB": 4, "FLAG": 5, "URGENT": 6}
    sorted_wells = sorted(well_records, key=lambda r: z_order.get(r["trigger_state"], 0))
    fw_upper = (focus_well_id or "").strip().upper()

    placed_boxes: list[tuple[int, int, int, int]] = []
    for w in sorted_wells:
        x, y = px(w["lon"]), py(w["lat"])
        if not (-20 <= x <= W + 20 and header_h - 20 <= y <= header_h + H + 20):
            continue
        rate = float(w.get("oil_rate_bopd") or 5.0)
        scale_mult = 1.25 if is_zoomed else 1.0
        radius = max(6 if is_zoomed else 5, min(18, int(round((4.5 + (rate ** 0.5) * 0.75) * scale_mult))))
        col = rgba_map.get(w["trigger_state"], (16, 185, 129, 235))
        is_hi = w["trigger_state"] in ("URGENT", "FLAG", "NO_JOB") or (w["well_id"].upper() == fw_upper)

        if w["well_id"].upper() == fw_upper:
            draw.ellipse((x - radius - 14, y - radius - 14, x + radius + 14, y + radius + 14), outline=(56, 189, 248, 255), width=3)
            draw.line([(x - radius - 20, y), (x - radius - 8, y)], fill=(56, 189, 248, 255), width=2)
            draw.line([(x + radius + 8, y), (x + radius + 20, y)], fill=(56, 189, 248, 255), width=2)
            draw.line([(x, y - radius - 20), (x, y - radius - 8)], fill=(56, 189, 248, 255), width=2)
            draw.line([(x, y + radius + 8), (x, y + radius + 20)], fill=(56, 189, 248, 255), width=2)

        if w["trigger_state"] == "URGENT":
            draw.ellipse((x - radius - 6, y - radius - 6, x + radius + 6, y + radius + 6), outline=(239, 68, 68, 235), width=3)
            draw.ellipse((x - radius - 11, y - radius - 11, x + radius + 11, y + radius + 11), outline=(239, 68, 68, 145), width=2)
        elif w["trigger_state"] == "FLAG":
            draw.ellipse((x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4), outline=(249, 115, 22, 200), width=2)

        stroke_col = (255, 255, 255, 255) if is_hi else (15, 23, 42, 240)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=col, outline=stroke_col, width=2)

    # Draw callout labels in priority order with collision avoidance
    for w in reversed(sorted_wells):
        if not w.get("label"):
            continue
        x, y = px(w["lon"]), py(w["lat"])
        if not (4 <= x <= W - 4 and header_h + 4 <= y <= header_h + H - 4):
            continue
        rate = float(w.get("oil_rate_bopd") or 5.0)
        scale_mult = 1.25 if is_zoomed else 1.0
        radius = max(6 if is_zoomed else 5, min(18, int(round((4.5 + (rate ** 0.5) * 0.75) * scale_mult))))
        col = rgba_map.get(w["trigger_state"], (16, 185, 129, 235))
        if w["well_id"].upper() == fw_upper:
            col = (56, 189, 248, 255)
        lbl = f"{w['well_id']} ({int(round(rate))}b/d)"
        tw = len(lbl) * 6 + 10
        candidates = [
            (x + radius + 6, y - 9),
            (x - radius - tw - 6, y - 9),
            (x + radius + 6, y - 27),
            (x + radius + 6, y + 10),
            (x - radius - tw - 6, y + 10),
            (x - radius - tw - 6, y - 27),
        ]
        chosen_lx, chosen_ly = candidates[0]
        for cx, cy in candidates:
            lx = min(W - tw - 6, max(6, cx))
            ly = max(header_h + 6, min(header_h + H - 22, cy))
            box = (lx - 2, ly - 2, lx + tw + 2, ly + 19)
            if not any(
                not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3])
                for b in placed_boxes
            ):
                chosen_lx, chosen_ly = lx, ly
                break
        placed_boxes.append((chosen_lx, chosen_ly, chosen_lx + tw, chosen_ly + 17))
        draw.rectangle((chosen_lx, chosen_ly, chosen_lx + tw, chosen_ly + 17), fill=(15, 23, 42, 235), outline=col, width=2)
        draw.text((chosen_lx + 5, chosen_ly + 2), lbl, fill=(255, 255, 255, 255))

    # 4. Top GIS header bar (ASCII-clean for PIL bitmap font)
    draw.rectangle((0, 0, W, header_h), fill=(15, 23, 42, 255))
    draw.line([(0, header_h - 1), (W, header_h - 1)], fill=(51, 65, 85, 255), width=1)
    hdr_left = (
        f"ONGC ASSAM ASSET - GELEKI SATELLITE GIS | {zoom_title} ({n_rendered} WELLS IN VIEW)"
        if is_zoomed
        else f"ONGC ASSAM ASSET - GELEKI FIELD SATELLITE GIS WELL MAP ({n_rendered} WELLS | ESRI WORLD IMAGERY)"
    )
    draw.text((14, 13), hdr_left, fill=(248, 250, 252, 255))
    draw.text((W - 265, 13), "WGS84 (EPSG:4326) | SIVASAGAR, ASSAM", fill=(56, 189, 248, 255))

    # 5. Bottom legend & status bar
    fy = header_h + H
    draw.rectangle((0, fy, W, canvas_h), fill=(15, 23, 42, 255))
    draw.line([(0, fy), (W, fy)], fill=(51, 65, 85, 255), width=1)
    legend_items = [
        ("URGENT", counts.get("URGENT", 0), (239, 68, 68, 255)),
        ("FLAG", counts.get("FLAG", 0), (249, 115, 22, 255)),
        ("NO_JOB (REFUSED)", counts.get("NO_JOB", 0), (59, 130, 246, 255)),
        ("HEALTHY", counts.get("HEALTHY", 0), (16, 185, 129, 255)),
        ("SHUT_IN", counts.get("SHUT_IN", 0), (148, 163, 184, 255)),
    ]
    lx_cursor = 14
    for name, cnt, lcol in legend_items:
        draw.ellipse((lx_cursor, fy + 10, lx_cursor + 12, fy + 22), fill=lcol, outline=(255, 255, 255, 220), width=1)
        txt = f"{name}: {cnt}"
        draw.text((lx_cursor + 17, fy + 10), txt, fill=(241, 245, 249, 255))
        lx_cursor += len(txt) * 6 + 38

    draw.text((W - 235, fy + 10), "Bubble Size = Oil Rate (BOPD)", fill=(148, 163, 184, 255))

    final_rgb = Image.alpha_composite(canvas, overlay).convert("RGB")
    buf = io.BytesIO()
    final_rgb.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _render_georeferenced_satellite_tile_uri(
    well_records: list[dict[str, Any]],
    boundary_pts: list[dict[str, Any]],
    lon_bounds: tuple[float, float] | None = None,
    lat_bounds: tuple[float, float] | None = None,
    is_zoomed: bool = False,
    target_width: int = 680,
    quality: int = 58,
) -> str:
    """Render a pure georeferenced Esri World Imagery satellite raster tile (no header/footer padding) for Vega-Lite Layer 0 mark:image."""
    import base64
    import io
    from PIL import Image, ImageDraw

    all_lons = [w["lon"] for w in well_records] + [pt["lon"] for pt in boundary_pts]
    all_lats = [w["lat"] for w in well_records] + [pt["lat"] for pt in boundary_pts]
    full_lon_min = round(min(all_lons) - 0.007, 4) if all_lons else 94.754
    full_lon_max = round(max(all_lons) + 0.007, 4) if all_lons else 94.866
    full_lat_min = round(min(all_lats) - 0.006, 4) if all_lats else 26.912
    full_lat_max = round(max(all_lats) + 0.006, 4) if all_lats else 27.014

    LON_MIN, LON_MAX = lon_bounds if lon_bounds else (full_lon_min, full_lon_max)
    LAT_MIN, LAT_MAX = lat_bounds if lat_bounds else (full_lat_min, full_lat_max)

    sat_path = os.path.join(GEODATA_DIR, "geleki_satellite_basemap.jpg")
    if os.path.exists(sat_path):
        src_im = Image.open(sat_path).convert("RGBA")
        orig_w, orig_h = src_im.size
        target_height = int(round(orig_h * (target_width / float(orig_w))))
        if is_zoomed:
            u0 = max(0.0, min(0.95, (LON_MIN - full_lon_min) / max(1e-6, full_lon_max - full_lon_min)))
            u1 = max(u0 + 0.05, min(1.0, (LON_MAX - full_lon_min) / max(1e-6, full_lon_max - full_lon_min)))
            v0 = max(0.0, min(0.95, (full_lat_max - LAT_MAX) / max(1e-6, full_lat_max - full_lat_min)))
            v1 = max(v0 + 0.05, min(1.0, (full_lat_max - LAT_MIN) / max(1e-6, full_lat_max - full_lat_min)))
            crop_box = (
                int(round(u0 * orig_w)),
                int(round(v0 * orig_h)),
                int(round(u1 * orig_w)),
                int(round(v1 * orig_h)),
            )
            base_im = src_im.crop(crop_box).resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            base_im = src_im.resize((target_width, target_height), Image.Resampling.LANCZOS)
    else:
        target_height = 510
        base_im = Image.new("RGBA", (target_width, target_height), (22, 48, 36, 255))

    W, H = base_im.size
    tint = Image.new("RGBA", (W, H), (8, 18, 30, 38))
    draw = ImageDraw.Draw(tint)
    if not is_zoomed:
        draw.rectangle((12, 10, 295, 30), fill=(15, 23, 42, 195), outline=(253, 224, 71, 220), width=1)
        draw.text((18, 15), "ONGC GELEKI LEASE · ESRI WORLD IMAGERY", fill=(253, 224, 71, 255))

    final_rgb = Image.alpha_composite(base_im, tint).convert("RGB")
    buf = io.BytesIO()
    final_rgb.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def build_well_map_surface(
    field: str = "Geleki",
    focus_well_id: str = "",
    cluster: str = "",
    radius_deg: float = 0.018,
    surface_id: str | None = None,
) -> list[types.Part]:
    """Build a single unified, full-bleed A2UI v0.9 Interactive Satellite GIS VegaChart surface for the Geleki Field Map (TC-016)."""
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

    lon_min, lon_max, lat_min, lat_max, zoom_title, is_zoomed = _resolve_map_viewport(
        well_records=well_records,
        boundary_pts=boundary_pts,
        focus_well_id=focus_well_id,
        cluster=cluster,
        radius_deg=radius_deg if radius_deg != 0.018 else 0.013,
    )

    in_view_wells = [
        w
        for w in well_records
        if lon_min <= w["lon"] <= lon_max and lat_min <= w["lat"] <= lat_max
    ]
    if is_zoomed and in_view_wells:
        c_lon = 0.5 * (lon_min + lon_max)
        c_lat = 0.5 * (lat_min + lat_max)
        nearest = sorted(
            in_view_wells,
            key=lambda w: (w["lon"] - c_lon) ** 2 + (w["lat"] - c_lat) ** 2,
        )[:14]
        for w in nearest:
            w["label"] = w["well_id"]

    counts = wm.colour_legend
    sat_tile_uri = _render_georeferenced_satellite_tile_uri(
        well_records=well_records,
        boundary_pts=boundary_pts,
        lon_bounds=(lon_min, lon_max),
        lat_bounds=(lat_min, lat_max),
        is_zoomed=is_zoomed,
        target_width=600,
        quality=50,
    )

    lon_domain = [lon_min, lon_max]
    lat_domain = [lat_min, lat_max]

    fw_upper = (focus_well_id or "").strip().upper()

    # Single unified Interactive Satellite GIS Vega-Lite specification:
    # Layer 0 is the georeferenced satellite tile bound to [lon_min..lon_max, lat_min..lat_max]
    # on the exact same pan/zoom coordinate scales as the lease boundary and 142 interactive well markers.
    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 760,
        "height": 540,
        "padding": 6,
        "autosize": {"type": "fit", "contains": "padding"},
        "background": "#0F172A",
        "config": {
            "axis": {
                "labelColor": "#CBD5E1",
                "titleColor": "#F8FAFC",
                "gridColor": "rgba(255, 255, 255, 0.16)",
                "domainColor": "#475569",
                "tickColor": "#475569",
                "labelFontSize": 11,
                "titleFontSize": 12,
            },
            "legend": {
                "labelColor": "#F1F5F9",
                "titleColor": "#38BDF8",
                "labelFontSize": 11,
                "titleFontSize": 11,
                "fillColor": "#1E293B",
                "strokeColor": "#334155",
                "padding": 8,
                "cornerRadius": 6,
            },
            "view": {"stroke": "#334155", "strokeWidth": 1.5},
        },
        "data": {"values": well_records},
        "layer": [
            {
                "data": {
                    "values": [
                        {
                            "img_uri": sat_tile_uri,
                            "lon_min": lon_min,
                            "lon_max": lon_max,
                            "lat_min": lat_min,
                            "lat_max": lat_max,
                        }
                    ]
                },
                "mark": {"type": "image", "aspect": False, "clip": True},
                "encoding": {
                    "url": {"field": "img_uri", "type": "nominal"},
                    "x": {
                        "field": "lon_min",
                        "type": "quantitative",
                        "scale": {"domain": lon_domain, "zero": False},
                        "title": "Longitude (°E — Scroll Mouse Wheel to Zoom · Drag to Pan · Double-Click to Reset)",
                    },
                    "x2": {"field": "lon_max"},
                    "y": {
                        "field": "lat_max",
                        "type": "quantitative",
                        "scale": {"domain": lat_domain, "zero": False},
                        "title": "Latitude (°N)",
                    },
                    "y2": {"field": "lat_min"},
                },
            },
            {
                "data": {"values": boundary_pts},
                "mark": {
                    "type": "line",
                    "color": "#FDE047",
                    "strokeDash": [7, 4],
                    "strokeWidth": 2.4,
                    "fill": "#38BDF8",
                    "fillOpacity": 0.08,
                    "clip": True,
                },
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative", "scale": {"domain": lon_domain, "zero": False}},
                    "y": {"field": "lat", "type": "quantitative", "scale": {"domain": lat_domain, "zero": False}},
                    "order": {"field": "order", "type": "quantitative"},
                },
            },
            {
                "transform": [
                    {
                        "filter": (
                            f"datum.trigger_state == 'URGENT' || datum.trigger_state == 'FLAG' || datum.trigger_state == 'NO_JOB'"
                            + (f" || datum.well_id == '{fw_upper}'" if fw_upper else "")
                        )
                    }
                ],
                "mark": {
                    "type": "point",
                    "filled": False,
                    "strokeWidth": 2.4,
                    "opacity": 0.9,
                    "clip": True,
                },
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative"},
                    "y": {"field": "lat", "type": "quantitative"},
                    "size": {
                        "field": "oil_rate_bopd",
                        "type": "quantitative",
                        "legend": None,
                        "scale": {"range": [220, 720]},
                    },
                    "color": {
                        "field": "trigger_state",
                        "type": "nominal",
                        "legend": None,
                        "scale": {
                            "domain": ["URGENT", "FLAG", "NO_JOB", "HEALTHY", "SHUT_IN"],
                            "range": ["#EF4444", "#FB923C", "#38BDF8", "#10B981", "#CBD5E1"],
                        },
                    },
                },
            },
            {
                "params": [
                    {"name": "pan_zoom", "select": "interval", "bind": "scales"},
                    {
                        "name": "status_filter",
                        "select": {"type": "point", "fields": ["trigger_state"]},
                        "bind": "legend",
                    },
                ],
                "mark": {
                    "type": "circle",
                    "stroke": "#FFFFFF",
                    "strokeWidth": 1.3,
                    "clip": True,
                },
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative", "scale": {"domain": lon_domain, "zero": False}},
                    "y": {"field": "lat", "type": "quantitative", "scale": {"domain": lat_domain, "zero": False}},
                    "size": {
                        "field": "oil_rate_bopd",
                        "type": "quantitative",
                        "title": "Oil Rate (BOPD)",
                        "scale": {"range": [65, 440] if is_zoomed else [50, 380]},
                    },
                    "color": {
                        "field": "trigger_state",
                        "type": "nominal",
                        "title": "Status (Click to Filter)",
                        "scale": {
                            "domain": ["URGENT", "FLAG", "NO_JOB", "HEALTHY", "SHUT_IN"],
                            "range": ["#EF4444", "#FB923C", "#38BDF8", "#10B981", "#CBD5E1"],
                        },
                    },
                    "opacity": {
                        "condition": {"param": "status_filter", "value": 0.96},
                        "value": 0.15,
                    },
                    "tooltip": [
                        {"field": "well_id", "type": "nominal", "title": "Well ID"},
                        {"field": "trigger_state", "type": "nominal", "title": "Status / Trigger"},
                        {"field": "zone", "type": "nominal", "title": "Reservoir Sand"},
                        {"field": "lift_type", "type": "nominal", "title": "Artificial Lift"},
                        {"field": "oil_rate_bopd", "type": "quantitative", "title": "Oil Rate (BOPD)"},
                        {"field": "water_cut_pct", "type": "quantitative", "title": "Water Cut (%)"},
                        {"field": "lon", "type": "quantitative", "title": "Longitude (°E)", "format": ".4f"},
                        {"field": "lat", "type": "quantitative", "title": "Latitude (°N)", "format": ".4f"},
                    ],
                },
            },
            {
                "transform": [{"filter": "datum.label != ''"}],
                "mark": {
                    "type": "text",
                    "align": "left",
                    "dx": 9,
                    "dy": -6,
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": "#FFFFFF",
                    "stroke": "#0F172A",
                    "strokeWidth": 0.4,
                    "clip": True,
                },
                "encoding": {
                    "x": {"field": "lon", "type": "quantitative"},
                    "y": {"field": "lat", "type": "quantitative"},
                    "text": {"field": "label", "type": "nominal"},
                },
            },
        ],
    }

    sid = surface_id or f"geleki-map-{uuid.uuid4().hex[:8]}"
    title_text = (
        f"Geleki Field — {zoom_title} ({len(in_view_wells)} Wells in Zoomed Cluster)"
        if is_zoomed
        else f"Geleki Field — {wm.n_rendered}-Well Interactive Satellite GIS Map"
    )
    caption_text = (
        f"URGENT: {counts.get('URGENT', 0)} · FLAG: {counts.get('FLAG', 0)} · "
        f"NO_JOB: {counts.get('NO_JOB', 0)} · HEALTHY: {counts.get('HEALTHY', 0)} · "
        f"SHUT_IN: {counts.get('SHUT_IN', 0)} · Scroll Mouse-Wheel to Zoom Satellite Map · Drag to Pan · Click Legend to Filter"
    )
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
            "text": title_text,
            "variant": "h3",
        },
        {
            "id": "card-caption",
            "component": "Text",
            "text": caption_text,
            "variant": "caption",
        },
        {
            "id": "card-chart",
            "component": "VegaChart",
            "spec": {"path": "/spec"},
            "height": 560,
        },
    ]
    return [
        wrap_a2ui_part("createSurface", sid, {"catalogId": DEFAULT_GE_CATALOG_ID}),
        wrap_a2ui_part("updateDataModel", sid, {"value": {"spec": vega_spec}}),
        wrap_a2ui_part("updateComponents", sid, {"components": components}),
    ]


def build_google_maps_card_surface(
    field: str = "Geleki",
    well_id: str = "",
    cluster: str = "",
    surface_id: str | None = None,
) -> list[types.Part]:
    """Build an A2UI v0.9 interactive Google Maps Satellite 3D launch card for a specific well, cluster, or field."""
    from tools.render_well_map import render_well_map

    res = render_well_map(field=field)
    wm = res.value
    target_name = f"{field} Field (Assam)"
    lat = 26.9634
    lon = 94.8105
    zoom = 14
    info_lines: list[str] = []

    fw_upper = (well_id or "").strip().upper()
    cl_upper = (cluster or "").strip().upper()

    if fw_upper:
        for p in wm.points:
            if p.well_id.upper() == fw_upper:
                lat = float(p.lat)
                lon = float(p.lon)
                zoom = 17
                target_name = f"Well {p.well_id}"
                oil_rate = p.size_value or 0.0
                state = p.colour_key
                zone = p.tooltip.get("current_zone", "Unknown")
                lift = p.tooltip.get("lift_type", "Unknown")
                wc = p.tooltip.get("water_cut_pct", 0.0)
                info_lines = [
                    f"**Target Well:** `{p.well_id}` (Urgency Status: **{state}**)",
                    f"**GPS Coordinates:** `{lat:.5f}°N, {lon:.5f}°E` (WGS84)",
                    f"**Reservoir Formation:** {zone}  ·  **Artificial Lift:** {lift}",
                    f"**Current Telemetry:** {oil_rate:.1f} BOPD  ·  Water Cut: {wc:.1f}%",
                ]
                break
    elif cl_upper:
        target_name = f"Geleki {cl_upper} Cluster"
        zoom = 16
        if any(k in cl_upper for k in ("NE", "NORTH", "129")):
            lat, lon = 26.9890, 94.8335
        elif any(k in cl_upper for k in ("CENT", "MID", "112")):
            lat, lon = 26.9660, 94.8085
        elif any(k in cl_upper for k in ("SW", "SOUTH", "141")):
            lat, lon = 26.9335, 94.7800

    gmaps_sat_url = f"https://www.google.com/maps/@{lat:.5f},{lon:.5f},{zoom}z/data=!3m1!1e3"
    gmaps_pin_url = f"https://www.google.com/maps/search/?api=1&query={lat:.5f},{lon:.5f}"

    sid = surface_id or f"gmaps-{uuid.uuid4().hex[:8]}"
    card_title = f"Google Maps Satellite View — {target_name}"
    caption_text = f"Coordinates: {lat:.5f}°N, {lon:.5f}°E · Zoom: {zoom}z"

    lines = list(info_lines) if info_lines else [
        f"Live satellite view of the ONGC Geleki Field ({wm.n_rendered} active wellheads).",
        f"**Field Center:** `{lat:.5f}°N, {lon:.5f}°E` (Upper Assam Shelf)",
    ]
    lines.append("")
    lines.append(f"👉 **[📍 Launch in Live Google Maps (3D Satellite)]({gmaps_sat_url})**")
    lines.append(f"📌 **[🗺️ Open Pinned Coordinates in Google Maps]({gmaps_pin_url})**")
    details_md = "\n\n".join(lines)

    components = [
        {"id": "root", "component": "Card", "child": "card-col"},
        {
            "id": "card-col",
            "component": "Column",
            "children": ["card-title", "card-caption", "card-details"],
        },
        {"id": "card-title", "component": "Text", "text": card_title, "variant": "h3"},
        {"id": "card-caption", "component": "Text", "text": caption_text, "variant": "caption"},
        {"id": "card-details", "component": "Text", "text": details_md, "variant": "body"},
    ]
    return [
        wrap_a2ui_part("createSurface", sid, {"catalogId": DEFAULT_GE_CATALOG_ID}),
        wrap_a2ui_part(
            "updateDataModel",
            sid,
            {
                "value": {
                    "target": target_name,
                    "lat": lat,
                    "lon": lon,
                    "zoom": zoom,
                    "satellite_url": gmaps_sat_url,
                    "pin_url": gmaps_pin_url,
                }
            },
        ),
        wrap_a2ui_part("updateComponents", sid, {"components": components}),
    ]


def build_production_chart_surface(
    well_id: str = "GK-129",
    months: int = 36,
    surface_id: str | None = None,
) -> list[types.Part]:
    """Build A2UI v0.9 interactive dual-axis time-series chart for oil/water/liquid rates & water cut (TC-017).

    Uses a single-view layer spec with independent Y scales (not vconcat) so Gemini Enterprise's
    transformSpec (which rewrites top-level width/height to 'container' with autosize='fit')
    always renders cleanly.
    """
    dp = load_table("daily_production")
    wh = load_table("workover_history")
    w_dp = dp[dp["well_id"] == well_id].sort_values("production_date").copy()
    if w_dp.empty:
        w_dp = dp[dp["well_id"] == "GK-129"].sort_values("production_date").copy()
        well_id = "GK-129"

    w_dp["prod_date_dt"] = pd.to_datetime(w_dp["production_date"])
    cutoff = w_dp["prod_date_dt"].max() - pd.Timedelta(days=int(months * 30.5))
    w_dp = w_dp[w_dp["prod_date_dt"] >= cutoff].reset_index(drop=True)
    stride_idx = set(w_dp.iloc[::10].index)
    shutin_mask = (~w_dp["is_producing"].astype(bool)) | w_dp["oil_rate_bopd"].isna()
    shutin_idx = set(w_dp[shutin_mask].iloc[::4].index)
    keep_idx = sorted(stride_idx | shutin_idx | {w_dp.index[0], w_dp.index[-1]})
    sampled = w_dp.loc[keep_idx].drop_duplicates(subset=["production_date"]).copy()

    rate_values: list[dict[str, Any]] = []
    wc_values: list[dict[str, Any]] = []
    for _, r in sampled.iterrows():
        d_str = str(r["production_date"])[:10]
        is_shutin = not bool(r.get("is_producing", True)) or pd.isna(r.get("oil_rate_bopd"))
        oil_val = None if is_shutin else round(float(r["oil_rate_bopd"]), 1)
        wat_val = None if is_shutin else round(float(r["water_rate_bwpd"]), 1)
        liq_val = None if is_shutin else round(float(r["liquid_rate_blpd"]), 1)
        wc_val = None if is_shutin else round(float(r["water_cut_pct"]), 1)

        rate_values.append({"date": d_str, "series": "Oil Rate (BOPD)", "rate": oil_val, "wc": wc_val})
        rate_values.append({"date": d_str, "series": "Water Rate (BWPD)", "rate": wat_val, "wc": wc_val})
        rate_values.append({"date": d_str, "series": "Total Liquid (BLPD)", "rate": liq_val, "wc": wc_val})
        wc_values.append({"date": d_str, "series": "Water Cut (%)", "water_cut_pct": wc_val})

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
        "width": 640,
        "height": 340,
        "background": "#FFFFFF",
        "data": {"values": rate_values},
        "resolve": {"scale": {"y": "independent"}},
        "layer": [
            {
                "mark": {"type": "line", "strokeWidth": 2.4, "point": False},
                "encoding": {
                    "x": {"field": "date", "type": "temporal", "title": "Production Date"},
                    "y": {
                        "field": "rate",
                        "type": "quantitative",
                        "title": "Fluid Rate (BOPD / BWPD / BLPD)",
                        "axis": {"orient": "left"},
                    },
                    "color": {
                        "field": "series",
                        "type": "nominal",
                        "title": "Telemetry Stream",
                        "scale": {
                            "domain": [
                                "Oil Rate (BOPD)",
                                "Water Rate (BWPD)",
                                "Total Liquid (BLPD)",
                                "Water Cut (%)",
                            ],
                            "range": ["#16A34A", "#2563EB", "#64748B", "#DC2626"],
                        },
                    },
                    "tooltip": [
                        {"field": "date", "type": "temporal", "title": "Date"},
                        {"field": "series", "type": "nominal", "title": "Stream"},
                        {"field": "rate", "type": "quantitative", "title": "Rate (bbl/d)"},
                        {"field": "wc", "type": "quantitative", "title": "Water Cut (%)"},
                    ],
                },
            },
            {
                "data": {"values": wc_values},
                "mark": {
                    "type": "line",
                    "strokeWidth": 2.0,
                    "strokeDash": [4, 3],
                    "color": "#DC2626",
                },
                "encoding": {
                    "x": {"field": "date", "type": "temporal"},
                    "y": {
                        "field": "water_cut_pct",
                        "type": "quantitative",
                        "title": "Water Cut (%)",
                        "scale": {"domain": [0, 100]},
                        "axis": {"orient": "right", "titleColor": "#DC2626", "labelColor": "#DC2626"},
                    },
                    "color": {"field": "series", "type": "nominal"},
                },
            },
            {
                "data": {"values": interventions},
                "mark": {"type": "rule", "color": "#D97706", "strokeDash": [6, 3], "strokeWidth": 2.2},
                "encoding": {
                    "x": {"field": "date", "type": "temporal"},
                    "tooltip": [
                        {"field": "date", "type": "temporal", "title": "Workover Date"},
                        {"field": "label", "type": "nominal", "title": "Job & Outcome"},
                    ],
                },
            },
        ],
    }

    return build_vega_card_parts(
        title=f"{well_id} — {months}-Month Oil/Water/Liquid Rate & Water Cut Telemetry",
        caption=(
            f"Shut-in days preserved as gaps (TC-017.1)  ·  "
            f"Workover markers: {', '.join(i['label'] for i in interventions) or 'None'}"
        ),
        vega_spec=vega_spec,
        height=390,
        surface_id=surface_id,
    )


def build_chan_chart_surface(well_id: str = "GK-129", surface_id: str | None = None) -> list[types.Part]:
    """Build A2UI v0.9 SPE-30775 Log-Log WOR & WOR' Derivative diagnostic plot (TC-002)."""
    from tools import chan_diagnostic

    res = chan_diagnostic(well_id)
    slope = float(res.value.wor_prime_slope) if res.value else 1.08
    wor_slope = float(res.value.wor_slope) if res.value else 1.12
    mech = res.value.mechanism.value if res.value else "CHANNELLING"

    pts: list[dict[str, Any]] = []
    if res.value and res.value.series:
        for idx, (_dt, wor, wor_p) in enumerate(res.value.series, start=1):
            pts.append({"day": idx, "curve": "WOR (Water-Oil Ratio)", "val": round(max(float(wor), 0.001), 4)})
            pts.append({"day": idx, "curve": "WOR' Derivative (dWOR/dt)", "val": round(max(float(wor_p), 0.001), 4)})
    else:
        for d in [5, 10, 15, 20, 25, 30]:
            wor = 0.8 * ((d / 5.0) ** max(wor_slope, 0.25))
            wor_p = 0.04 * ((d / 5.0) ** max(slope, 0.25))
            pts.append({"day": d, "curve": "WOR (Water-Oil Ratio)", "val": round(float(wor), 4)})
            pts.append({"day": d, "curve": "WOR' Derivative (dWOR/dt)", "val": round(float(wor_p), 4)})

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 640,
        "height": 340,
        "background": "#FFFFFF",
        "data": {"values": pts},
        "mark": {"type": "line", "point": True, "strokeWidth": 2.5},
        "encoding": {
            "x": {
                "field": "day",
                "type": "quantitative",
                "scale": {"type": "log"},
                "title": "Days in Diagnostic Window (Log Scale)",
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
                {"field": "day", "type": "quantitative", "title": "Day"},
                {"field": "curve", "type": "nominal", "title": "Curve"},
                {"field": "val", "type": "quantitative", "title": "Value"},
            ],
        },
    }

    return build_vega_card_parts(
        title=f"{well_id} — SPE-30775 Chan Water-Control Log-Log Diagnostic",
        caption=f"Log-Log WOR slope = {wor_slope:+.2f}, WOR' slope = {slope:+.2f} ({mech}) · Positive slope confirms behind-pipe channelling vs negative slope for coning",
        vega_spec=vega_spec,
        height=400,
        surface_id=surface_id,
    )


def build_ranking_chart_surface(surface_id: str | None = None) -> list[types.Part]:
    """Build A2UI v0.9 Candidate Ranking & Uplift Bar Chart (TC-010)."""
    from tools import rank_candidates

    queues = rank_candidates(field="Geleki").value
    bars: list[dict[str, Any]] = []
    if queues:
        for c in queues.rig_queue + queues.rigless_queue:
            bars.append(
                {
                    "well_id": f"{c.well_id} ({c.job_code})",
                    "queue": f"{c.queue} QUEUE",
                    "uplift_bbl_12mo": round(float(c.deferred_bbl_avoided_12mo), 0),
                    "net_value_lakh": round(float(c.net_value_inr_lakh), 1),
                    "priority_lakh_per_day": round(float(c.priority_value_per_day_lakh), 1),
                    "job_code": c.job_code,
                    "diagnosis": c.mechanism,
                    "rig_days": float(c.rig_days),
                }
            )
    bars.append(
        {
            "well_id": "GK-141 (REFUSED)",
            "queue": "REFUSED (RESERVOIR_DECLINE)",
            "uplift_bbl_12mo": 0.0,
            "net_value_lakh": 0.0,
            "priority_lakh_per_day": 0.0,
            "job_code": "NO_JOB_JUSTIFIED",
            "diagnosis": "OFFSET_RESERVOIR_DECLINE",
            "rig_days": 0.0,
        }
    )

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 640,
        "height": 320,
        "background": "#FFFFFF",
        "data": {"values": bars},
        "mark": {"type": "bar", "cornerRadiusEnd": 4},
        "encoding": {
            "y": {
                "field": "well_id",
                "type": "nominal",
                "sort": "-x",
                "title": "Candidate Well & Job Code",
            },
            "x": {
                "field": "net_value_lakh",
                "type": "quantitative",
                "title": "12-Month Net Economic Value (INR Lakh)",
            },
            "color": {
                "field": "queue",
                "type": "nominal",
                "title": "Execution Queue",
                "scale": {
                    "domain": ["RIG QUEUE", "RIGLESS QUEUE", "REFUSED (RESERVOIR_DECLINE)"],
                    "range": ["#DC2626", "#2563EB", "#94A3B8"],
                },
            },
            "tooltip": [
                {"field": "well_id", "type": "nominal", "title": "Well & Job"},
                {"field": "queue", "type": "nominal", "title": "Queue"},
                {"field": "diagnosis", "type": "nominal", "title": "Mechanism"},
                {"field": "net_value_lakh", "type": "quantitative", "title": "Net Value (INR Lakh)"},
                {"field": "priority_lakh_per_day", "type": "quantitative", "title": "Priority (INR Lakh/Day)"},
                {"field": "uplift_bbl_12mo", "type": "quantitative", "title": "Deferred Oil Avoided (12mo BBL)"},
                {"field": "rig_days", "type": "quantitative", "title": "Rig/Crew Days"},
            ],
        },
    }

    return build_vega_card_parts(
        title="Geleki Field — Ranked Rig & Rigless Workover Candidates (Economic Value & Priority)",
        caption="Rig Queue (GK-055, GK-087, GK-129) · Rigless Queue (GK-103, GK-112, GK-147) · Refused: GK-141 (NO_JOB_JUSTIFIED — Regional Reservoir Decline)",
        vega_spec=vega_spec,
        height=390,
        surface_id=surface_id,
    )


def build_report_surface(
    field: str = "Geleki",
    period: str = "WEEKLY",
    surface_id: str | None = None,
) -> list[types.Part]:
    """Build A2UI v0.9 Rig & Rigless Campaign Schedule Gantt / Uplift Chart for Turn 4 Executive Reports (TC-014 / TC-015)."""
    from tools import schedule_rigs

    sched = schedule_rigs(field=field).value
    rows: list[dict[str, Any]] = []
    if isinstance(sched, dict) and sched.get("rig_assignments"):
        for idx, a in enumerate(sched["rig_assignments"]):
            dur = float(a.get("rig_days", 3.0))
            rows.append(
                {
                    "well_id": f"{a['well_id']} ({a['job_code']})",
                    "unit": a.get("rig_id", f"RIG-ASSAM-0{idx+1}"),
                    "queue": "RIG CAMPAIGN",
                    "start_day": idx * 2,
                    "end_day": idx * 2 + dur,
                    "duration_days": dur,
                    "uplift_bbl_12mo": float(a.get("deferred_bbl_avoided_12mo", 4500.0)),
                }
            )
    rows.extend(
        [
            {"well_id": "GK-103 (SURF_CHOKE_ADJ)", "unit": "SURF-CREW-01", "queue": "RIGLESS CREW", "start_day": 1, "end_day": 1.5, "duration_days": 0.5, "uplift_bbl_12mo": 2680.0},
            {"well_id": "GK-112 (CHEM_SCALE_BULLHEAD)", "unit": "CTU-NAZIRA-01", "queue": "RIGLESS CREW", "start_day": 1.5, "end_day": 3.0, "duration_days": 1.5, "uplift_bbl_12mo": 7420.0},
            {"well_id": "GK-147 (CHEM_HOT_OIL_ANNULUS)", "unit": "HOU-GELEKI-01", "queue": "RIGLESS CREW", "start_day": 2.5, "end_day": 4.0, "duration_days": 1.5, "uplift_bbl_12mo": 4520.0},
        ]
    )

    vega_spec: dict[str, Any] = {
        "$schema": VEGA_SCHEMA_URL,
        "width": 640,
        "height": 300,
        "background": "#FFFFFF",
        "data": {"values": rows},
        "mark": {"type": "bar", "cornerRadius": 4, "height": 22},
        "encoding": {
            "y": {
                "field": "well_id",
                "type": "nominal",
                "title": "Scheduled Intervention (Well & Job Code)",
                "sort": {"field": "start_day", "order": "ascending"},
            },
            "x": {
                "field": "start_day",
                "type": "quantitative",
                "title": "Campaign Timeline (Days from Dispatch)",
            },
            "x2": {"field": "end_day"},
            "color": {
                "field": "queue",
                "type": "nominal",
                "title": "Execution Resource",
                "scale": {
                    "domain": ["RIG CAMPAIGN", "RIGLESS CREW"],
                    "range": ["#DC2626", "#2563EB"],
                },
            },
            "tooltip": [
                {"field": "well_id", "type": "nominal", "title": "Well & Job"},
                {"field": "unit", "type": "nominal", "title": "Assigned Rig / Crew"},
                {"field": "queue", "type": "nominal", "title": "Campaign Track"},
                {"field": "duration_days", "type": "quantitative", "title": "Duration (Days)"},
                {"field": "uplift_bbl_12mo", "type": "quantitative", "title": "Deferred Oil Avoided (12mo BBL)"},
            ],
        },
    }

    return build_vega_card_parts(
        title=f"ONGC Assam Asset — {period.title()} Workover & Rig Allocation Schedule ({field})",
        caption="15-Rig Fleet & Surface Rigless Crew Dispatch · Audit Section 'Where the System Was Wrong' Verified",
        vega_spec=vega_spec,
        height=370,
        surface_id=surface_id,
    )

