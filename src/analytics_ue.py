from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

try:
    from .io import CLEAN_DIR  # type: ignore
except Exception:
    CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"

_PRODUCTS = ["Web Developer", "Digital Marketing", "UX/UI Design"]
_GROWTH_LEVERS = ["UA", "C1", "CPA", "AOV", "APC"]
_HADI_ROWS = [
    {
        "Часть": "H (гипотеза)",
        "Описание": (
            "Если сократить время первого контакта с лидом (SLA) до 24 часов за счет регламента, автоматических напоминаний в CRM и контроля обработки лидов, "
            "то конверсия C1 (B / UA) вырастет с текущего уровня до ~10% (целевое значение)"
        ),
    },
    {
        "Часть": "A (действия)",
        "Описание": (
            "Проводим A/B-тест на новых лидах:\n"
            "A - контроль: текущий процесс обработки лидов (без изменений);\n"
            "B - эксперимент:\n"
            "- автоматическая задача менеджеру связаться ≤ 24 часов\n"
            "- push-напоминания в CRM\n"
            "- шаблоны сообщений / скрипты\n"
            "- контроль времени обработки и SLA-алерты\n"
        ),
    },
    {
        "Часть": "D (данные и метрики)",
        "Описание": (
            "UE-метрика (целевая): C1 = B / UA по группам A и B.\n"
            "Продуктовая метрика: доля лидов, где SLA ≤ 24 часов (Deals: SLA).\n"
            "Дополнительно: конверсии по стадиям воронки и распределение SLA.\n"
            "Для теста используем:\n"
            "- рассчитанный объем выборки n\n"
            "- текущий трафик сегмента (UA/day)\n"
            "- минимальный обнаруживаемый эффект x = target - p_base\n"
        ),
    },
    {
        "Часть": "I (интерпретация)",
        "Описание": (
            """Если C1_B ≥ 10% и разница между группами A и B превышает минимально обнаруживаемый эффект x, рассчитанный для сегмента,
            то гипотеза считается подтвержденной, и новый процесс масштабируется на весь поток лидов.
            Если прирост меньше x - подтверждаем нулевую гипотезу и формируем следующую"""
        ),
    },
]


def _load_table(name: str) -> pd.DataFrame:
    """
    Читает parquet-таблицу из data/clean по имени набора.
    """
    path = Path(CLEAN_DIR) / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл: {path}")
    return pd.read_parquet(path)


def load_ue_tables() -> Dict[str, pd.DataFrame]:
    """
    Загружает Deals/Contacts/Calls/Spend из data/clean.
    """
    names = ["Deals", "Contacts", "Calls", "Spend"]
    return {name.lower(): _load_table(name) for name in names}


def _calc_r_i(row: pd.Series) -> pd.Series:
    """
    Считает AOV_I и R_I для конкретной сделки.
    """
    months = row["months_of_study"]
    duration = row["course_duration"]
    total = row["offer_total_amount"]
    initial = row["initial_amount_paid"]

    if pd.isna(months) or pd.isna(duration) or pd.isna(total) or months <= 0 or duration <= 0:
        return pd.Series({"aov_i": np.nan, "r_i": np.nan})

    if total - initial > 0 and duration > 1:
        monthly_tail = (total - initial) / (duration - 1)
        numerator = initial + max(months - 1, 0) * monthly_tail
        aov_i = numerator / months if months else np.nan
    else:
        aov_i = total / duration

    r_i = aov_i * months if pd.notna(aov_i) else np.nan
    return pd.Series({"aov_i": aov_i, "r_i": r_i})


def _unique(series: pd.Series) -> float:
    """
    Возвращает число уникальных значений в колонке как float.
    """
    return float(series.astype("string").nunique(dropna=True))


