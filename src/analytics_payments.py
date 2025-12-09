from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

try:
    from .io import CLEAN_DIR  # type: ignore
except Exception:
    CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"


def load_deals_for_payments() -> pd.DataFrame:
    """
    Загружает очищенные сделки и добавляет поля для анализа платежей.
    """
    base = Path(CLEAN_DIR)
    parquet_path = base / "Deals.parquet"
    csv_path = base / "Deals.csv"

    if parquet_path.exists():
        deals = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        deals = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Не найден файл Deals в директории {base}")

    deals["Created Time"] = pd.to_datetime(deals["Created Time"], errors="coerce")
    deals["Closing Date"] = pd.to_datetime(deals["Closing Date"], errors="coerce")
    deals["month"] = deals["Created Time"].dt.to_period("M").astype("string")
    return _add_status_flags(deals)


def _add_status_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет булевые признаки статуса сделки: is_paid, is_closed, is_lost.
    """
    result = df.copy()
    stage_str = result["Stage"].astype("string")

    result["is_paid"] = stage_str.str.contains("payment done", case=False, na=False)
    result["is_closed"] = result["Closing Date"].notna()
    result["is_lost"] = stage_str.str.contains("lost", case=False, na=False)
    result.loc[result["is_paid"], "is_lost"] = False
    return result


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """
    Безопасное деление столбцов (деление на ноль заменяем на 0).
    """
    return num.div(den.replace(0, np.nan)).fillna(0.0)


def payment_product_metrics(
    deals: pd.DataFrame,
    month: Optional[str] = None,
    target_products: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Возвращает агрегаты по типу оплаты, продукту и типу обучения.
    """
    df = deals.copy()
    if month:
        df = df[df["month"] == month]
    if target_products:
        df = df[df["Product"].isin(target_products)]

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Payment Type",
                "Product",
                "Education Type",
                "n_deals",
                "n_paid",
                "n_lost",
                "revenue_total",
                "cr_deals_to_paid",
                "lost_rate",
            ]
        )

    df["Offer Total Amount"] = pd.to_numeric(df["Offer Total Amount"], errors="coerce").fillna(0.0)

    grouped = (
        df.groupby(["Payment Type", "Product", "Education Type"], dropna=False)
        .agg(
            n_deals=("Id", "count"),
            n_paid=("is_paid", "sum"),
            n_lost=("is_lost", "sum"),
            revenue_total=("Offer Total Amount", "sum"),
        )
        .reset_index()
    )
    grouped["cr_deals_to_paid"] = _safe_div(grouped["n_paid"], grouped["n_deals"])
    grouped["lost_rate"] = _safe_div(grouped["n_lost"], grouped["n_deals"])
    return grouped
