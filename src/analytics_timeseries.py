from __future__ import annotations

"""
- Ежедневные ряды: создано сделок, звонков, конверсия сделок (%).
- Ежедневные закрытия.
- Распределение time-to-close (дней).
"""

from pathlib import Path
from typing import Tuple, Optional, Dict

import numpy as np
import pandas as pd

try:
    from .io import CLEAN_DIR  # type: ignore
except Exception:
    CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"


def _load_table(name: str) -> pd.DataFrame:
    """
    Загружает таблицу из data/clean: сперва Parquet, затем CSV (если паркет недоступен).
    """
    base = Path(CLEAN_DIR)
    p_parquet = base / f"{name}.parquet"
    if p_parquet.exists():
        try:
            return pd.read_parquet(p_parquet)
        except Exception:
            pass
    p_csv = base / f"{name}.csv"
    if p_csv.exists():
        return pd.read_csv(p_csv)
    raise FileNotFoundError(f"Не найден файл для набора {name} в {base}")


def load_deals_calls() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Загрузить Deals/Calls из data/clean (Parquet) и привести даты.
    """
    deals = _load_table("Deals").rename(columns={
        "Created Time": "created_time",
        "Closing Date": "closing_date",
    })
    calls = _load_table("Calls").rename(columns={
        "Call Start Time": "call_start_time",
    })
    deals["created_time"] = pd.to_datetime(deals["created_time"], errors="coerce")
    deals["closing_date"] = pd.to_datetime(deals["closing_date"], errors="coerce")
    calls["call_start_time"] = pd.to_datetime(calls["call_start_time"], errors="coerce")
    return deals, calls


def make_daily_series(deals: pd.DataFrame, calls: pd.DataFrame) -> pd.DataFrame:
    """
    Ежедневные counts: deals_created, calls_total и конверсия сделок (%).
    """
    deals_daily = (
        deals.set_index("created_time").resample("D").size().rename("deals_created").reset_index()
    ).rename(columns={"created_time": "date"})
    calls_daily = (
        calls.set_index("call_start_time").resample("D").size().rename("calls_total").reset_index()
    ).rename(columns={"call_start_time": "date"})
    daily = pd.merge(deals_daily, calls_daily, on="date", how="outer").fillna(0)
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["deal_rate_pct"] = np.where(
        daily["calls_total"] > 0,
        (daily["deals_created"] / daily["calls_total"]) * 100.0,
        np.nan,
    )
    return daily


def make_closed_daily(deals: pd.DataFrame, upper: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Ежедневные закрытия; отбрасываем аномалии closing_date < created_time.
    Если указана верхняя граница `upper`, дополнительно фильтруем даты > upper.
    """
    # Берём только записи, где обе даты заданы
    valid = deals.dropna(subset=["closing_date", "created_time"]).copy()
    # Отбрасываем технически невозможные случаи: закрытие раньше создания
    valid = valid[valid["closing_date"] >= valid["created_time"]]

    cd = (
        valid.set_index("closing_date").resample("D").size()
        .rename("deals_closed").reset_index()
    )
    if upper is not None:
        cd = cd[cd["closing_date"] <= upper]
    return cd


def make_ttc_series(deals: pd.DataFrame) -> pd.Series:
    """
    Серия валидных значений time-to-close (дни, >=0).
    """
    ttc = (deals["closing_date"] - deals["created_time"]).dt.total_seconds() / 86400.0
    valid = ttc.dropna()
    return valid[valid >= 0]



def calls_duration_stats(calls: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    Быстрая сводка по длительности звонков (в секундах и минутах): медиана и 90-й перцентиль.
    Ищет колонку по подстроке 'duration'. Возвращает None, если колонка не найдена или нет данных.
    """
    dur_col = None
    for c in calls.columns:
        if "duration" in str(c).lower():
            dur_col = c
            break
    if dur_col is None:
        return None
    dur = pd.to_numeric(calls[dur_col], errors="coerce").dropna()
    dur = dur[dur >= 0]
    if dur.empty:
        return None
    med_s = float(dur.median())
    p90_s = float(dur.quantile(0.90))
    return {
        "med_s": med_s,
        "p90_s": p90_s,
        "med_m": med_s / 60.0,
        "p90_m": p90_s / 60.0,
        "n": float(len(dur)),
    }


def ttc_hist_counts(valid: pd.Series,
                    bins: Optional[list] = None,
                    labels: Optional[list] = None) -> pd.Series:
    """
    Подсчёт распределения time-to-close по корзинам. Значения - количество сделок на корзину.
    0-3, 4-7, 8-14, 15-30, 31-60, 61-120, 121-365.
    """
    if valid is None or valid.empty:
        return pd.Series(dtype="int64")
    if bins is None:
        bins = [-0.001, 3, 7, 14, 30, 60, 120, 365]
    if labels is None:
        labels = ["0-3", "4-7", "8-14", "15-30", "31-60", "61-120", "121-365"]
    binned = pd.cut(valid, bins=bins, labels=labels, include_lowest=True, right=True)
    return binned.value_counts().sort_index()


def overall_period_and_conversion(daily: pd.DataFrame) -> Optional[Dict[str, object]]:
    """
    Подсчёт периода данных и общей конверсии сделок ~ 100 * sum(deals_created) / sum(calls_total).
    Возвращает None при пустом daily.
    """
    if daily is None or daily.empty:
        return None
    date_from = pd.to_datetime(daily["date"]).min().date()
    date_to = pd.to_datetime(daily["date"]).max().date()
    deals_sum = int(daily["deals_created"].sum())
    calls_sum = int(daily["calls_total"].sum())
    conv_overall = float(deals_sum / calls_sum * 100.0) if calls_sum > 0 else float("nan")
    return {
        "date_from": date_from,
        "date_to": date_to,
        "deals_sum": deals_sum,
        "calls_sum": calls_sum,
        "conv_overall": conv_overall,
    }




