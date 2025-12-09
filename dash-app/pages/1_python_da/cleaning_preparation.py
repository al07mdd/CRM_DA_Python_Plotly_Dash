from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from dash import html, dcc, dash_table, register_page, callback, Input, Output

register_page(
    __name__,
    path="/data/cleaning",
    name="Шаг 2 - очистка",
    title="Очистка данных",
    order=20,
)

# Пути
APP_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APP_DIR.parent
REPORT_JSON_PATH = PROJECT_ROOT / "reports" / "step2_eda_summary.json"

# Краткие описания столбцов (для таблицы пропусков)
COLUMN_DESCRIPTIONS: dict[str, str] = {
    # Contacts
    "Id": "Идентификатор контакта.",
    "Contact Owner Name": "Имя лица, ответственного за управление контактом.",
    "Created Time": "Дата внесения контакта в базу.",
    "Modified Time": "Дата последней модификации контакта.",
    # Calls
    "Call Start Time": "Время начала звонка.",
    "Call Owner Name": "Имя лица, ответственного за звонок.",
    "CONTACTID": "Уникальный идентификатор контакта (может отсутствовать)",
    "Call Type": "Тип звонка (входящий/исходящий и т.п.)",
    "Call Duration (in seconds)": "Длительность звонка в секундах",
    "Call Status": "Окончательный статус звонка.",
    "Outgoing Call Status": "Статус исходящих вызовов.",
    "Scheduled in CRM": "Был ли звонок запланирован в CRM",
    "Dialled Number": "Набранный номер телефона",
    "Tag": "Тэг вызова",
    # Spend
    "Date": "Дата, указывающая, когда были отслежены показы, клики и расходы на рекламу.",
    "Source": "Канал, на котором было показано объявление.",
    "Campaign": "Кампания, в рамках которой было показано объявление.",
    "AdGroup": "Подмножество в кампании, содержащее одно или несколько объявлений с одинаковыми целями или настройками.",
    "Ad": "Конкретная реклама, показываемая пользователям.",
    "Impressions": "Количество показов рекламы пользователям.",
    "Clicks": "Количество нажатий пользователей на рекламу.",
    "Spend": "Количество денег, потраченных на рекламную кампанию или группу объявлений за указанный период.",
    # Deals
    "Deal Owner Name": "Имя лица, ответственного за сделку.",
    "Closing Date": "Дата закрытия сделки, если применимо.",
    "Stage": "Текущая стадия сделки.",
    "Quality": "Классификация качества сделки, указывающая на ее потенциальный или целевой статус.",
    "Payment Type": "Тип используемого или ожидаемого способа оплаты.",
    "Lost Reason": "Причина, по которой сделка была потеряна, если применимо.",
    "SLA": "Время действия соглашения об уровне обслуживания, указывающее на время отклика.",
    "Content": "Конкретная реклама, показываемая пользователям (=Ad).",
    "Term": "Группа объявлений (= AdGroup)",
    "Product": "Конкретный продукт или услуга, связанная со сделкой.",
    "Education Type": "Тип образования или обучения.",
    "Initial Amount Paid": "Первоначальный платеж клиента.",
    "Offer Total Amount": "Общая сумма предложения, представленного клиенту.",
    "Contact Name": "Идентификатор контактного лица по сделке.",
    "City": "Город, относящийся к клиенту.",
    "Level of Deutsch": "Уровень владения немецким (если применимо)",
    "Course duration": "Длительность курса",
    "Months of study": "Количество месяцев которые отучился студент",
    "Page": "Веб-страница или целевая страница, на которой был получен лид.",
}

