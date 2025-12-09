from __future__ import annotations

import math
from pathlib import Path
import sys

from dash import html, register_page, dash_table


register_page(
    __name__,
    path="/product/hypotheses",
    name="Hypotheses",
    title="Unit Economics Hypotheses",
    order=120,
)


def _project_root() -> Path:
    """
    Добавляет корень проекта в sys.path для импорта src-модулей.
    """
    app_dir = Path(__file__).resolve().parents[2]
    root = app_dir.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    return root


def _table_records(df):
    """
    Готовит данные для Dash DataTable, заменяя недопустимые значения.
    """
    records = df.to_dict("records")
    for row in records:
        for key, value in list(row.items()):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                row[key] = None
    return records


def _make_table(table_id: str, data, columns):
    """
    Создает таблицу с единым стилем для секции гипотез.
    """
    return dash_table.DataTable(
        id=table_id,
        data=data,
        columns=columns,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "whiteSpace": "pre-line",
            "height": "auto",
            "fontFamily": "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
            "fontSize": 13,
            "padding": "6px",
        },
        style_header={"textAlign": "left", "fontWeight": 600},
        css=[{"selector": ".dash-table-container", "rule": "max-width: 100%;"}],
    )


def _fmt_pct(value, digits=2):
    """
    Форматирует значение в проценты либо возвращает тире при отсутствии данных.
    """
    if value is None:
        return "-"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "-"
    return f"{value * 100:.{digits}f}%"


def _fmt_num(value, digits=0):
    """
    Форматирует число с заданным количеством знаков или возвращает тире.
    """
    if value is None:
        return "-"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "-"
    fmt = f"{{:.{digits}f}}"
    return fmt.format(value)


