# src/analytics_campaigns.py
"""
Утилиты для анализа эффективности кампаний/источников: загрузка очищенных данных,
агрегация Spend+Deals, расчёт метрик воронки и таблиц для дашборда.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "clean"


def _load_clean_table(name: str) -> pd.DataFrame:
    """
    Загружает таблицу из data/clean: предпочитает Parquet, при падении читает CSV.
    """
    p_parquet = DATA_DIR / f"{name}.parquet"
    if p_parquet.exists():
        try:
            return pd.read_parquet(p_parquet)
        except Exception:
            pass
    p_csv = DATA_DIR / f"{name}.csv"
    if p_csv.exists():
        return pd.read_csv(p_csv)
    raise FileNotFoundError(f"Не найден {name} в {DATA_DIR}")


def load_campaign_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Читает очищенные parquet Deals/Spend и приводит ключевые поля к единому виду.
    """
    deals = _load_clean_table("Deals")
    spend = _load_clean_table("Spend")

    deals = deals.rename(
        columns={
            "Id": "id",
            "Created Time": "created_time",
            "Closing Date": "closing_date",
            "Campaign": "campaign",
            "Source": "source",
            "Stage": "stage",
            "Initial Amount Paid": "initial_amount_paid",
            "Offer Total Amount": "offer_total_amount",
            "Term (AdGroup)": "adgroup",
        }
    )
    spend = spend.rename(
        columns={
            "Date": "date",
            "Campaign": "campaign",
            "Source": "source",
            "AdGroup": "adgroup",
            "Impressions": "impressions",
            "Clicks": "clicks",
            "Spend": "spend",
        }
    )

    # приведение типов и гарантия наличия ключей для джойна
    if "adgroup" not in deals.columns:
        deals["adgroup"] = ""
    if "adgroup" not in spend.columns:
        spend["adgroup"] = ""
    deals["adgroup"] = deals["adgroup"].fillna("").astype(str)
    spend["adgroup"] = spend["adgroup"].fillna("").astype(str)

    deals["campaign"] = deals["campaign"].fillna("").astype(str)
    deals["source"] = deals["source"].fillna("").astype(str)
    spend["campaign"] = spend["campaign"].fillna("").astype(str)
    spend["source"] = spend["source"].fillna("").astype(str)

    deals["is_paid"] = deals["stage"].str.lower().eq("payment done")
    # выручка считаем по Offer Total Amount только для оплативших
    deals["revenue_value"] = deals["offer_total_amount"].where(deals["is_paid"]).fillna(0)

    return deals, spend


def safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """
    Безопасное деление: приводит к числам, делит и возвращает 0 при нулевом/пустом знаменателе.
    """
    num_f = pd.to_numeric(num, errors="coerce")
    den_f = pd.to_numeric(den, errors="coerce")
    res = num_f.div(den_f.replace({0: np.nan}))
    return res.fillna(0)


def summarize_spend(df: pd.DataFrame, by: Union[str, Sequence[str]]) -> pd.DataFrame:
    """
    Агрегация spend: показы, клики и расходы по заданным полям.
    """
    by = [by] if isinstance(by, str) else list(by)
    return (
        df.groupby(by, dropna=False)
        .agg(impressions=("impressions", "sum"), clicks=("clicks", "sum"), spend=("spend", "sum"))
    )


def summarize_deals(df: pd.DataFrame, by: Union[str, Sequence[str]]) -> pd.DataFrame:
    """
    Агрегация сделок: лиды, оплаты и выручка по заданным полям.
    """
    by = [by] if isinstance(by, str) else list(by)
    return (
        df.groupby(by, dropna=False)
        .agg(leads=("id", "count"), paid=("is_paid", "sum"), revenue=("revenue_value", "sum"))
    )