# Краткие примечания по очистке 
CLEANING_NOTES: dict[str, list[str]] = {
    "Contacts": [
        "Id приведены к строковому типу, дубликаты по Id удалены.",
        "Пробелы в текстовых полях удалены, даты приведены к datetime.",
    ],
    "Calls": [
        "Id приведены к строковому типу, дубликаты по Id удалены.",
        "CONTACTID оставлены пустыми, если звонок не привязан к контакту.",
        "Outgoing Call Status и Call Type нормализованы (регистр и пробелы приведены к единому виду).",
        "Scheduled in CRM приведён к булевому типу; пропуски интерпретированы как False.",
        "Столбцы Dialled Number и Tag удалены, так как полностью пустые.",
    ],
    "Spend": [
        "Дубликаты строк удалены целиком, даты приведены к datetime.",
        "Числовые столбцы Impressions, Clicks, Spend приведены к числовым типам.",
        "Campaign, AdGroup, Ad сохранены даже при пропусках (кампания могла не указываться).",
    ],
    "Deals": [
        "Дубликаты по Id удалены, пустые Id и пустые Created Time удалены.",
        "Id приведены к строковому типу без потери символов; пробелы обрезаны.",
        "Stage, Quality, Payment Type нормализованы (регистр и пробелы приведены к единому виду).",
        "Source заполнен значением 'unknown', если не указан.",
        "Числовые суммы Initial Amount Paid и Offer Total Amount приведены к float.",
        "Пустые строки/текст в Initial Amount Paid и Offer Total Amount после приведения к числу стали NaN (значения не подставлялись).",
    ],
}


def load_clean_report(path: Path = REPORT_JSON_PATH) -> list[dict[str, Any]]:
    try:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def summarize_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in files:
        before = item.get("before") or {}
        after = item.get("after") or {}
        rows.append(
            {
                "name": item.get("name"),
                "rows_before": before.get("rows"),
                "cols_before": before.get("cols"),
                "rows_after": after.get("rows"),
                "cols_after": after.get("cols"),
            }
        )
    return rows


def build_dtype_rows(item: dict[str, Any]) -> list[dict[str, Any]]:
    before = item.get("before") or {}
    after = item.get("after") or {}
    d_before = before.get("dtypes") or {}
    d_after = after.get("dtypes") or {}
    cols = sorted({*d_before.keys(), *d_after.keys()})
    return [{"column": c, "before": d_before.get(c), "after": d_after.get(c)} for c in cols]


def build_nan_rows(item: dict[str, Any]) -> list[dict[str, Any]]:
    before = item.get("before") or {}
    after = item.get("after") or {}
    n_before = before.get("nan_counts") or {}
    n_after = after.get("nan_counts") or {}
    cols = sorted({*n_before.keys(), *n_after.keys()})
    rows: list[dict[str, Any]] = []
    for c in cols:
        rows.append(
            {
                "column": c,
                "description": COLUMN_DESCRIPTIONS.get(c, "-"),
                "before": n_before.get(c, 0),
                "after": n_after.get(c, 0),
            }
        )
    return rows


def layout():
    from .sidebar import get_sidebar

    files_data = load_clean_report()
    options = [{"label": f.get("name"), "value": f.get("name")} for f in files_data]
    default_value = options[0]["value"] if options else None

    summary_rows = summarize_files(files_data)

    table_common_kwargs = dict(
        style_table={"overflowX": "hidden", "width": "100%", "minWidth": 0},
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "padding": "6px",
            "fontFamily": "Inter, system-ui",
            "fontSize": 13,
            "maxWidth": 320,
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
                            html.H3("Очистка и подготовка данных"),
                            html.Div(
                                [
                                    html.Button("Обновить отчёт", id="clean-reload-btn"),
                                    dcc.ConfirmDialog(id="clean-reload-msg"),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "12px",
                                    "margin": "6px 6px 16px",
                                },
                            ),
                            dash_table.DataTable(
                                id="clean-summary-table",
                                data=summary_rows,
                                columns=[
                                    {"name": "Файл", "id": "name"},
                                    {"name": "Строк было", "id": "rows_before"},
                                    {"name": "Строк стало", "id": "rows_after"},
                                    {"name": "Столбцов было", "id": "cols_before"},
                                    {"name": "Столбцов стало", "id": "cols_after"},
                                ],
                                sort_action="native",
                                filter_action="native",
                                page_size=10,
                                **table_common_kwargs,
                            ),
                        ],
                    ),
                    html.Article(
                        [
                            html.H3("Файл"),
                            dcc.Dropdown(
                                id="clean-file-select",
                                options=options,
                                value=default_value,
                                placeholder="Выберите файл",
                                clearable=False,
                                style={"maxWidth": "520px"},
                            ),
                            html.Div(id="clean-file-meta", style={"margin": "10px 6px 10px"}),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H4("Типы столбцов (было/стало)"),
                                            dash_table.DataTable(id="clean-dtypes-table", **table_common_kwargs),
                                        ],
                                        style={"marginBottom": 18},
                                    ),
                                    html.Div(
                                        [
                                            html.H4("Пропуски (NaN)"),
                                            dash_table.DataTable(id="clean-nan-table", **table_common_kwargs),
                                        ],
                                        style={"marginBottom": 18},
                                    ),
                                    html.Div(
                                        [
                                            html.Details(
                                                open=False,
                                                children=[
                                                    html.Summary("Примечания"),
                                                    html.Div(id="clean-notes", style={"marginTop": 8}),
                                                ],
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
            ),
        ],
    )