def layout():
    """
    Структурирует страницу гипотез (HADI + проверка) с таблицами и примечанием.
    """
    from .sidebar import get_sidebar

    _project_root()
    from src.analytics_ue import hadi_table, hypothesis_check_info  # type: ignore

    hadi_df = hadi_table()
    info_rows = hypothesis_check_info()

    business_info = None
    calc_block = None
    empty_note = None

    if info_rows:
        check_rows = []
        for row in info_rows:
            check_rows.append(
                {
                    "segment": row.get("segment"),
                    "p_base": _fmt_pct(row.get("p_base")),
                    "target": _fmt_pct(row.get("target")),
                    "delta": _fmt_pct(row.get("x_abs")),
                    "n_per_group": _fmt_num(row.get("n_per_group"), digits=0),
                    "ua_per_day": _fmt_num(row.get("ua_per_day"), digits=0),
                    "n_available": _fmt_num(row.get("n_available"), digits=0),
                    "days_required": _fmt_num(row.get("days_required"), digits=0),
                    "min_ua_per_day": _fmt_num(row.get("min_ua_per_day"), digits=0),
                    "x_mde": _fmt_pct(row.get("x_mde"), digits=3),
                    "status": "Укладываемся в 14 дней" if row.get("fits_limit") else "НЕ укладываемся в 14 дней",
                }
            )

        business_info = next((row for row in info_rows if row.get("segment") == "Business"), None)
        if business_info:
            calc_rows = [
                ("C1 база", _fmt_pct(business_info.get("p_base")), "Текущая конверсия (B / UA)"),
                ("C1 цель", _fmt_pct(business_info.get("target")), "Желаемый уровень конверсии"),
                ("x = цель - база", _fmt_pct(business_info.get("x_abs")), "Абсолютный эффект, который нужно достичь"),
                (
                    "n на группу",
                    _fmt_num(business_info.get("n_per_group"), digits=0),
                    "16 * p_base * (1 - p_base) / x^2",
                ),
                (
                    "UA/день факт",
                    _fmt_num(business_info.get("ua_per_day"), digits=0),
                    "Средний трафик по периоду",
                ),
                (
                    "n за 14 дней",
                    _fmt_num(business_info.get("n_available"), digits=0),
                    "UA/день * 14",
                ),
                (
                    "Дней для теста",
                    _fmt_num(business_info.get("days_required"), digits=0),
                    "n / (UA/день)",
                ),
                (
                    "Мин. UA/день (14 дней)",
                    _fmt_num(business_info.get("min_ua_per_day"), digits=0),
                    "n / 14 (минимальное число лидов в день)",
                ),
                (
                    "x (мин. обнаруживаемый эффект)",
                    _fmt_pct(business_info.get("x_mde"), digits=3),
                    "sqrt(16 * p * (1 - p) / n)",
                ),
            ]

            calc_block = html.Div(
                [
                    html.H4("Пример расчета (бизнес)", style={"margin": "16px 0 8px"}),
                    html.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Показатель", style={"textAlign": "left", "padding": "4px 8px"}),
                                        html.Th("Значение", style={"textAlign": "left", "padding": "4px 8px"}),
                                        html.Th("Комментарий", style={"textAlign": "left", "padding": "4px 8px"}),
                                    ]
                                )
                            ),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(name, style={"padding": "4px 8px", "fontWeight": 500}),
                                            html.Td(value, style={"padding": "4px 8px"}),
                                            html.Td(comment, style={"padding": "4px 8px", "color": "#4b5563"}),
                                        ]
                                    )
                                    for name, value, comment in calc_rows
                                ]
                            ),
                        ],
                        style={
                            "borderCollapse": "collapse",
                            "width": "100%",
                            "border": "1px solid #e5e7eb",
                        },
                    ),
                    html.P(
                        f"При нашем трафике можно обнаружить эффект, при изменении x на {_fmt_pct(business_info.get('x_mde'), digits=3)}.",
                        style={"margin": "12px 0 0", "color": "#111827"},
                    ),
                ]
            )
    else:
        check_rows = []
        empty_note = html.P(
            "Недостаточно данных для расчета: проверьте корректность исходных таблиц.",
            style={"marginTop": "12px", "color": "#ef4444"},
        )

    controls = html.Article(
        className="viz-controls",
        style={"padding": "6px 12px 6px"},
        children=[
            html.Div(
                [
                    html.H3("Гипотеза по точке роста C1 (HADI + проверка)", style={"margin": "0"}),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "4px"},
            )
        ],
    )

    hadi_card = html.Article(
        className="viz-card",
        children=[
            html.H3("HADI по точке роста C1"),
            _make_table(
                "ue-hadi-table",
                _table_records(hadi_df),
                [
                    {"name": "Блок", "id": "Часть"},
                    {"name": "Описание", "id": "Описание"},
                ],
            ),
        ],
    )

    check_children = [
        html.H3("Проверка гипотезы"),
        _make_table(
            "ue-hypothesis-check-table",
            check_rows,
            [
                {"name": "Сегмент", "id": "segment"},
                {"name": "C1 (база)", "id": "p_base"},
                {"name": "C1 (цель)", "id": "target"},
                {"name": "Δ (цель - база)", "id": "delta"},
                {"name": "n на группу", "id": "n_per_group"},
                {"name": "UA/день", "id": "ua_per_day"},
                {"name": "n за 14 дней", "id": "n_available"},
                {"name": "Дней для теста", "id": "days_required"},
                {"name": "Мин. UA/день", "id": "min_ua_per_day"},
                {"name": "x (мин. эффект)", "id": "x_mde"},
                {"name": "Статус", "id": "status"},
            ],
        ),
    ]
    if calc_block:
        check_children.append(
            html.Details(
                open=False,
                children=[
                    html.Summary("Примечание (пример расчета):"),
                    calc_block,
                    html.P(
                        "Формула минимально обнаружимого эффекта: x = sqrt(16 * p * (1 - p) / n), "
                        f"где p = {_fmt_pct(business_info.get('p_base'))} - базовая конверсия, "
                        f"n ((ua / days_total) * days_limit(14 дней)) = {_fmt_num(business_info.get('n_available'), digits=0)} - трафик на группу за 14 дней. ",
                        # f"Подставляя эти значения получаем x ≈ {_fmt_pct(business_info.get('x_mde'), digits=3)}.",
                        style={"margin": "12px 0 0", "color": "#4b5563"},
                    ),
                ],
                style={"marginTop": "12px"},
            )
        )
    if empty_note:
        check_children.append(empty_note)

    check_card = html.Article(className="viz-card", children=check_children)

    right_col = html.Div(
        style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[controls, hadi_card, check_card],
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        className="viz-page",
        children=[get_sidebar(), right_col],
    )
