"""
Очистка данных.

Функции:
- читают Excel-файлы из data/raw с dtype=str, чтобы не терять лидирующие нули и буквы в идентификаторах;
- приводят типы, убирают дубликаты и пустые столбцы;
- сохраняют очищенные таблицы в CSV и Parquet в data/clean;
- формируют отчёт (JSON + MD) с метаданными: было/стало, типы, пропуски, пути сохранения.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Sequence, Any

import pandas as pd

from . import io as srs_io


def safe_print(msg: str) -> None:
    """
    Печать с защитой от UnicodeEncodeError в консоли Windows.
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc, errors="replace"))


def drop_all_null_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Удаляет столбцы, где все значения NaN.
    """
    return df.dropna(axis=1, how="all")


def drop_duplicate_rows(df: pd.DataFrame, subset: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """
    Удаляет дубликаты строк (если задан subset - по указанным столбцам).
    """
    return df.drop_duplicates(subset=subset, keep="first")


def strip_whitespace(df: pd.DataFrame, columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """
    Обрезает пробелы в строковых столбцах (по умолчанию - все object/string).
    """
    if columns is None:
        columns = [c for c in df.columns if df[c].dtype == "object" or pd.api.types.is_string_dtype(df[c])]
    for c in columns:
        df[c] = df[c].astype("string").str.strip()
    return df


def normalize_text_series(s: pd.Series) -> pd.Series:
    """
    Приводит строки к нижнему регистру, убирает лишние пробелы.
    """
    s = s.astype("string")
    s = s.str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    s = s.str.lower()
    return s


def normalize_categorical(df: pd.DataFrame, columns: Sequence[str], fill_unknown: bool = False) -> pd.DataFrame:
    """
    Нормализует текстовые категории: обрезает пробелы, приводит к нижнему регистру. При fill_unknown заполняет NaN как 'unknown'.
    """
    for c in columns:
        if c in df.columns:
            df[c] = normalize_text_series(df[c])
            if fill_unknown:
                df[c] = df[c].fillna("unknown")
    return df


def to_datetime(df: pd.DataFrame, column: str, dayfirst: bool = True, fmt: str | None = None) -> pd.DataFrame:
    """
    Преобразует столбец в datetime (некорректные значения превращаются в NaT).
    """
    if column in df.columns:
        df[column] = pd.to_datetime(df[column], errors="coerce", dayfirst=dayfirst, format=fmt)
    return df


def to_int(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Преобразует столбец к pandas Int64 (nullable).
    """
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
    return df


