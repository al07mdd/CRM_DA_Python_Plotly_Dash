from __future__ import annotations

import math
from pathlib import Path
import sys

from dash import html, register_page, dash_table


register_page(
    __name__,
    path="/product/unit-economics",
    name="Unit Economics",
    title="Unit Economics Module",
    order=90,
)


def _project_root() -> Path:
    """
    Обеспечивает доступ к корню проекта для импортов src.
    """
    app_dir = Path(__file__).resolve().parents[2]
    root = app_dir.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    return root


def _table_records(df):
    """
    Преобразует DataFrame в dict-список и заменяет NaN/inf на None.
    """
    records = df.to_dict("records")
    for row in records:
        for key, value in list(row.items()):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                row[key] = None
    return records


def _make_table(table_id: str, data, columns):
    """
    Создает DataTable с единым стилем для страницы.
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
            "maxWidth": 240,
        },
        style_header={"textAlign": "left", "fontWeight": 600},
        css=[{"selector": ".dash-table-container", "rule": "max-width: 100%;"}],
    )


METRIC_LABELS = {
    "UA": "лиды",
    "B": "клиенты",
    "AC": "маркетинговый бюджет",
    "T": "транзакции",
    "Revenue": "выручка",
    "C1": "конверсия (B/UA)",
    "CPA": "стоимость привлечения потенциального клиента",
    "CAC": "стоимость привлечения клиента",
    "AOV": "средний чек",
    "APC": "среднее кол-во сделок на клиента",
    "CLTV": "средняя валовая прибыль на клиента",
    "LTV": "средняя валовая прибыль на юнит масштабирования",
    "CM": "маржинальная прибыль",
}


def layout():
    """
    Отрисовывает страницу юнит-экономики с двумя таблицами.
    """
    from .sidebar import get_sidebar

    _project_root()
    from src.analytics_ue import unit_economics_tables  # type: ignore

    overall_df, product_df = unit_economics_tables()
    overall_reset = overall_df.rename_axis("Metric").reset_index().rename(columns={"value": "Value"})

    overall_reset["Metric"] = overall_reset["Metric"].apply(
        lambda code: f"{code} ({METRIC_LABELS.get(code)})" if METRIC_LABELS.get(code) else code
    )

    product_reset = product_df.reset_index()

    controls = html.Article(
        className="viz-controls",
        style={"padding": "6px 12px 6px"},
        children=[
            html.Div(
                [
                    html.H3("Расчет базовых метрик и юнит-экономики", style={"margin": "0"}),
                    html.P(
                        "Все показатели строятся по очищенным parquet-файлам data/clean (Deals, Contacts, Calls, Spend).",
                        style={"margin": "4px 0 0", "color": "#4b5563"},
                    ),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "4px"},
            )
        ],
    )

    cards = html.Div(
        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            html.Article(
                className="viz-card",
                children=[
                    html.H3("Юнит-экономика (по бизнесу в целом)"),
                    _make_table(
                        "ue-overall-table",
                        _table_records(overall_reset),
                        [
                            {"name": "Метрика", "id": "Metric"},
                            {"name": "Значение", "id": "Value"},
                        ],
                    ),
                ],
            ),
            html.Article(
                className="viz-card",
                children=[
                    html.H3("Юнит-экономика (по продуктам)"),
                    _make_table(
                        "ue-products-table",
                        _table_records(product_reset),
                        [
                            {"name": "Продукт", "id": "Product"},
                            {"name": "UA", "id": "UA"},
                            {"name": "B", "id": "B"},
                            {"name": "AC", "id": "AC"},
                            {"name": "T", "id": "T"},
                            {"name": "Revenue", "id": "Revenue"},
                            {"name": "C1 (%)", "id": "C1"},
                            {"name": "CPA", "id": "CPA"},
                            {"name": "AOV", "id": "AOV"},
                            {"name": "APC", "id": "APC"},
                            {"name": "CLTV", "id": "CLTV"},
                            {"name": "LTV", "id": "LTV"},
                            {"name": "CM", "id": "CM"},
                        ],
                    ),
                ],
            ),
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
