# src/simple_import.py

"""
Импорт исходных данных и генерация отчёта.

Поиск всех файлы Excel (*.xlsx) в data/raw,
загрузка их с pandas и отчёт в reports/.

"""

from pathlib import Path
import json
import pandas as pd


def generate_import_report(
    data_dir: str | Path = "data/raw",
    report_path: str | Path = "reports/import_checklist.md",
) -> None:
    """
    Загрузка всех .xlsx из каталога data/raw и запись отчёта.

    Параметры:
        data_dir: путь к каталогу с исходными файлами.
        report_path: путь к итоговому .md отчёту.
    """
    # Приводим пути к объектам Path и создаём каталог для отчёта при необходимости
    data_dir = Path(data_dir)
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Ищем все Excel-файлы
    excel_files = sorted(data_dir.glob("*.xlsx"))

    # Накапливаем строки отчёта в список
    lines: list[str] = []
    lines.append("# Отчёт о загрузке исходных данных\n")
    lines.append(f"Каталог: `{data_dir.as_posix()}`\n")

    if not excel_files:
        # Если файлов нет - фиксируем в отчёте
        lines.append("Файлы *.xlsx не найдены.\n")
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return

    # Обрабатываем каждый Excel-файл по очереди
    report_json: list[dict] = []

    for fpath in excel_files:
        lines.append(f"\n## {fpath.name}\n")
        try:
            # Загружаем файл в DataFrame
            df_file = pd.read_excel(fpath)
            df = df_file

            # Базовая сводка по таблице
            n_rows, n_cols = df.shape
            lines.append("- Статус: успешно загружен\n")
            lines.append(f"- Путь: `{fpath.as_posix()}`\n")
            lines.append(f"- Размер: {n_rows} строк × {n_cols} столбцов\n")
            lines.append(f"- Столбцы: {list(map(str, df.columns))}\n")

            # Типы данных по столбцам
            dtypes_map = {str(c): str(t) for c, t in df.dtypes.items()}
            lines.append("\n### Типы данных (столбец,dtype)\n")
            dtype_rows = ["column,dtype"] + [f"{col},{dtypes_map[col]}" for col in map(str, df.columns)]
            lines.append("\n".join(dtype_rows))

            # Пропуски (NaN) по столбцам
            lines.append("\n### Пропуски (NaN) по столбцам\n")
            lines.append("column,NaN")
            nan_counts = df.isna().sum()
            lines.extend([f"{str(col)},{int(nan_counts[col])}" for col in df.columns])

            # Предпросмотр первых 5 строк 
            preview_csv = df.head(5).to_csv(index=False)
            lines.append("\n### Пример данных (первые 5 строк, CSV)\n")
            lines.append(preview_csv.strip())

            # Данные для JSON-отчёта
            report_json.append(
                {
                    "name": fpath.name,
                    "path": fpath.as_posix(),
                    "status": "ok",
                    "rows": int(n_rows),
                    "cols": int(n_cols),
                    "columns": list(map(str, df.columns)),
                    "dtypes": dtypes_map,
                    "nan_counts": {str(c): int(nan_counts[c]) for c in df.columns},
                    # Через pandas.to_json приводим значения к сериализуемым типам
                    "sample": json.loads(
                        df.head(5).to_json(orient="records", date_format="iso", force_ascii=False)
                    ),
                }
            )
        except Exception as e:
            # Фиксируем ошибку чтения и продолжаем со следующим файлом
            lines.append("- Статус: ошибка при чтении файла\n")
            lines.append(f"- Путь: `{fpath.as_posix()}`\n")
            lines.append(f"- Сообщение: {e}\n")

            # Для JSON фиксируем ошибку
            report_json.append(
                {
                    "name": fpath.name,
                    "path": fpath.as_posix(),
                    "status": "error",
                    "error": str(e),
                }
            )

        # Разделитель между файлами
        lines.append("\n---\n")

    # Готовый отчёт в UTF-8
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # JSON-версии отчёта
    json_path = report_path.with_suffix(".json")
    json_path.write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    generate_import_report()