def to_float(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Преобразует столбец к float64 (nullable).
    """
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("float64")
    return df


def id_to_string(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Оставляет идентификатор строковым без промежуточного to_numeric (не теряем нули/буквы).
    """
    if column in df.columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def df_brief(df: pd.DataFrame) -> dict[str, Any]:
    """
    Короткое описание датафрейма: размер, типы, пропуски, первые 5 строк.
    """
    dtypes_map = {str(c): str(t) for c, t in df.dtypes.items()}
    nan_counts = df.isna().sum()
    info = {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": list(map(str, df.columns)),
        "dtypes": dtypes_map,
        "nan_counts": {str(c): int(nan_counts[c]) for c in df.columns},
        "sample": json.loads(df.head(5).to_json(orient="records", date_format="iso", force_ascii=False)),
    }
    return info


# Очистка таблиц

def clean_contacts(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Очистка Contacts: обрезка пробелов, удаление дубликатов по Id, приведение дат.
    """
    notes: list[str] = []
    before_cols = set(df.columns)

    df = drop_all_null_columns(df)
    df = strip_whitespace(df)
    df = drop_duplicate_rows(df, subset=["Id"])
    df = id_to_string(df, "Id")
    df = to_datetime(df, "Created Time", dayfirst=True)
    df = to_datetime(df, "Modified Time", dayfirst=True)

    removed_cols = sorted(set(before_cols) - set(df.columns))
    if removed_cols:
        notes.append(f"Удалены пустые столбцы: {removed_cols}")
    return df, notes


def clean_calls(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Очистка Calls: нормализация статусов, bool для Scheduled, Id и CONTACTID строковые.
    """
    notes: list[str] = []
    before_cols = set(df.columns)

    df = drop_all_null_columns(df)
    df = strip_whitespace(df)
    df = drop_duplicate_rows(df, subset=["Id"])
    df = id_to_string(df, "Id")
    df = to_datetime(df, "Call Start Time", dayfirst=True)
    df = to_int(df, "Call Duration (in seconds)")

    if "CONTACTID" in df.columns:
        df["CONTACTID"] = df["CONTACTID"].astype("string").str.strip()

    if "Scheduled in CRM" in df.columns:
        df["Scheduled in CRM"] = pd.to_numeric(df["Scheduled in CRM"], errors="coerce").fillna(0).astype(int).astype(bool)
        notes.append("'Scheduled in CRM' приведён к bool; пропуски трактованы как False.")

    df = normalize_categorical(df, ["Call Type", "Call Status", "Outgoing Call Status"], fill_unknown=True)

    removed_cols = sorted(set(before_cols) - set(df.columns))
    if removed_cols:
        notes.append(f"Удалены пустые столбцы: {removed_cols}")
    return df, notes


def clean_spend(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Очистка Spend: удаление пустых столбцов и точных дубликатов, типы для даты и метрик.
    """
    notes: list[str] = []
    before_cols = set(df.columns)

    df = drop_all_null_columns(df)
    df = strip_whitespace(df)
    df = drop_duplicate_rows(df)
    df = to_datetime(df, "Date", dayfirst=True, fmt="%Y-%m-%d %H:%M:%S")
    if "Date" in df.columns:
        df["Date"] = df["Date"].dt.normalize()
    df = to_int(df, "Impressions")
    df = to_int(df, "Clicks")
    df = to_float(df, "Spend")

    removed_cols = sorted(set(before_cols) - set(df.columns))
    if removed_cols:
        notes.append(f"Удалены пустые столбцы: {removed_cols}")
    return df, notes


def clean_deals(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Очистка Deals: удаление пустых Id, нормализация категорий, приведение сумм к float.
    """
    notes: list[str] = []
    before_cols = set(df.columns)

    df = drop_all_null_columns(df)
    df = strip_whitespace(df)
    df = drop_duplicate_rows(df, subset=["Id"])
    df = df.dropna(subset=["Id"])
    df = id_to_string(df, "Id")
    df = df[df["Id"].notna()]
    df = df[~df["Id"].isin(["", "nan", "NaN", "<NA>"])]

    df = to_datetime(df, "Created Time", dayfirst=True)
    df = df.dropna(subset=["Created Time"])
    df = to_datetime(df, "Closing Date", dayfirst=True)

    df = to_float(df, "Initial Amount Paid")
    df = to_float(df, "Offer Total Amount")
    df = to_float(df, "Course duration")
    df = to_float(df, "Months of study")
    if "SLA" in df.columns:
        # SLA arrives as hh:mm:ss strings -> convert to float hours for analytics.
        sla_series = df["SLA"]
        if pd.api.types.is_numeric_dtype(sla_series):
            df["SLA"] = pd.to_numeric(sla_series, errors="coerce").astype("float64")
        else:
            sla_td = pd.to_timedelta(sla_series, errors="coerce")
            df["SLA"] = sla_td.dt.total_seconds() / 3600
        notes.append("SLA переводим в часы (float).")


    df = normalize_categorical(df, ["Stage", "Quality", "Payment Type"], fill_unknown=True)

    if "Source" in df.columns:
        df["Source"] = df["Source"].fillna("unknown")
        notes.append("'Source' заполнен значением 'unknown', если не указан.")

    removed_cols = sorted(set(before_cols) - set(df.columns))
    if removed_cols:
        notes.append(f"Удалены пустые столбцы: {removed_cols}")
    return df, notes


# Запуск и отчёт 

def run_cleaning(
    raw_dir: Path | str | None = None,
    clean_dir: Path | str | None = None,
    report_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Запускает полный цикл очистки: читает исходные файлы, очищает, сохраняет CSV/Parquet и отчёт.
    """

    raw_dir = Path(raw_dir) if raw_dir else srs_io.RAW_DIR
    clean_dir = Path(clean_dir) if clean_dir else srs_io.CLEAN_DIR
    clean_dir.mkdir(parents=True, exist_ok=True)

    report_md_path = Path(report_path) if report_path else (srs_io.REPORTS_DIR / "step2_eda_summary.md")
    report_json_path = report_md_path.with_suffix(".json")
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    tasks: list[dict[str, Any]] = [
        {"name": "Contacts", "path": raw_dir / "Contacts (Done).xlsx", "clean_name": "Contacts", "clean_fn": clean_contacts},
        {"name": "Calls", "path": raw_dir / "Calls_(Done).xlsx", "clean_name": "Calls", "clean_fn": clean_calls},
        {"name": "Spend", "path": raw_dir / "Spend (Done).xlsx", "clean_name": "Spend", "clean_fn": clean_spend},
        {"name": "Deals", "path": raw_dir / "Deals (Done).xlsx", "clean_name": "Deals", "clean_fn": clean_deals},
    ]

    lines: list[str] = []
    report_list: list[dict[str, Any]] = []

    lines.append("# Шаг 2 - EDA / Очистка (data/clean)\n")
    lines.append("Очистка выгрузок CRM и сохранение очищенных данных в `data/clean`.\n")

    def _to_rel(p: Path) -> str:
        try:
            return p.relative_to(srs_io.BASE_DIR).as_posix()
        except Exception:
            return p.as_posix()

    for t in tasks:
        name: str = t["name"]
        fpath: Path = t["path"]
        out_base: str = t["clean_name"]
        clean_fn = t["clean_fn"]

        lines.append(f"\n## {name}\n")
        try:
            df_raw = pd.read_excel(fpath, dtype=str)
            before = df_brief(df_raw)

            df_clean, notes = clean_fn(df_raw.copy())
            after = df_brief(df_clean)

            rows_removed = max(0, before["rows"] - after["rows"])
            cols_removed = [c for c in before["columns"] if c not in after["columns"]]

            csv_path = Path(clean_dir) / f"{out_base}.csv"
            parquet_path = Path(clean_dir) / f"{out_base}.parquet"
            srs_io.write_table(df_clean, csv_path)
            srs_io.write_table(df_clean, parquet_path)

            lines.append(f"Итог: {before['rows']}x{before['cols']} → {after['rows']}x{after['cols']}\n")
            if rows_removed:
                lines.append(f"- Удалены строки: {rows_removed}\n")
            if cols_removed:
                lines.append(f"- Удалены столбцы: {cols_removed}\n")
            if notes:
                for note in notes:
                    lines.append(f"- {note}\n")

            report_list.append(
                {
                    "name": name,
                    "path": _to_rel(fpath),
                    "status": "ok",
                    "before": before,
                    "after": after,
                    "changes": {
                        "rows_removed": rows_removed,
                        "columns_removed": cols_removed,
                        "notes": notes,
                    },
                    "clean_output": _to_rel(csv_path),
                    "clean_output_parquet": _to_rel(parquet_path),
                }
            )
        except Exception as e:  # noqa: BLE001
            lines.append("- Ошибка: не удалось очистить файл\n")
            lines.append(f"- Путь: `{fpath.as_posix()}`\n")
            lines.append(f"- Сообщение: {e}\n")
            report_list.append(
                {
                    "name": name,
                    "path": _to_rel(fpath),
                    "status": "error",
                    "error": str(e),
                }
            )

        lines.append("\n---\n")

    report_md_path.write_text("\n".join(lines), encoding="utf-8")
    report_json_path.write_text(json.dumps(report_list, ensure_ascii=False, indent=2), encoding="utf-8")

    safe_print(f"MD report saved to {report_md_path}")
    safe_print(f"JSON report saved to {report_json_path}")
    return {"md": report_md_path.as_posix(), "json": report_json_path.as_posix()}


if __name__ == "__main__":
    run_cleaning()
