"""
tests/test_contracts.py

Automated acceptance test suite covering:
  - Gate C Data Contract Invariants (DC-001..DC-084, AT-092)
  - Stage B Map Renderer (TC-016, AT-101..AT-106)
  - Stage D Analytical Tool Contracts (TC-001..TC-018, AT-001..AT-112)
  - Stage E Survival Model Honesty Gate (MS-100..MS-102)
  - Stage F Agent Orchestrator 4-turn flow (AS-010..AS-014)
"""

from datetime import date
import json
import os
import time

from agent import root_agent
from generator.validate import validate_all
from tools import (
    OffsetVerdict,
    ToolStatus,
    WaterMechanism,
    chan_diagnostic,
    check_mro,
    check_offsets,
    fillage_proxy,
    fit_decline_curve,
    generate_draft_plan,
    generate_report,
    plot_production,
    query_wells,
    rank_candidates,
    render_well_map,
    route_intervention,
    search_well_history,
)


def test_gate_c_data_invariants():
    assert validate_all() is True


def test_tc016_render_well_map():
    t0 = time.perf_counter()
    res = render_well_map(field="Geleki", as_of=date(2026, 9, 23))
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert res.status == ToolStatus.OK
    assert res.value.n_rendered == 142
    assert res.value.render_tier == "TIER_1_VEGA_GEOSHAPE"
    # Shut-in wells must have size_value=None (TC-016.3)
    shutin_points = [p for p in res.value.points if p.colour_key == "SHUT_IN"]
    assert len(shutin_points) > 0
    assert all(p.size_value is None for p in shutin_points)

    # AT-105: Non-Geleki field must return UNAVAILABLE
    bad = render_well_map(field="Lakwa", as_of=date(2026, 9, 23))
    assert bad.status == ToolStatus.UNAVAILABLE
    assert "field:Lakwa" in bad.missing_fields


def test_tc001_arps_decline_fit():
    res = fit_decline_curve("GK-129", as_of=date(2026, 9, 23))
    assert res.status == ToolStatus.OK
    assert res.value.residual_pct < -25.0


def test_tc002_chan_sign_convention_canary():
    # GK-129: positive WOR' slope -> CHANNELLING
    r129 = chan_diagnostic("GK-129", as_of=date(2026, 9, 23))
    assert r129.status == ToolStatus.OK
    assert r129.value.wor_prime_slope > 0.30
    assert r129.value.mechanism == WaterMechanism.CHANNELLING
    assert r129.value.discriminating_evidence is not None

    # GK-103: negative WOR' slope -> CONING (AT-030d canary: never CHANNELLING)
    r103 = chan_diagnostic("GK-103", as_of=date(2026, 9, 23))
    assert r103.status == ToolStatus.OK
    assert r103.value.wor_prime_slope < -0.10
    assert r103.value.mechanism == WaterMechanism.CONING

    # GK-117: paired injector step -> INJECTOR_BREAKTHROUGH
    r117 = chan_diagnostic("GK-117", as_of=date(2026, 9, 23))
    assert r117.value.mechanism == WaterMechanism.INJECTOR_BREAKTHROUGH

    # GK-141: ambiguous two injectors -> CHANNELLING_OR_INJECTOR_BREAKTHROUGH
    r141 = chan_diagnostic("GK-141", as_of=date(2026, 9, 23))
    assert r141.value.mechanism == WaterMechanism.CHANNELLING_OR_INJECTOR


def test_tc003_fillage_proxy_gk055():
    r055 = fillage_proxy("GK-055", as_of=date(2026, 9, 23))
    assert r055.status == ToolStatus.OK
    assert r055.value.theoretical_displacement_blpd == 78.5
    assert r055.value.actual_liquid_blpd == 51.2
    assert r055.value.gap_blpd == 27.3
    assert r055.value.volumetric_efficiency_pct == 65.2


def test_tc004_and_tc008_refusal_gk141():
    off_141 = check_offsets("GK-141", as_of=date(2026, 9, 23))
    assert off_141.status == ToolStatus.OK
    assert off_141.value.verdict == OffsetVerdict.RESERVOIR_DECLINE

    route_141 = route_intervention("GK-141", "CHANNELLING", off_141.value.verdict)
    assert route_141.value.job_code == "NO_JOB_JUSTIFIED"
    assert route_141.value.queue == "NONE"


def test_tc010_tc011_tc012_tc013():
    queues = rank_candidates(field="Geleki", as_of=date(2026, 9, 23)).value
    assert len(queues.rig_queue) == 3
    assert len(queues.rigless_queue) == 3
    assert any(w == "GK-141" for w, _, _ in queues.excluded_refusals)

    mro = check_mro("WSO_SQUEEZE", required_date=date(2026, 9, 25)).value
    assert mro["alternate_base"] == "SIVASAGAR"
    assert mro["transit_days"] == 2

    docs = search_well_history("GK-129").value
    assert len(docs) == 2
    assert any("2019" in d.title for d in docs)

    plan = generate_draft_plan("GK-129", run_date=date(2026, 9, 23)).value
    assert plan["approval_status"] == "AWAITING REVIEW"


