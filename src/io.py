# src/io.py
"""
Утилиты ввода-вывода для проекта:
- чтение/запись CSV, Excel, Parquet;
- стандартные пути data/raw, data/temp, data/clean, reports;
- безопасный вывод в консоль (без падения на UnicodeEncodeError).
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import json
import sys

# === Базовые пути ===
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

RAW_DIR = DATA_DIR / "raw"
TEMP_DIR = DATA_DIR / "temp"
CLEAN_DIR = DATA_DIR / "clean"


def safe_print(msg: str) -> None:
    """
    Печать с заменой некодируемых символов, чтобы не падать на Windows-консолях.
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc, errors="replace"))


def read_table(path: Path, **kwargs) -> pd.DataFrame:
    """
    Универсальное чтение таблицы (.csv, .xlsx, .parquet).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, **kwargs)
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path, **kwargs)
    if suffix == ".parquet":
        return pd.read_parquet(path, **kwargs)
    raise ValueError(f"Неподдерживаемое расширение файла: {suffix}")


def write_table(df: pd.DataFrame, path: Path, index: bool = False, **kwargs) -> None:
    """
    Запись датафрейма в .csv или .parquet.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=index, **kwargs)
    elif suffix == ".parquet":
        df.to_parquet(path, index=index, **kwargs)
    else:
        raise ValueError(f"Неподдерживаемое расширение: {suffix}")

    safe_print(f"OK. Saved: {path}")


def load_clean(name: str, fmt: str = "csv", **kwargs) -> pd.DataFrame:
    """
    Читает очищенную таблицу из data/clean/.
    """
    path = CLEAN_DIR / f"{name}.{fmt}"
    return read_table(path, **kwargs)


def save_temp(df: pd.DataFrame, name: str, fmt: str = "csv") -> None:
    """
    Сохраняет промежуточный файл в data/temp/.
    """
    path = TEMP_DIR / f"{name}.{fmt}"
    write_table(df, path)


def save_report(obj, name: str, fmt: str = "json") -> None:
    """
    Сохраняет отчёт (json или md) в reports/.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{name}.{fmt}"

    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    elif fmt == "md":
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(obj))
    else:
        raise ValueError("Допустимые форматы: json или md")

    safe_print(f"OK - report saved: {path}")


# Пример использования
if __name__ == "__main__":
    df_example = pd.DataFrame({"ID": [1, 2, 3], "Value": [10, 20, 30]})
    write_table(df_example, TEMP_DIR / "example.csv")
    df_loaded = read_table(TEMP_DIR / "example.csv")
    safe_print(str(df_loaded.head()))
    save_report({"rows": len(df_loaded)}, "example_report", fmt="json")