@callback(
    Output("clean-summary-table", "data"),
    Output("clean-reload-msg", "displayed"),
    Output("clean-reload-msg", "message"),
    Input("clean-reload-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reload_clean_report(n_clicks: int):
    try:
        from src.cleaning import run_cleaning  # type: ignore

        run_cleaning()
        msg = "Очистка завершена, отчёт обновлён (reports/step2_eda_summary.json)."
    except Exception:
        msg = "Не удалось запустить очистку. Проверьте логи."
    data = load_clean_report()
    return summarize_files(data), True, msg


@callback(
    Output("clean-file-select", "options"),
    Output("clean-file-select", "value"),
    Input("clean-summary-table", "data"),
)
def update_file_options(summary_rows: list[dict[str, Any]] | None):
    rows = summary_rows or []
    options = [{"label": r.get("name"), "value": r.get("name")} for r in rows]
    value = options[0]["value"] if options else None
    return options, value


@callback(
    Output("clean-file-meta", "children"),
    Output("clean-dtypes-table", "data"),
    Output("clean-dtypes-table", "columns"),
    Output("clean-nan-table", "data"),
    Output("clean-nan-table", "columns"),
    Output("clean-notes", "children"),
    Input("clean-file-select", "value"),
)
def update_file_details(selected_name: str | None):
    files_data = load_clean_report()
    if not selected_name:
        empty_cols = [
            {"name": "Столбец", "id": "column"},
            {"name": "Было", "id": "before"},
            {"name": "Стало", "id": "after"},
        ]
        empty_nan_cols = [
            {"name": "Столбец", "id": "column"},
            {"name": "Описание столбца", "id": "description"},
            {"name": "Было", "id": "before"},
            {"name": "Стало", "id": "after"},
        ]
        return html.Div(), [], empty_cols, [], empty_nan_cols, html.Div("Данные отсутствуют.")

    item = next((x for x in files_data if x.get("name") == selected_name), None)
    if not item:
        return html.Div("Файл не найден в отчёте."), [], [], [], [], html.Div()

    meta = html.Ul(
        [
            html.Li(["Статус: ", html.B(item.get("status") or "-")]),
            html.Li(["Исходный файл: ", html.Code(item.get("path") or "-")]),
            html.Li(["Результат CSV: ", html.Code(item.get("clean_output") or "-")]),
            html.Li(["Результат Parquet: ", html.Code(item.get("clean_output_parquet") or "-")]),
        ]
    )

    dtype_rows = build_dtype_rows(item)
    dtype_cols = [
        {"name": "Столбец", "id": "column"},
        {"name": "Было", "id": "before"},
        {"name": "Стало", "id": "after"},
    ]

    nan_rows = build_nan_rows(item)
    nan_cols = [
        {"name": "Столбец", "id": "column"},
        {"name": "Описание столбца", "id": "description"},
        {"name": "Было", "id": "before"},
        {"name": "Стало", "id": "after"},
    ]

    notes_from_report = (item.get("changes") or {}).get("notes") or []
    manual_notes = CLEANING_NOTES.get(selected_name, [])
    all_notes = manual_notes + notes_from_report
    notes_block = html.Ul([html.Li(n) for n in all_notes]) if all_notes else html.Div("Примечания отсутствуют.")

    return meta, dtype_rows, dtype_cols, nan_rows, nan_cols, notes_block
