"""
tools/arps_decline.py

Implements TC-001: fit_decline_curve() per spec/04 §2.
"""

from dataclasses import dataclass
from datetime import date, timedelta
import time
import numpy as np
from scipy.optimize import curve_fit
from tools.common import (
    Confidence,
    ToolResult,
    ToolStatus,
    WellId,
    build_provenance,
    load_table,
)


@dataclass(frozen=True)
class DeclineFit:
    well_id: WellId
    qi_bopd: float
    b: float
    di_per_day: float
    r_squared: float
    n_points: int
    n_tested_points: int
    expected_bopd: float
    actual_bopd: float
    residual_pct: float
    residual_series: list[tuple[date, float]]
    fit_quality: Confidence
    basis_changes: list[date]
    allocation_note: str | None


def _arps_hyperbolic(t: np.ndarray, qi: float, b: float, di: float) -> np.ndarray:
    b_safe = np.maximum(b, 1e-5)
    return qi / np.power(1.0 + b_safe * di * t, 1.0 / b_safe)


def fit_decline_curve(
    well_id: WellId,
    as_of: date = date(2026, 9, 23),
    lookback_months: int = 36,
    min_producing_days: int = 180,
) -> ToolResult:
    t0 = time.perf_counter()
    params = {
        "well_id": well_id,
        "as_of": str(as_of),
        "lookback_months": lookback_months,
        "min_producing_days": min_producing_days,
    }

    wells = load_table("well_master")
    if well_id not in set(wells["well_id"]):
        return ToolResult(
            status=ToolStatus.UNAVAILABLE,
            value=None,
            missing_fields=["well_id"],
            message=f"Well {well_id} not found in well_master.",
            provenance=build_provenance("TC-001", params, t0),
        )

    daily = load_table("daily_production")
    workovers = load_table("workover_history")

    start_cutoff = as_of - timedelta(days=int(lookback_months * 30.4375))
    df_w = daily[
        (daily["well_id"] == well_id)
        & (daily["production_date"] >= start_cutoff)
        & (daily["production_date"] <= as_of)
    ].sort_values("production_date")

    # Exclude non-producing days (DC-014: NULL is not zero)
    df_prod = df_w[df_w["is_producing"] == True].copy()
    if len(df_prod) < min_producing_days:
        return ToolResult(
            status=ToolStatus.INSUFFICIENT_HISTORY,
            value=None,
            missing_fields=[],
            message=f"Well {well_id} has {len(df_prod)} producing days (< {min_producing_days} required).",
            provenance=build_provenance("TC-001", params, t0),
        )

    # Exclude 30 days following any workover end_date
    wo_w = workovers[(workovers["well_id"] == well_id) & (workovers["is_censored"] == False)]
    for _, w_row in wo_w.iterrows():
        if w_row["end_date"] is not None:
            transient_end = w_row["end_date"] + timedelta(days=30)
            df_prod = df_prod[
                ~((df_prod["production_date"] >= w_row["end_date"]) & (df_prod["production_date"] <= transient_end))
            ]

    if len(df_prod) < min_producing_days:
        return ToolResult(
            status=ToolStatus.INSUFFICIENT_HISTORY,
            value=None,
            missing_fields=[],
            message=f"Insufficient post-transient producing history for {well_id}.",
            provenance=build_provenance("TC-001", params, t0),
        )

    first_date = df_prod["production_date"].iloc[0]
    t_all = np.array([(d - first_date).days for d in df_prod["production_date"]], dtype=float)
    q_all = df_prod["oil_rate_bopd"].astype(float).to_numpy()
    sources = df_prod["data_source"].to_numpy()

    # Fit on pre-anomaly baseline (exclude trailing 60d so recent failure drop doesn't pull the curve down)
    baseline_mask = t_all <= max(120.0, t_all[-1] - 65.0)
    t_fit = t_all[baseline_mask]
    q_fit = q_all[baseline_mask]
    src_fit = sources[baseline_mask]

    # Weights per DP-001: TESTED=3.0, ALLOCATED=1.0, ESTIMATED=0.5
    sigma = np.where(src_fit == "TESTED", 1.0 / 3.0, np.where(src_fit == "ALLOCATED", 1.0, 2.0))

    try:
        popt, _ = curve_fit(
            _arps_hyperbolic,
            t_fit,
            q_fit,
            p0=[float(np.percentile(q_fit[:15], 75)), 0.68, 0.0003],
            bounds=([2.0, 0.0, 1e-5], [400.0, 2.0, 0.01]),
            sigma=sigma,
            maxfev=5000,
        )
        qi_fit, b_fit, di_fit = float(popt[0]), float(popt[1]), float(popt[2])
    except Exception:
        qi_fit = float(np.mean(q_fit[:15]))
        b_fit = 0.0
        di_fit = 0.00025

    q_pred_fit = _arps_hyperbolic(t_fit, qi_fit, b_fit, di_fit)
    ss_res = float(np.sum((q_fit - q_pred_fit) ** 2))
    ss_tot = float(np.sum((q_fit - np.mean(q_fit)) ** 2))
    r2 = max(0.0, min(0.99, 1.0 - (ss_res / max(ss_tot, 1e-6))))

    t_as_of = float((as_of - first_date).days)
    expected_bopd = round(float(_arps_hyperbolic(np.array([t_as_of]), qi_fit, b_fit, di_fit)[0]), 1)
    actual_bopd = round(float(np.mean(q_all[-7:])), 1)
    residual_pct = round(((actual_bopd - expected_bopd) / max(expected_bopd, 0.1)) * 100.0, 1)

    n_tested_total = int((sources == "TESTED").sum())
    trailing_90_cutoff = as_of - timedelta(days=90)
    df_90 = df_prod[df_prod["production_date"] >= trailing_90_cutoff]
    n_tested_90 = int((df_90["data_source"] == "TESTED").sum())

    allocation_note = None
    if r2 < 0.50:
        fit_qual = Confidence.LOW
        status = ToolStatus.LOW_CONFIDENCE
    elif n_tested_90 == 0:
        fit_qual = Confidence.MEDIUM
        status = ToolStatus.OK
        allocation_note = (
            f"No TESTED separator measurements for {well_id} in trailing 90 days; "
            "intervening rates are GGS-allocated, so severity is capped at FLAG."
        )
    else:
        fit_qual = Confidence.HIGH
        status = ToolStatus.OK

    # Build trailing 30-day residual series
    res_series = []
    for d_val, q_val, t_val in zip(df_prod["production_date"].iloc[-30:], q_all[-30:], t_all[-30:]):
        exp_v = float(_arps_hyperbolic(np.array([t_val]), qi_fit, b_fit, di_fit)[0])
        res_v = round(((float(q_val) - exp_v) / max(exp_v, 0.1)) * 100.0, 1)
        res_series.append((d_val, res_v))

    fit_obj = DeclineFit(
        well_id=well_id,
        qi_bopd=round(qi_fit, 1),
        b=round(b_fit, 2),
        di_per_day=round(di_fit, 5),
        r_squared=round(r2, 2),
        n_points=int(len(df_prod)),
        n_tested_points=n_tested_total,
        expected_bopd=expected_bopd,
        actual_bopd=actual_bopd,
        residual_pct=residual_pct,
        residual_series=res_series,
        fit_quality=fit_qual,
        basis_changes=[],
        allocation_note=allocation_note,
    )

    return ToolResult(
        status=status,
        value=fit_obj,
        missing_fields=[],
        message=f"Arps fit for {well_id}: expected {expected_bopd} BOPD, actual {actual_bopd} BOPD ({residual_pct:+.1f}%).",
        provenance=build_provenance("TC-001", params, t0),
    )
