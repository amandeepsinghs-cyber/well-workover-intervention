"""
tools/common.py

Shared data structures, enums, and cached landing-table loader for all 18 deterministic tool contracts (spec/04).
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import date
from enum import Enum
from typing import Any, Literal
import pandas as pd

WellId = str
JobCode = str
Bopd = float
Blpd = float
KgCm2 = float
Metres = float
Days = float

LANDING_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "landing")
GEODATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "geodata")
CONFIG_VERSION = "1.0.0-geleki"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ToolStatus(str, Enum):
    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    DISCRIMINATOR_UNAVAILABLE = "DISCRIMINATOR_UNAVAILABLE"


class WaterMechanism(str, Enum):
    CONING = "CONING"
    CHANNELLING = "CHANNELLING"
    MULTILAYER = "MULTILAYER"
    NORMAL = "NORMAL_DISPLACEMENT"
    INDETERMINATE = "INDETERMINATE"
    INJECTOR_BREAKTHROUGH = "INJECTOR_BREAKTHROUGH"
    CHANNELLING_OR_INJECTOR = "CHANNELLING_OR_INJECTOR_BREAKTHROUGH"


class OffsetVerdict(str, Enum):
    WELL_SPECIFIC = "WELL_SPECIFIC"
    RESERVOIR_DECLINE = "RESERVOIR_DECLINE"
    MIXED = "MIXED"
    INSUFFICIENT = "INSUFFICIENT"


class MechSignature(str, Enum):
    PUMP_WEAR = "PUMP_WEAR"
    TUBING_LEAK = "TUBING_LEAK"
    WAX = "WAX"
    SCALE = "SCALE"
    ROD_PART = "ROD_PART"
    GAS_INTERFERENCE = "GAS_INTERFERENCE"
    NONE = "NONE"


@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    value: Any | None
    missing_fields: list[str]
    message: str
    provenance: dict


_TABLE_CACHE: dict[str, pd.DataFrame] = {}


def load_table(name: str) -> pd.DataFrame:
    if name not in _TABLE_CACHE:
        path = os.path.join(LANDING_DIR, f"{name}.parquet")
        df = pd.read_parquet(path)
        for col in df.columns:
            if "date" in col:
                df[col] = pd.to_datetime(df[col]).dt.date
        _TABLE_CACHE[name] = df
    return _TABLE_CACHE[name]


def build_provenance(tool_id: str, params: dict, t0: float) -> dict:
    payload = json.dumps(params, default=str, sort_keys=True)
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return {
        "tool_id": tool_id,
        "input_hash": h,
        "config_version": CONFIG_VERSION,
        "duration_ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }
