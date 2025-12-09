from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from .io import CLEAN_DIR  # type: ignore
except Exception:
    CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"


def _load_table(name: str) -> pd.DataFrame:
    """
    Загружает parquet/csv по имени файла из каталога с очищенными данными.
    """
    base = Path(CLEAN_DIR)
    parquet_path = base / f"{name}.parquet"
    if parquet_path.exists():
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            pass
    csv_path = base / f"{name}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"Не найден файл для набора {name} в {base}")


def load_deals_calls() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Читает Deals/Calls и приводит к удобным названиям/типам.
    """
    deals = _load_table("Deals").rename(
        columns={
            "Id": "deal_id",
            "Created Time": "created_time",
            "Closing Date": "closing_date",
            "Stage": "stage",
            "Offer Total Amount": "offer_total",
            "Initial Amount Paid": "initial_amount",
            "Deal Owner Name": "deal_owner",
            "Contact Name": "contact_id",
            "Lost Reason": "lost_reason",
        }
    )
    calls = _load_table("Calls").rename(
        columns={
            "Id": "call_id",
            "Call Start Time": "call_start_time",
            "Call Duration (in seconds)": "call_duration",
            "CONTACTID": "contact_id",
        }
    )

    deals["created_time"] = pd.to_datetime(deals["created_time"], errors="coerce")
    deals["closing_date"] = pd.to_datetime(deals["closing_date"], errors="coerce")
    calls["call_start_time"] = pd.to_datetime(calls["call_start_time"], errors="coerce")
    deals["month"] = deals["created_time"].dt.to_period("M").astype(str)
    return deals, calls


def _prepare_with_calls(deals: pd.DataFrame, calls: pd.DataFrame) -> pd.DataFrame:
    """
    Заполняет сделки агрегатами по звонкам и расчётными флагами/суммами.
    """
    valid_calls = calls.copy()
    valid_calls["call_duration"] = valid_calls["call_duration"].fillna(0)
    valid_calls = valid_calls[valid_calls["call_duration"] > 0]
    valid_calls = valid_calls[valid_calls["call_start_time"].notna()]

    calls_join = (
        deals[["deal_id", "contact_id", "created_time"]]
        .merge(
            valid_calls[["call_id", "contact_id", "call_start_time"]],
            on="contact_id",
            how="left",
        )
        .dropna(subset=["call_start_time", "created_time"])
    )
    calls_join = calls_join[calls_join["call_start_time"] >= calls_join["created_time"]]

    calls_by_deal = (
        calls_join.groupby("deal_id", dropna=False)
        .agg(
            calls_cnt=("call_id", "count"),
            first_call_time=("call_start_time", "min"),
        )
        .reset_index()
    )

    df = deals.merge(calls_by_deal, how="left", on="deal_id")
    df["calls_cnt"] = df["calls_cnt"].fillna(0)
    df["has_call"] = df["calls_cnt"] > 0

    df["is_paid"] = df["stage"].str.lower().str.contains("payment done", na=False)
    df["is_closed"] = df["closing_date"].notna()
    df["is_lost"] = df["stage"].str.lower().str.contains("lost", na=False)
    df.loc[df["is_paid"], "is_lost"] = False

    df["offer_total"] = df["offer_total"].fillna(0)
    df["initial_amount"] = df["initial_amount"].fillna(0)
    df["revenue_manager"] = np.where(df["is_paid"], df["offer_total"], 0.0)

    # SLA берем напрямую из Deals (значения уже переведены в часы при очистке).
    df["lead_to_first_call_hours"] = pd.to_numeric(df.get("SLA"), errors="coerce")

    df["is_processed"] = df["is_closed"] | df["has_call"]
    return df

def owner_metrics(
    deals: pd.DataFrame,
    calls: pd.DataFrame,
    month: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Возвращает агрегаты по менеджерам и причинам потерь (опционально фильтр по месяцу).
    """
    df = _prepare_with_calls(deals, calls)
    if month:
        df = df[df["month"] == month]

    def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
        return num.div(den.replace(0, np.nan)).fillna(0)

    owners = (
        df.groupby("deal_owner", dropna=False)
        .agg(
            n_deals=("deal_id", "count"),
            n_processed=("is_processed", "sum"),
            n_closed=("is_closed", "sum"),
            n_paid=("is_paid", "sum"),
            n_lost=("is_lost", "sum"),
            revenue_won=("revenue_manager", "sum"),
            calls_cnt_total=("calls_cnt", "sum"),
            n_processed_with_calls=("has_call", "sum"),
            avg_lead_to_first_call_hours=("lead_to_first_call_hours", "mean"),
        )
        .reset_index()
    )

    owners["cr_deals_to_paid"] = safe_div(owners["n_paid"], owners["n_deals"])
    owners["cr_processed_to_paid"] = safe_div(owners["n_paid"], owners["n_processed"])
    owners["revenue_per_paid"] = safe_div(owners["revenue_won"], owners["n_paid"])
    owners["revenue_per_deal"] = safe_div(owners["revenue_won"], owners["n_deals"])
    owners["calls_cnt_per_processed"] = safe_div(
        owners["calls_cnt_total"], owners["n_processed"]
    )
    owners["calls_coverage"] = safe_div(
        owners["n_processed_with_calls"], owners["n_processed"]
    )
    owners["lost_rate_by_closed"] = safe_div(owners["n_lost"], owners["n_processed"])
    owners["lost_rate_by_all"] = safe_div(owners["n_lost"], owners["n_deals"])

    lost = df[df["is_lost"]].copy()
    lost_reason_by_owner = (
        lost.groupby(["deal_owner", "lost_reason"], dropna=False)
        .agg(n_lost=("deal_id", "count"))
        .reset_index()
    )
    if len(lost_reason_by_owner):
        lost_reason_by_owner["n_lost_total_owner"] = (
            lost_reason_by_owner.groupby("deal_owner")["n_lost"].transform("sum")
        )
        lost_reason_by_owner["share_owner_lost"] = safe_div(
            lost_reason_by_owner["n_lost"], lost_reason_by_owner["n_lost_total_owner"]
        )
    else:
        lost_reason_by_owner["n_lost_total_owner"] = 0
        lost_reason_by_owner["share_owner_lost"] = 0.0

    return {"owners": owners, "lost_reason_by_owner": lost_reason_by_owner}
