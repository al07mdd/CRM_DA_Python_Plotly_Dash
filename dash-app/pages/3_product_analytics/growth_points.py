from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd
from dash import html, register_page, dash_table


register_page(
    __name__,
    path="/product/growth-points",
    name="Growth Points",
    title="Unit Economics Growth Points",
    order=100,
)


def _slug(text: str) -> str:
    """
    Генерирует безопасный идентификатор для использования в id таблиц.
    """
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "segment"


def _project_root() -> Path:
    """
    Гарантирует доступ к корню проекта для импорта src. модулей.
    """
    app_dir = Path(__file__).resolve().parents[2]
    root = app_dir.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    return root


def _table_records(df: pd.DataFrame | None):
    """
    Конвертирует DataFrame в список словарей и очищает NaN для таблиц Dash.
    """
    if df is None:
        return []
    records = df.to_dict("records")
    for row in records:
        for key, value in list(row.items()):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                row[key] = None
    return records


def _highlight_rules(df: pd.DataFrame, key_cols: list[str], *, full_row: bool = False):
    """
    Возвращает правила подсветки строк с максимальным приростом CM.
    """
    if df.empty or "CM_delta_%" not in df.columns:
        return []
    max_val = df["CM_delta_%"].max()
    if pd.isna(max_val):
        return []
    targets = df[df["CM_delta_%"] == max_val]
    rules = []
    for _, row in targets.iterrows():
        clauses = [f"{{{col}}} = '{row[col]}'" for col in key_cols]
        query = " && ".join(clauses)
        style = {
            "if": {"filter_query": query},
            "backgroundColor": "rgba(70, 150, 200, 0.18)", 
        }
        if not full_row:
            style["column_id"] = "CM_delta_%"
        rules.append(style)
    return rules


def _make_table(table_id: str, data, columns, *, style_data_conditional=None):
    """
    Создает настроенную Dash DataTable с общим стилем раздела.
    """
    return dash_table.DataTable(
        id=table_id,
        data=data,
        columns=columns,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "fontFamily": "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
            "fontSize": 13,
            "padding": "6px",
        },
        style_header={"textAlign": "left", "fontWeight": 600},
        style_data_conditional=style_data_conditional or [],
        css=[{"selector": ".dash-table-container", "rule": "max-width: 100%;"}],
    )


def layout():
    """
    Отрисовывает страницу точек роста с двумя контейнерами таблиц.
    """
    from .sidebar import get_sidebar

    _project_root()
    from src.analytics_ue import growth_scenarios_table  # type: ignore

    growth_df = growth_scenarios_table().sort_values(["Segment", "Metric"]).reset_index(drop=True)
    business_df = growth_df[growth_df["Segment"] == "Business"].drop(columns=["Segment"]).reset_index(drop=True)
    product_df = growth_df[growth_df["Segment"] != "Business"].reset_index(drop=True)

    controls = html.Article(
        className="viz-controls",
        style={"padding": "6px 12px 6px"},
        children=[
            html.Div(
                [
                    html.H3("Поиск точек роста (для бизнеса в целом и по отдельным продуктам)", style={"margin": "0"}),
                    html.P(
                        "Каждый сценарий меняет одну метрику на ±10% (CPA уменьшается) и показывает эффект на CM.",
                        style={"margin": "4px 0 0", "color": "#4b5563"},
                    ),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "4px"},
            )
        ],
    )

    segments = [seg for seg in product_df["Segment"].dropna().unique()]

    product_cards = [
        html.Article(
            className="viz-card",
            children=[
                html.H3(f"Точки роста: {segment}"),
                _make_table(
                    f"ue-growth-{_slug(segment)}",
                    _table_records(
                        segment_df := product_df[product_df["Segment"] == segment]
                        .drop(columns=["Segment"])
                        .reset_index(drop=True)
                    ),
                    [
                        {"name": "Метрика", "id": "Metric"},
                        {"name": "Базовая CM", "id": "CM_base"},
                        {"name": "Новая CM", "id": "CM_new"},
                        {"name": "Δ CM", "id": "CM_delta"},
                        {"name": "Δ CM (%)", "id": "CM_delta_%"},
                    ],
                    style_data_conditional=_highlight_rules(segment_df, ["Metric"], full_row=True),
                ),
            ],
        )
        for segment in segments
    ]

    cards = html.Div(
        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            html.Article(
                className="viz-card",
                children=[
                    html.H3("Точки роста (по бизнесу в целом):"),
                    _make_table(
                        "ue-growth-business",
                        _table_records(business_df),
                        [
                            {"name": "Метрика", "id": "Metric"},
                            {"name": "Базовый CM", "id": "CM_base"},
                            {"name": "Новый CM", "id": "CM_new"},
                            {"name": "Δ CM", "id": "CM_delta"},
                            {"name": "Δ CM (%)", "id": "CM_delta_%"},
                        ],
                        style_data_conditional=_highlight_rules(business_df, ["Metric"], full_row=True),
                    ),
                ],
            ),
            *product_cards,
        ],
    )

    right_col = html.Div(
        style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[controls, cards],
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        className="viz-page",
        children=[get_sidebar(), right_col],
    )
