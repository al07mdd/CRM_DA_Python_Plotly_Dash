from __future__ import annotations

import sys
from pathlib import Path
from dash import Input, Output, callback, dcc, html, register_page
import plotly.express as px
import plotly.graph_objects as go

register_page(
    __name__,
    path="/viz/payments",
    name="Анализ платежей и продуктов",
    title="Final Project - Анализ платежей и продуктов",
    order=70,
)

APP_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analytics_payments import load_deals_for_payments, payment_product_metrics  # type: ignore

# Загружаем очищенные сделки один раз при импорте страницы.
DEALS_DF = load_deals_for_payments()
MONTH_OPTIONS = sorted(m for m in DEALS_DF["month"].dropna().unique())

# Целевые продукты, которые показываем в визуализации.
TARGET_PRODUCTS = ["Web Developer", "Digital Marketing", "UX/UI Design"]

# Человеко-читаемые подписи для всплывающих подсказок.
VALUE_TITLES = {
    "revenue_total": "Выручка",
    "n_deals": "Количество сделок",
    "n_paid": "Количество оплат",
}


def _empty_fig(message: str) -> go.Figure:
    """
    Создаёт пустой график с текстом-подсказкой.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
    return fig


def layout() -> html.Div:
    """
    Возвращает страницу шага 7 с заголовком и фильтрами на одной линии.
    """
    from .sidebar import get_sidebar

    controls = html.Article(
        [
            html.Div(
                [
                    html.H3("Анализ платежей и продуктов", style={"margin": "0"}),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("Метрика:", style={"fontSize": 16}),
                                    dcc.Dropdown(
                                        id="payments-value-metric",
                                        options=[
                                            {"label": "Выручка", "value": "revenue_total"},
                                            {"label": "Количество сделок", "value": "n_deals"},
                                            {"label": "Количество оплат", "value": "n_paid"},
                                        ],
                                        value="revenue_total",
                                        clearable=False,
                                        style={"minWidth": "220px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "8px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Span("Месяц:", style={"fontSize": 16}),
                                    dcc.Dropdown(
                                        id="payments-month",
                                        options=[{"label": "Все месяцы", "value": ""}]
                                        + [{"label": m, "value": m} for m in MONTH_OPTIONS],
                                        value="",
                                        clearable=False,
                                        style={"minWidth": "150px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "8px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "16px",
                            "alignItems": "flex-start",
                            "flexWrap": "wrap",
                            "marginLeft": "auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                    "alignItems": "flex-start",
                    "flexWrap": "wrap",
                    "width": "100%",
                },
            ),
        ],
        className="viz-controls",
        style={"padding": "10px 16px"},
    )

    treemap_card = html.Article(
        [
            html.H3(
                "Структура продаж по типам оплаты и продуктам (для: Web Developer, Digital Marketing, UX/UI Design)",
                id="payments-title",
            ),
            dcc.Graph(
                id="payments-treemap",
                figure=_empty_fig("Выберите параметры, чтобы построить график."),
                config={"displayModeBar": False},
                style={"width": "100%", "height": "520px"},
            ),
        ],
        className="viz-card",
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        className="viz-page",
        children=[
            get_sidebar(),
            html.Div(
                style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
                children=[controls, treemap_card],
            ),
        ],
    )


@callback(
    Output("payments-treemap", "figure"),
    Output("payments-title", "children"),
    Input("payments-month", "value"),
    Input("payments-value-metric", "value"),
)
def update_payments_treemap(month_value: str, value_metric: str):
    """
    Перестраивает TreeMap с учётом выбранного месяца и метрики размера.
    """
    df = payment_product_metrics(
        DEALS_DF,
        month=month_value or None,
        target_products=TARGET_PRODUCTS,
    )
    if df.empty or value_metric not in df.columns:
        return (
            _empty_fig("Нет данных для выбранных параметров."),
            "Структура продаж по типам оплаты и продуктам - нет данных",
        )

    plot_df = df.copy()
    for col in ["Payment Type", "Product", "Education Type"]:
        plot_df[col] = plot_df[col].fillna("unknown")

    metric_label = VALUE_TITLES.get(value_metric, value_metric)
    fig = px.treemap(
        plot_df,
        path=[px.Constant("Все сделки"), "Payment Type", "Product", "Education Type"],
        values=value_metric,
        color=value_metric,
        color_continuous_scale=[
            "rgb(99, 110, 250)",
            "rgb(180, 189, 250)",
        ],
    )
    fig.update_traces(
        hovertemplate=f"<b>%{{label}}</b><br>{metric_label}: %{{value:,.0f}}<extra></extra>",
        marker=dict(showscale=False),
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_showscale=False,
    )
    title = (
        "Структура продаж по типам оплаты и продуктам (для: Web Developer, Digital Marketing, UX/UI Design)"
        f" - метрика: {metric_label}"
    )
    return fig, title