def _prepare_context(tables: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, object]:
    """
    Строит базовые таблицы, метрики и сегменты для повторного использования.
    """
    tables = tables or load_ue_tables()
    deals = tables["deals"].copy()
    spend = tables["spend"]
    contacts = tables["contacts"]
    calls = tables["calls"]

    closed_deals = deals[deals["Stage"] == "payment done"].copy()
    closed_deals = closed_deals[closed_deals["Offer Total Amount"].fillna(0) > 10].copy()

    closed_deals["months_of_study"] = closed_deals["Months of study"]
    closed_deals["course_duration"] = closed_deals["Course duration"]
    closed_deals["initial_amount_paid"] = closed_deals["Initial Amount Paid"].fillna(0)
    closed_deals["offer_total_amount"] = closed_deals["Offer Total Amount"].fillna(0)
    closed_deals[["aov_i", "r_i"]] = closed_deals.apply(_calc_r_i, axis=1)

    ua_candidates: List[float] = []
    if "Contact Name" in deals.columns:
        ua_candidates.append(_unique(deals["Contact Name"]))
    if "Id" in contacts.columns:
        ua_candidates.append(_unique(contacts["Id"]))
    if "CONTACTID" in calls.columns:
        ua_candidates.append(_unique(calls["CONTACTID"]))

    ua = max(ua_candidates) if ua_candidates else float("nan")

    buyers = closed_deals["Id"].nunique()
    ac = float(spend["Spend"].sum())
    transactions = float(closed_deals["months_of_study"].fillna(0).sum())
    revenue = float(closed_deals["r_i"].sum())

    c1 = buyers / ua if ua else np.nan
    c1_pct = c1 * 100 if pd.notna(c1) else np.nan
    cpa = ac / ua if ua else np.nan
    cac = ac / buyers if buyers else np.nan
    aov = revenue / transactions if transactions else np.nan
    apc = transactions / buyers if buyers else np.nan
    cltv = aov * apc if pd.notna(aov) and pd.notna(apc) else np.nan
    ltv = cltv * c1 if pd.notna(cltv) and pd.notna(c1) else np.nan
    cm = ua * (ltv - cpa) if pd.notna(ltv) and pd.notna(cpa) else np.nan

    metrics = pd.Series(
        {
            "UA": ua,
            "B": buyers,
            "AC": ac,
            "T": transactions,
            "Revenue": revenue,
            "C1": c1_pct,
            "CPA": cpa,
            "CAC": cac,
            "AOV": aov,
            "APC": apc,
            "CLTV": cltv,
            "LTV": ltv,
            "CM": cm,
        }
    ).to_frame(name="value").round(2)

    product_rows = []
    for product in _PRODUCTS:
        deals_product = deals[deals["Product"] == product]
        closed_product = closed_deals[closed_deals["Product"] == product]

        buyers_product = closed_product["Id"].nunique()
        transactions_product = float(closed_product["months_of_study"].fillna(0).sum())
        revenue_product = float(closed_product["r_i"].sum())
        c1_product = buyers_product / ua if ua else np.nan
        c1_pct_product = c1_product * 100 if pd.notna(c1_product) else np.nan
        aov_product = revenue_product / transactions_product if transactions_product else np.nan
        apc_product = transactions_product / buyers_product if buyers_product else np.nan
        cltv_product = aov_product * apc_product if pd.notna(aov_product) and pd.notna(apc_product) else np.nan
        ltv_product = cltv_product * c1_product if pd.notna(cltv_product) and pd.notna(c1_product) else np.nan
        cm_product = ua * (ltv_product - cpa) if pd.notna(ltv_product) and pd.notna(cpa) else np.nan

        product_rows.append(
            {
                "Product": product,
                "UA": ua,
                "B": buyers_product,
                "AC": ac,
                "T": transactions_product,
                "Revenue": revenue_product,
                "C1": c1_pct_product,
                "CPA": cpa,
                "AOV": aov_product,
                "APC": apc_product,
                "CLTV": cltv_product,
                "LTV": ltv_product,
                "CM": cm_product,
            }
        )

    product_metrics_df = pd.DataFrame(product_rows).set_index("Product").round(2)

    segments: Dict[str, Dict[str, float]] = {
        "Business": {
            "UA": metrics.loc["UA", "value"],
            "C1": metrics.loc["C1", "value"] / 100 if pd.notna(metrics.loc["C1", "value"]) else np.nan,
            "CPA": metrics.loc["CPA", "value"],
            "AOV": metrics.loc["AOV", "value"],
            "APC": metrics.loc["APC", "value"],
            "CM": metrics.loc["CM", "value"],
        }
    }
    for product in product_metrics_df.index:
        row = product_metrics_df.loc[product]
        segments[product] = {
            "UA": row["UA"],
            "C1": row["C1"] / 100 if pd.notna(row["C1"]) else np.nan,
            "CPA": row["CPA"],
            "AOV": row["AOV"],
            "APC": row["APC"],
            "CM": row["CM"],
        }

    return {
        "tables": tables,
        "metrics": metrics,
        "product_metrics": product_metrics_df,
        "segments": segments,
    }


def _compute_cm(ua_value, c1_value, cpa_value, aov_value, apc_value):
    """
    Считаем CM по заданным значениям UA/C1/CPA/AOV/APC.
    """
    if any(pd.isna(x) for x in [ua_value, c1_value, cpa_value, aov_value, apc_value]):
        return np.nan
    cltv_value = aov_value * apc_value
    ltv_value = cltv_value * c1_value
    return ua_value * (ltv_value - cpa_value)