def build_metrics(deals: pd.DataFrame, spend: pd.DataFrame, group_cols: Union[str, Sequence[str]]) -> pd.DataFrame:
    """
    Считает метрики воронки и эффективности для группировки group_cols.
    """
    spend_g = summarize_spend(spend, group_cols)
    deals_g = summarize_deals(deals, group_cols)
    merged = spend_g.merge(deals_g, left_index=True, right_index=True, how="outer", sort=False).fillna(0)
    metrics = merged.copy()
    # эффективность креатива и кликов
    metrics["ctr"] = safe_ratio(metrics["clicks"], metrics["impressions"])  # клики / показы
    metrics["cpc"] = safe_ratio(metrics["spend"], metrics["clicks"])  # стоимость клика
    # конверсии и стоимость лида/оплаты
    metrics["cr"] = safe_ratio(metrics["paid"], metrics["leads"])  # лид -> оплата
    metrics["cpl"] = safe_ratio(metrics["spend"], metrics["leads"])  # стоимость лида
    metrics["cpa"] = safe_ratio(metrics["spend"], metrics["paid"])  # стоимость оплаты
    # возврат на расходы
    metrics["roas"] = safe_ratio(metrics["revenue"], metrics["spend"])  # выручка / затраты
    # шаги воронки
    metrics["click_to_lead"] = safe_ratio(metrics["leads"], metrics["clicks"])  # из кликов в лиды
    metrics["lead_to_paid"] = safe_ratio(metrics["paid"], metrics["leads"])  # из лидов в оплату
    metrics["full_conversion"] = safe_ratio(metrics["paid"], metrics["impressions"])  # оплата от показа
    # чек
    metrics["avg_payment"] = safe_ratio(metrics["revenue"], metrics["paid"])  # средний платёж
    return metrics.reset_index()


def funnel_table(deals: pd.DataFrame, spend: pd.DataFrame) -> pd.DataFrame:
    """
    Готовит табличную воронку: Impressions → Clicks → Leads → Paid + конверсии к следующему шагу.
    """
    overall = {
        "impressions": spend["impressions"].sum(),
        "clicks": spend["clicks"].sum(),
        "leads": len(deals),
        "paid": deals["is_paid"].sum(),
    }
    ctr = safe_ratio(pd.Series([overall["clicks"]]), pd.Series([overall["impressions"]])).iat[0]
    click_to_lead = safe_ratio(pd.Series([overall["leads"]]), pd.Series([overall["clicks"]])).iat[0]
    lead_to_paid = safe_ratio(pd.Series([overall["paid"]]), pd.Series([overall["leads"]])).iat[0]

    def pct(x: float) -> float:
        return round(float(x * 100), 3)

    return pd.DataFrame(
        [
            {"этап": "Impressions", "количество": overall["impressions"], "конверсия в следующий этап, %": pct(ctr)},
            {"этап": "Clicks", "количество": overall["clicks"], "конверсия в следующий этап, %": pct(click_to_lead)},
            {"этап": "Leads", "количество": overall["leads"], "конверсия в следующий этап, %": pct(lead_to_paid)},
            {"этап": "Paid", "количество": overall["paid"], "конверсия в следующий этап, %": "---"},
        ]
    )


def compute_all_metrics(
    deals: pd.DataFrame,
    spend: pd.DataFrame,
    source: str | None = None,
    campaign: str | None = None,
    adgroup: str | None = None,
) -> dict:
    """
    Собирает метрики по текущему фильтру (source/campaign/adgroup) и общую воронку.
    """
    deals_f = deals.copy()
    spend_f = spend.copy()
    if source:
        deals_f = deals_f[deals_f["source"] == source]
        spend_f = spend_f[spend_f["source"] == source]
    if campaign:
        deals_f = deals_f[deals_f["campaign"] == campaign]
        spend_f = spend_f[spend_f["campaign"] == campaign]
    if adgroup:
        deals_f = deals_f[deals_f["adgroup"] == adgroup]
        spend_f = spend_f[spend_f["adgroup"] == adgroup]

    deals_with_campaign = deals_f[deals_f["campaign"] != ""]
    campaign_metrics = build_metrics(deals_with_campaign, spend_f, ["campaign"])
    source_metrics = build_metrics(deals_f, spend_f, ["source"])
    adgroup_metrics = build_metrics(deals_with_campaign, spend_f, ["campaign", "adgroup"])

    funnel = funnel_table(deals_f, spend_f)
    return {
        "funnel": funnel,
        "campaign_metrics": campaign_metrics,
        "source_metrics": source_metrics,
        "adgroup_metrics": adgroup_metrics,
    }
