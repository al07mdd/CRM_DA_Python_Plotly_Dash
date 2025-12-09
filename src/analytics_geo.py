from __future__ import annotations

"""
Гео‑утилиты:
- загрузка сделок и координат городов;
- нормализация уровня немецкого (A/B/C 0–2, с учетом кириллицы);
- агрегаты по городам (deals, paid, win_rate) и по выбранному уровню.
"""

from pathlib import Path
import re
from typing import Optional

import pandas as pd

try:
    from .io import CLEAN_DIR, TEMP_DIR  # type: ignore
except Exception:  # pragma: no cover - fallback for standalone runs
    BASE_DIR = Path(__file__).resolve().parents[1]
    CLEAN_DIR = BASE_DIR / "data" / "clean"
    TEMP_DIR = BASE_DIR / "data" / "temp"

DEALS_FILE = Path(CLEAN_DIR) / "Deals.parquet"
CITY_COORDS_FILE = Path(TEMP_DIR) / "city_coords.parquet"

LAT_MIN, LAT_MAX = 47.0, 55.5
LON_MIN, LON_MAX = 5.0, 16.5

MANUAL_COORDS = {
    "Berlin": (52.5200, 13.4050),
    "München": (48.1374, 11.5755),
    "Hamburg": (53.5511, 9.9937),
    "Leipzig": (51.3397, 12.3731),
    "Nürnberg": (49.4521, 11.0767),
    "Düsseldorf": (51.2277, 6.7735),
    "Dresden": (51.0504, 13.7373),
    "Köln": (50.9375, 6.9603),
    "Frankfurt": (50.1109, 8.6821),
    "Dortmund": (51.5136, 7.4653),
    "Duisburg": (51.4344, 6.7623),
    "Mannheim": (49.4875, 8.4660),
    "Karlsruhe": (49.0069, 8.4037),
    "Essen": (51.4556, 7.0116),
    "Bremen": (53.0793, 8.8017),
    "Oberhausen": (51.4963, 6.8638),
    "Braunschweig": (52.2689, 10.5268),
    "Stuttgart": (48.7758, 9.1829),
    "Bochum": (51.4818, 7.2162),
    "Aachen": (50.7753, 6.0839),
    "Hannover": (52.3759, 9.7320),
    "Augsburg": (48.3705, 10.8978),
    "Ulm": (48.4011, 9.9876),
    "Lübeck": (53.8655, 10.6866),
    "Kassel": (51.3127, 9.4797),
}


def normalize_level(val) -> Optional[str]:
    """
    Привести текст уровня к формату A/B/C0-2, учитывая кириллицу.
    """
    if pd.isna(val):
        return None
    text = str(val).strip()
    text = re.sub(r"[Аа]", "A", text)
    text = re.sub(r"[ВвБб]", "B", text)
    text = re.sub(r"[Сс]", "C", text)
    text = text.upper().replace(" ", "")
    match = re.search(r"[ABC][0-2]", text)
    return match.group() if match else None


def _read_deals_table() -> pd.DataFrame:
    """
    Загружает Deals из data/clean: приоритет Parquet, затем CSV.
    """
    if DEALS_FILE.exists():
        try:
            return pd.read_parquet(DEALS_FILE)
        except Exception:
            pass
    csv_path = DEALS_FILE.with_suffix(".csv")
    if csv_path.exists():
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"Не найден файл Deals в {DEALS_FILE.parent}")


def load_deals() -> pd.DataFrame:
    """
    Загрузить сделки, добавить success и нормализованный уровень языка.
    """
    deals = _read_deals_table()
    deals = deals.rename(columns={"Level of Deutsch": "level_raw"})
    deals["success"] = deals["Stage"].eq("payment done") & deals["City"].notna() & deals["City"].ne("-")
    deals["level_norm"] = deals["level_raw"].map(normalize_level)
    return deals


def load_city_coords() -> pd.DataFrame:
    """
    Загрузить координаты городов из кэша в data/temp.
    """
    expected = ["City", "lat", "lon"]
    frames = []
    if CITY_COORDS_FILE.exists():
        coords = pd.read_parquet(CITY_COORDS_FILE)
        if set(expected).issubset(coords.columns):
            frames.append(coords[expected])
    manual_df = (
        pd.DataFrame.from_dict(MANUAL_COORDS, orient="index", columns=["lat", "lon"])
        .reset_index()
        .rename(columns={"index": "City"})
    )
    frames.append(manual_df)
    if not frames:
        return pd.DataFrame(columns=expected)
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.dropna(subset=["lat", "lon"]).drop_duplicates(subset="City", keep="first")
    return merged


def city_options(deals: pd.DataFrame) -> list[str]:
    """
    Уникальные нормализованные уровни для выпадающих списков.
    """
    levels = deals["level_norm"].dropna().unique().tolist()
    return sorted(levels)


def _filter_bbox(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    return df[
        df["lat"].between(LAT_MIN, LAT_MAX)
        & df["lon"].between(LON_MIN, LON_MAX)
    ]


def make_city_summary(deals: pd.DataFrame, coords: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегаты по городам: сделки, оплаты, win_rate + координаты (bbox DE).
    """
    if deals is None or deals.empty or coords is None or coords.empty:
        return pd.DataFrame(columns=["City", "deals", "paid", "win_rate", "lat", "lon"])
    base = deals.loc[deals["City"].notna() & deals["City"].ne("-"), ["City", "success"]]
    agg = (
        base.groupby("City")
        .agg(deals=("success", "size"), paid=("success", "sum"))
        .reset_index()
    )
    agg["win_rate"] = agg["paid"] / agg["deals"]
    merged = agg.merge(coords, on="City", how="inner")
    return _filter_bbox(merged)


def make_level_city_summary(deals: pd.DataFrame, coords: pd.DataFrame, level: Optional[str]) -> pd.DataFrame:
    """
    Агрегаты по городам для выбранного уровня языка.
    """
    if level is None:
        return pd.DataFrame(columns=["City", "deals", "paid", "win_rate", "lat", "lon"])
    subset = deals.loc[
        deals["City"].notna() & deals["City"].ne("-") & deals["level_norm"].eq(level),
        ["City", "success"],
    ]
    if subset.empty or coords is None or coords.empty:
        return pd.DataFrame(columns=["City", "deals", "paid", "win_rate", "lat", "lon"])
    agg = (
        subset.groupby("City")
        .agg(deals=("success", "size"), paid=("success", "sum"))
        .reset_index()
    )
    agg["win_rate"] = agg["paid"] / agg["deals"]
    merged = agg.merge(coords, on="City", how="inner")
    return _filter_bbox(merged)