def test_tc017_and_tc018_pushback_caveat():
    ps = plot_production("GK-129").value
    assert ps.n_producing_days > 900
    assert any(m.outcome == "FAILED" for m in ps.interventions)

    # AT-112b: order_by='oil_rate_bopd' must always populate caveat
    q_abs = query_wells(order_by="oil_rate_bopd", direction="ASC", limit=5).value
    assert q_abs.caveat is not None and len(q_abs.caveat) > 20

    q_res = query_wells(order_by="decline_residual_pct", direction="ASC", limit=5).value
    assert q_res.caveat is None


def test_stage_e_survival_model_metrics():
    metrics_path = os.path.join("model", "survival_model_metrics.json")
    assert os.path.exists(metrics_path)
    with open(metrics_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert 0.65 <= m["holdout_c_index"] <= 0.72
    assert m["holdout_c_index"] > m["trigger_b_c_index"]
    assert m["gates_passed"] is True


def test_stage_f_agent_4_turns():
    from google.adk.agents import Agent
    assert isinstance(root_agent, Agent)
    assert root_agent.name == "geleki_workover_intervention_agent"
    assert len(root_agent.tools) == 19
    t1 = root_agent.execute_demo_turn_1_map()
    t2 = root_agent.execute_demo_turn_2_pushback()
    t3 = root_agent.execute_demo_turn_3_candidates()
    t4 = root_agent.execute_demo_turn_4_reports()
    assert t1["result"]["value"]["n_rendered"] == 142
    assert t2["caveat"] is not None
    assert len(t3["tool_trace"]) == 10
    assert "where_the_system_was_wrong" in t4["monthly"]["value"]


def test_a2ui_v09_surfaces():
    from agent.adk_tools import adk_open_google_maps, adk_plot_production, adk_render_well_map
    from agent.agent import emit_a2ui_surface

    # 1. Test 1 Map A2UI surface emission & coordinate bounding-box check
    adk_render_well_map(field="Geleki")
    map_content = emit_a2ui_surface()
    assert map_content is not None
    assert len(map_content.parts) == 3
    for p in map_content.parts:
        raw = p.inline_data.data.decode("utf-8")
        assert raw.startswith("<a2a_datapart_json>")
        assert raw.endswith("</a2a_datapart_json>")
        assert '"mimeType":"application/json+a2ui"' in raw
        inner = json.loads(raw.split("<a2a_datapart_json>")[1].split("</a2a_datapart_json>")[0])
        if "updateDataModel" in inner["data"]:
            assert len(raw) < 95000, f"updateDataModel payload too large ({len(raw)} bytes > 95 KB)"
            spec = inner["data"]["updateDataModel"]["value"]["spec"]
            wells = spec["data"]["values"]
            assert len(wells) == 142
            assert spec["layer"][0]["mark"]["type"] == "image"
            assert spec["layer"][0]["encoding"]["x2"]["field"] == "lon_max"
            assert spec["layer"][0]["encoding"]["y2"]["field"] == "lat_min"
            lon_dom = spec["layer"][0]["encoding"]["x"]["scale"]["domain"]
            lat_dom = spec["layer"][0]["encoding"]["y"]["scale"]["domain"]
            for w in wells:
                assert lon_dom[0] <= w["lon"] <= lon_dom[1], f"Well {w['well_id']} lon {w['lon']} outside {lon_dom}"
                assert lat_dom[0] <= w["lat"] <= lat_dom[1], f"Well {w['well_id']} lat {w['lat']} outside {lat_dom}"
        if "updateComponents" in inner["data"]:
            comps = {c["id"]: c for c in inner["data"]["updateComponents"]["components"]}
            assert "card-sat-image" not in comps, "Duplicate static satellite image component must not be present"
            assert comps["card-column"]["children"] == ["card-title", "card-caption", "card-chart"]

    # 2. Test Turn 2 Multi-surface emission (Production Plot + Chan Diagnostic in one turn)
    from agent.adk_tools import adk_chan_diagnostic, adk_generate_report, adk_rank_candidates
    adk_plot_production(well_id="GK-129", months=36)
    adk_chan_diagnostic(well_id="GK-129")
    turn2_content = emit_a2ui_surface()
    assert turn2_content is not None
    assert len(turn2_content.parts) == 6  # 3 parts for production + 3 parts for chan

    # 3. Test Turn 3 Ranking A2UI surface emission
    adk_rank_candidates(field="Geleki")
    turn3_content = emit_a2ui_surface()
    assert turn3_content is not None
    assert len(turn3_content.parts) == 3

    # 4. Test Turn 4 Report & Schedule A2UI surface emission
    adk_generate_report(field="Geleki", period="MONTHLY")
    turn4_content = emit_a2ui_surface()
    assert turn4_content is not None
    assert len(turn4_content.parts) == 3

    # 5. Test Google Maps Dedicated Tool & A2UI Launch Card
    g_res = adk_open_google_maps(field="Geleki", well_id="GK-055")
    assert g_res["status"] == "SUCCESS"
    assert "https://www.google.com/maps/@" in g_res["google_maps_satellite_url"]
    assert g_res["well_metadata"]["well_id"] == "GK-055"
    gmaps_content = emit_a2ui_surface()
    assert gmaps_content is not None
    assert len(gmaps_content.parts) == 3
    for p in gmaps_content.parts:
        raw = p.inline_data.data.decode("utf-8")
        assert "<a2a_datapart_json>" in raw
        assert '"mimeType":"application/json+a2ui"' in raw