def _growth_table(segments: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Формирует таблицу сценариев изменения CM для всех сегментов.
    """
    rows = []
    for segment, data in segments.items():
        base_cm = data["CM"]
        for lever in _GROWTH_LEVERS:
            ua_adj = data["UA"]
            c1_adj = data["C1"]
            cpa_adj = data["CPA"]
            aov_adj = data["AOV"]
            apc_adj = data["APC"]

            if lever == "UA":
                ua_adj *= 1.10
            elif lever == "C1":
                c1_adj *= 1.10
            elif lever == "CPA":
                cpa_adj *= 0.90
            elif lever == "AOV":
                aov_adj *= 1.10
            elif lever == "APC":
                apc_adj *= 1.10

            new_cm = _compute_cm(ua_adj, c1_adj, cpa_adj, aov_adj, apc_adj)
            rows.append(
                {
                    "Segment": segment,
                    "Metric": lever,
                    "CM_base": base_cm,
                    "CM_new": new_cm,
                    "CM_delta": new_cm - base_cm if pd.notna(base_cm) else np.nan,
                    "CM_delta_%": ((new_cm / base_cm) - 1) * 100 if base_cm else np.nan,
                }
            )

    return pd.DataFrame(rows).round(2)


def _ua_daily_counts(deals: pd.DataFrame) -> Dict[str, float]:
    """
    Считаем средний показатель UA в день для бизнеса и каждого сегмента продукта.
    """
    deals_copy = deals.copy()
    deals_copy["Created Time"] = pd.to_datetime(deals_copy["Created Time"], errors="coerce")
    deals_copy["created_day"] = deals_copy["Created Time"].dt.normalize()

    def calc(df: pd.DataFrame) -> float:
        if df.empty or "Contact Name" not in df.columns:
            return float("nan")
        ua_total = _unique(df["Contact Name"])
        dates = df["created_day"].dropna()
        if dates.empty or not ua_total:
            return float("nan")
        days_span = (dates.max() - dates.min()).days + 1
        if days_span <= 0:
            return float("nan")
        return ua_total / days_span

    counts: Dict[str, float] = {"Business": calc(deals_copy)}
    for product in _PRODUCTS:
        product_df = deals_copy[deals_copy["Product"] == product]
        counts[product] = calc(product_df)
    return counts



def _experiment_scope(segments: Dict[str, Dict[str, float]], deals: pd.DataFrame) -> list[Dict[str, float]]:
    """
    Считаем параметры для A/B-теста C1 отдельно для бизнеса и продуктов.
    """
    rows: list[Dict[str, float]] = []
    effect_target = 0.10
    max_days = 14

    ua_daily = _ua_daily_counts(deals)

    for segment, data in segments.items():
        p_base = data.get("C1")
        ua_base = data.get("UA")
        x_abs = (effect_target - p_base) if pd.notna(p_base) else np.nan
        ua_per_day = ua_daily.get(segment)

        if pd.isna(ua_per_day) or ua_per_day <= 0:
            n_available = np.nan
        else:
            n_available = ua_per_day * max_days

        if pd.notna(p_base) and pd.notna(n_available) and n_available > 0:
            x_mde = float(np.sqrt((16 * p_base * (1 - p_base)) / n_available))
        else:
            x_mde = np.nan

        if pd.isna(p_base) or pd.isna(ua_base) or pd.isna(x_abs) or x_abs <= 0:
            n_per_group = np.nan
            days_required = np.nan
            min_ua_per_day = np.nan
            fits_limit = False
        else:
            n_per_group = (16 * p_base * (1 - p_base)) / (x_abs ** 2)
            days_required = (n_per_group / ua_per_day) if ua_per_day and not pd.isna(ua_per_day) else np.nan
            min_ua_per_day = (n_per_group / max_days) if max_days else np.nan
            fits_limit = bool(days_required <= max_days) if pd.notna(days_required) else False

        rows.append(
            {
                "segment": segment,
                "p_base": p_base,
                "target": effect_target,
                "x_abs": x_abs,
                "n_per_group": n_per_group,
                "ua_per_day": ua_per_day,
                "n_available": n_available,
                "days_required": days_required,
                "min_ua_per_day": min_ua_per_day,
                "fits_limit": fits_limit,
                "x_mde": x_mde,
                "max_days": max_days,
            }
        )

    return rows


def unit_economics_tables() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Таблицы для юнит-экономики: общий бизнес + срез по продуктам.
    """
    ctx = _prepare_context()
    return ctx["metrics"], ctx["product_metrics"]


def growth_scenarios_table() -> pd.DataFrame:
    """
    Таблица сценариев роста CM при изменении UA/C1/CPA/AOV/APC на ±10%.
    """
    ctx = _prepare_context()
    return _growth_table(ctx["segments"])


def hadi_table() -> pd.DataFrame:
    """
    Таблица HADI с фиксированными описаниями.
    """
    return pd.DataFrame(_HADI_ROWS)


def hypothesis_check_info() -> list[Dict[str, float]]:
    """
    Возвращает параметры проверки C1 по всему бизнесу и сегментам.
    """
    ctx = _prepare_context()
    return _experiment_scope(ctx["segments"], ctx["tables"]["deals"])
