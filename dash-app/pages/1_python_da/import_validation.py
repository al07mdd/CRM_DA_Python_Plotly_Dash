from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from dash import html, dcc, dash_table, register_page, callback, Input, Output


register_page(
    __name__,
    path="/data/import",
    name="Импорт",
    title="Данные - Импорт",
    order=10,
)


# Пути
APP_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APP_DIR.parent
IMPORT_JSON_PATH = PROJECT_ROOT / "reports" / "import_checklist.json"


def load_import_checklist(path: Path = IMPORT_JSON_PATH) -> list[dict[str, Any]]:
    try:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def summarize_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in files:
        out.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "rows": item.get("rows"),
                "cols": item.get("cols"),
                "path": item.get("path"),
            }
        )
    return out


def layout():
    from .sidebar import get_sidebar

    files_data = load_import_checklist()
    options = [{"label": f.get("name"), "value": f.get("name")} for f in files_data]
    default_value = options[0]["value"] if options else None

    summary_rows = summarize_files(files_data)
    # Компактные, по левому краю таблицы
    table_common_kwargs = dict(
        style_table={"overflowX": "hidden", "width": "100%", "minWidth": 0},
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "padding": "6px",
            "fontFamily": "Inter, system-ui",
            "fontSize": 13,
            "maxWidth": 280,
        },
        style_header={"textAlign": "left", "fontWeight": 600},
        css=[
            {
                "selector": ".dash-cell div.dash-cell-value",
                "rule": "white-space: normal; overflow: hidden; text-overflow: ellipsis;",
            },
            {"selector": ".dash-table-container", "rule": "max-width: 100%;"},
        ],
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        children=[
            get_sidebar(),
            html.Div(
                style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
                children=[
                    html.Article(
                        [
                            html.H3("Импорт данных"),
                            html.Div(
                                [
                                    html.Button("Обновить отчёт", id="imp-reload-btn"),
                                    dcc.ConfirmDialog(id="imp-reload-msg"),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "12px",
                                    "margin": "6px 6px 16px",
                                },
                            ),
                            dash_table.DataTable(
                                id="imp-summary-table",
                                data=summary_rows,
                                columns=[
                                    {"name": "Файл", "id": "name"},
                                    {"name": "Статус", "id": "status"},
                                    {"name": "Строк", "id": "rows"},
                                    {"name": "Колонок", "id": "cols"},
                                    {"name": "Путь", "id": "path"},
                                ],
                                sort_action="native",
                                filter_action="native",
                                page_size=10,
                                style_cell_conditional=[
                                    {"if": {"column_id": "path"}, "maxWidth": 420},
                                ],
                                **table_common_kwargs,
                            ),
                        ],
                    ),

                    html.Article(
                        [
                            html.H3("Файл"),
                            dcc.Dropdown(
                                id="imp-file-select",
                                options=options,
                                value=default_value,
                                placeholder="Выберите файл",
                                clearable=False,
                                style={"maxWidth": "520px"},
                            ),
                            html.Div(id="imp-file-meta", style={"margin": "10px 6px 10px"}),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H4("Типы столбцов"),
                                            dash_table.DataTable(
                                                id="imp-dtypes-table", **table_common_kwargs
                                            ),
                                        ],
                                        style={"marginBottom": 18},
                                    ),
                                    html.Div(
                                        [
                                            html.H4("Пропуски (NaN)"),
                                            dash_table.DataTable(
                                                id="imp-nan-table", **table_common_kwargs
                                            ),
                                        ],
                                        style={"marginBottom": 18},
                                    ),
                                ]
                            ),
                        ],
                    ),

                    # в отдельной статье, чтобы изолировать ширину
                    html.Article(
                        [
                            html.H3("Первые 5 строк"),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        id="imp-sample-table",
                                        page_size=5,
                                        style_table={
                                            "minWidth": 1100,
                                            "overflowX": "auto",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "padding": "6px",
                                            "fontFamily": "Inter, system-ui",
                                            "fontSize": 13,
                                        },
                                        style_header={"textAlign": "left", "fontWeight": 600},
                                    )
                                ],
                                style={
                                    "overflowX": "auto",
                                    "width": "100%",
                                    "maxWidth": "1400px",
                                    "margin": "0 auto",
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


@callback(
    Output("imp-summary-table", "data"),
    Output("imp-reload-msg", "displayed"),
    Output("imp-reload-msg", "message"),
    Input("imp-reload-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reload_import(n_clicks: int):
    # Попробуем заново сгенерировать отчет перед его повторной загрузкой.
    try:
        from src.simple_import import generate_import_report  # type: ignore
        generate_import_report()
    except Exception:
        pass
    data = load_import_checklist()
    msg = (
        "Отчёт обновлён из reports/import_checklist.json"
        if data
        else "Файл отчёта не найден. Сначала выполните: python -m srs.simple_import"
    )
    return summarize_files(data), True, msg


@callback(
    Output("imp-file-select", "options"),
    Output("imp-file-select", "value"),
    Input("imp-summary-table", "data"),
)
def update_file_options(summary_rows: list[dict[str, Any]] | None):
    rows = summary_rows or []
    options = [{"label": r.get("name"), "value": r.get("name")} for r in rows]
    value = options[0]["value"] if options else None
    return options, value


@callback(
    Output("imp-file-meta", "children"),
    Output("imp-dtypes-table", "data"),
    Output("imp-dtypes-table", "columns"),
    Output("imp-nan-table", "data"),
    Output("imp-nan-table", "columns"),
    Output("imp-sample-table", "data"),
    Output("imp-sample-table", "columns"),
    Output("imp-sample-table", "style_table"),
    Input("imp-file-select", "value"),
)
def update_file_details(selected_name: str | None):
    files_data = load_import_checklist()
    if not selected_name:
        return html.Div(), [], [], [], [], [], [], {"minWidth": 900, "overflowX": "auto"}
    item = next((x for x in files_data if x.get("name") == selected_name), None)
    if not item:
        return html.Div(), [], [], [], [], [], [], {"minWidth": 900, "overflowX": "auto"}

    meta = html.Ul(
        [
            html.Li(["Статус: ", html.B(item.get("status"))]),
            html.Li(["Строк: ", html.Code(str(item.get("rows")))]),
            html.Li(["Колонок: ", html.Code(str(item.get("cols")))]),
            html.Li(["Путь: ", html.Code(item.get("path"))]),
        ]
    )

    dtypes = item.get("dtypes") or {}
    dtypes_rows = [{"column": k, "dtype": v} for k, v in dtypes.items()]
    dtypes_cols = [
        {"name": "column", "id": "column"},
        {"name": "dtype", "id": "dtype"},
    ]

    nans = item.get("nan_counts") or {}
    nan_rows = [{"column": k, "n_missing": v} for k, v in nans.items()]
    nan_cols = [
        {"name": "column", "id": "column"},
        {"name": "n_missing", "id": "n_missing"},
    ]

    sample_rows = item.get("sample") or []
    sample_cols = (
        [{"name": c, "id": c} for c in sample_rows[0].keys()] if sample_rows else []
    )

    n_cols = len(sample_cols)
    base = 120  # px per column
    min_width = max(900, base * n_cols) if n_cols else 900
    style_table = {"minWidth": min_width, "overflowX": "auto"}

    return meta, dtypes_rows, dtypes_cols, nan_rows, nan_cols, sample_rows, sample_cols, style_table
