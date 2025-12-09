# src/analytics_descriptive.py

from __future__ import annotations

"""
Описательная статистика: числовая сводка (mean/median/mode/range) и частотные таблицы для категорий
"""

from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd

try:
    # Желательно использовать переменную или путь CLEAN_DIR, взятый из проектного модуля ввода-вывода (IO), а не задавать его вручную.
    from .io import CLEAN_DIR  # type: ignore
except Exception:
    # Запасной вариант: data/clean относительно корня
    CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"


# Наборы данных, с которыми работаем
DATASETS: List[str] = ["Contacts", "Calls", "Spend", "Deals"]

# Числовые поля, которые имеют смысл для описательной статистики
ALLOWED_NUMERIC: Dict[str, List[str]] = {
    "Calls": ["Call Duration (in seconds)"],
    "Spend": ["Impressions", "Clicks", "Spend"],
    "Deals": [
        "Course duration",
        "Months of study",
        "Initial Amount Paid",
        "Offer Total Amount",
    ],
}

# Категориальные поля для частотных таблиц
CATEGORICAL_COLS: Dict[str, List[str]] = {
    "Deals": ["Quality", "Stage", "Source", "Product"],
    "Calls": ["Call Type", "Call Status", "Call Owner Name"],
    "Spend": ["Source", "Campaign", "AdGroup", "Ad"],
}


def load_clean_csv(name: str) -> Optional[pd.DataFrame]:
    """
    Загружает датасет из data/clean: сначала Parquet, затем CSV.

    Возвращает DataFrame или None, если подходящий файл не найден/сломан.
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
        try:
            return pd.read_csv(p_csv)
        except Exception:
            return None
    return None


def numeric_summary(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Числовая сводка: среднее, медиана, мода, диапазон (max–min). Если columns = None, берём все числовые поля в df.
    """
    if columns is None:
        num = df.select_dtypes(include="number")
    else:
        cols = [c for c in columns if c in df.columns]
        if not cols:
            return pd.DataFrame()
        num = df[cols].apply(pd.to_numeric, errors="coerce")

    if num.empty:
        return pd.DataFrame()

    mode_row = num.mode().iloc[0] if not num.mode().empty else pd.Series(index=num.columns, dtype="float64")
    out = pd.DataFrame(
        {
            "mean": num.mean(),
            "median": num.median(),
            "mode": mode_row,
            "range": num.max() - num.min(),
        }
    )
    return out


def categorical_summary(df: pd.DataFrame, column: str, top: int = 20) -> pd.DataFrame:
    """
    Частотная таблица для колонки: count + percent (в %), с учётом NaN. Возвращает top N значений.
    """
    if column not in df.columns:
        return pd.DataFrame({"info": [f"No column {column}"]})
    s = df[column]
    vc = s.value_counts(dropna=False)
    share = (vc / vc.sum() * 100).round(2)
    return pd.DataFrame({"count": vc, "percent": share}).head(top)


def present_numeric_columns(df: pd.DataFrame, dataset: str) -> List[str]:
    """
    Вернёт список доступных в df числовых колонок из ALLOWED_NUMERIC[dataset].
    """
    cols = ALLOWED_NUMERIC.get(dataset, [])
    return [c for c in cols if c in df.columns]


def present_categorical_columns(df: pd.DataFrame, dataset: str) -> List[str]:
    """
    Вернёт доступные в df категории из CATEGORICAL_COLS[dataset].
    """
    cols = CATEGORICAL_COLS.get(dataset, [])
    return [c for c in cols if c in df.columns]


def load_all() -> Dict[str, Optional[pd.DataFrame]]:
    """
    Загрузить все доступные наборы данных из data/clean.
    """
    return {name: load_clean_csv(name) for name in DATASETS}


def summarize_dataset(name: str) -> Dict[str, object]:
    """
    Сводка по одному набору.

    Ключи:
      - name: имя набора
      - numeric_cols: используемые числовые колонки
      - numeric_summary: DataFrame со статистикой (или пустой)
      - categorical_cols: используемые категории
      - categorical: {колонка -> DataFrame с частотами}
    """
    df = load_clean_csv(name)
    if df is None:
        return {
            "name": name,
            "numeric_cols": [],
            "numeric_summary": pd.DataFrame(),
            "categorical_cols": [],
            "categorical": {},
        }

    num_cols = present_numeric_columns(df, name)
    num_summary = numeric_summary(df, num_cols) if num_cols else pd.DataFrame()

    cat_cols = present_categorical_columns(df, name)
    cat_summaries: Dict[str, pd.DataFrame] = {}
    for col in cat_cols:
        cat_summaries[col] = categorical_summary(df, col, top=20)

    return {
        "name": name,
        "numeric_cols": num_cols,
        "numeric_summary": num_summary,
        "categorical_cols": cat_cols,
        "categorical": cat_summaries,
    }
