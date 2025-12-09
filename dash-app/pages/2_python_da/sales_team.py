from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from dash import Input, Output, State, callback, dcc, html, register_page
import plotly.express as px
import plotly.graph_objects as go


register_page(
    __name__,
    path="/viz/sales",
    name="Отдел продаж",
    title="Визуализации - Отдел продаж",
    order=60,
)

APP_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analytics_sales import load_deals_calls, owner_metrics  # type: ignore

DEALS_DF, CALLS_DF = load_deals_calls()
DEALS_DF = DEALS_DF[DEALS_DF["deal_owner"].notna()]
MONTH_OPTIONS = sorted(m for m in DEALS_DF["month"].dropna().unique())
BASE_METRICS = owner_metrics(DEALS_DF, CALLS_DF, month=None)
DEFAULT_OWNER = (
    BASE_METRICS["owners"].sort_values("revenue_won", ascending=False)["deal_owner"].iloc[0]
    if len(BASE_METRICS["owners"])
    else None
)
OWNER_MONTHS = DEALS_DF.groupby("deal_owner")["month"].nunique().to_dict()
TOP_N = 15
METRIC_INFO = {
    "revenue_won": ("Ожидаемая выручка", "(Сумма Offer Total Amount по выигранным сделкам)"),
    "cr_processed_to_paid": ("CR обработанных - оплату", "(Доля оплаченных среди обработанных сделок)"),
    "n_processed": ("Обработанные сделки", "(Количество сделок с закрытием или звонком)"),
    "revenue_per_deal": ("Средняя выручка на сделку", "(Выручка / все сделки менеджера)"),
    "revenue_per_paid": ("Средняя выручка на оплату", "(Выручка / оплаченные сделки)"),
    "calls_cnt_per_processed": ("Звонков на обработанную", "(В среднем звонков на обработанную сделку)"),
    "avg_lead_to_first_call_hours": ("Средний SLA", "(Значение SLA из Deals в часах)"),
    "lost_rate_by_closed": ("Доля потерь среди обработанных", "(Потери / обработанные сделки)"),
    "n_lost": ("Потерянные сделки", "(Количество сделок в статусе lost)"),
}


def _apply_viz_style(fig: go.Figure) -> go.Figure:
    """
    Единое оформление графиков (фон, отступы, hover).
    """
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=12, t=20, b=20),
        hovermode="closest",
    )
    return fig


def _empty_fig(message: str) -> go.Figure:
    """
    Пустой график-заглушка с текстом, когда нет данных.
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
    return _apply_viz_style(fig)


def _format_currency(value: float) -> str:
    """
    Форматирует денежные значения с пробелами и без копеек.
    """
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}".replace(",", " ")


def _format_pct(value: float) -> str:
    """
    Форматирует доли и проценты.
    """
    if pd.isna(value):
        return "-"
    return f"{value * 100:.1f}%"


def _format_metric_display(metric: str, value: float) -> str:
    """
    Возвращает строку для подписи выбранной метрики (учитывает тип).
    """
    if pd.isna(value):
        return "-"
    if metric in {"cr_processed_to_paid", "lost_rate_by_closed"}:
        return f"{value:.1%}"
    if metric in {"calls_cnt_per_processed", "avg_lead_to_first_call_hours"}:
        suffix = " ч" if metric == "avg_lead_to_first_call_hours" else ""
        return f"{value:.1f}{suffix}"
    if metric in {"revenue_won", "revenue_per_deal", "revenue_per_paid"}:
        return _format_currency(value)
    return f"{value:,.0f}".replace(",", " ")


def _kpi_block(title: str, value: str, caption: str) -> html.Div:
    """
    Стандартизированный блок KPI с заголовком, значением и подписью.
    """
    return html.Div(
        [
            html.Div(title, className="kpi-title"),
            html.Div(value, className="kpi-value"),
            html.Div(caption, className="kpi-caption"),
        ],
        style={
            "padding": "12px",
            "border": "1px solid #e5e7eb",
            "borderRadius": "8px",
            "display": "flex",
            "flexDirection": "column",
            "gap": "4px",
            "minWidth": "140px",
        },
    )


def layout():
    """
    Конструирует страницу Dash: фильтры, KPI, лидерборд, профиль менеджера.
    """
    from .sidebar import get_sidebar

    controls = html.Article(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Анализ эффективности продаж", style={"margin": "0 0 8px"}),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Метрика:"),
                            dcc.Dropdown(
                                id="sales-metric",
                                options=[
                                    {"label": "Ожидаемая выручка", "value": "revenue_won"},
                                    {"label": "Конверсия обработанных в оплату", "value": "cr_processed_to_paid"},
                                    {"label": "Обработанные сделки", "value": "n_processed"},
                                    {"label": "Средняя выручка на сделку", "value": "revenue_per_deal"},
                                    {"label": "Средняя выручка на оплату", "value": "revenue_per_paid"},
                                    {"label": "Звонков на обработанную", "value": "calls_cnt_per_processed"},
                                    {"label": "Средний SLA до первого звонка", "value": "avg_lead_to_first_call_hours"},
                                    {"label": "Доля потерь среди обработанных", "value": "lost_rate_by_closed"},
                                    {"label": "Потерянные сделки", "value": "n_lost"},
                                ],
                                value="revenue_won",
                                clearable=False,
                                style={"minWidth": "300px", "zIndex": 5, "lineHeight": "28px"},
                            ),
                            html.Label("Мин. обработанных сделок:"),
                            dcc.Input(
                                id="sales-min-processed",
                                type="number",
                                value=10,
                                min=0,
                                step=5,
                                style={"width": "100px"},
                            ),
                            html.Label("Месяц:"),
                            dcc.Dropdown(
                                id="sales-month",
                                options=[{"label": "Все периоды", "value": ""}]
                                + [{"label": m, "value": m} for m in MONTH_OPTIONS],
                                value="",
                                clearable=False,
                                style={"minWidth": "150px", "zIndex": 5},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "12px",
                            "alignItems": "flex-end",
                            "flexWrap": "wrap",
                            "marginLeft": "auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "gap": "16px",
                    "width": "100%",
                },
            )
        ],
        className="viz-controls",
        style={"padding": "10px 16px"},
    )

    kpi_card = html.Article(
        [
            html.Div(
                id="sales-kpi",
                style={"display": "grid", "gap": "12px", "gridTemplateColumns": "repeat(4, minmax(180px, 1fr))"},
            )
        ],
        className="viz-card",
    )

    leaderboard_card = html.Article(
        [
            html.H3("Рейтинг менеджеров", id="sales-leaderboard-title"),
            dcc.Graph(
                id="sales-leaderboard",
                figure=_empty_fig("Выберите параметры чтобы увидеть лидеров."),
                config={"displayModeBar": False},
                style={"width": "100%", "height": "420px"},
            ),
        ],
        className="viz-card",
    )

    profile_card = html.Article(
        [
            html.H3("Профиль менеджера: менеджер не выбран", id="sales-profile-title"),
            dcc.Dropdown(
                id="sales-owner-select",
                options=[],
                value=DEFAULT_OWNER,
                placeholder="Выберите менеджера",
                clearable=False,
                style={"maxWidth": "260px", "zIndex": 5},
            ),
            html.Div(
                id="sales-owner-kpi",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, minmax(150px, 1fr))",
                    "gap": "12px",
                },
            ),
        ],
        className="viz-card",
    )

    metrics_rows = [
        ("n_deals", "Все лиды менеджера", "count сделок по Deal Owner"),
        ("n_processed", "Обработанные сделки", "sum(is_closed или был звонок)"),
        ("n_paid", "Оплаченные сделки", "Stage содержит “payment done”"),
        ("n_lost", "Потерянные сделки", "Stage содержит “lost” (кроме оплаченых)"),
        ("revenue_won", "Ожидаемая выручка", "sum(Offer Total Amount) по n_paid"),
        ("revenue_per_deal", "Средняя выручка на сделку", "revenue_won / n_deals"),
        ("revenue_per_paid", "Средний чек", "revenue_won / n_paid"),
        ("cr_deals_to_paid", "CR всех лидов в оплату", "n_paid / n_deals"),
        ("cr_processed_to_paid", "CR обработанных в оплату", "n_paid / n_processed"),
        ("calls_cnt_per_processed", "Звонков на обработанную", "calls_cnt_total / n_processed"),
        ("calls_coverage", "Обработка со звонком", "n_processed_with_calls / n_processed"),
        ("avg_lead_to_first_call_hours", "Средний SLA", "SLA из Deals (часы)"),
        ("lost_rate_by_closed", "Потери среди обработанных", "n_lost / n_processed"),
    ]

    header_style = {"padding": "6px 8px", "textAlign": "left", "borderBottom": "1px solid #e5e7eb"}
    cell_style = {"padding": "6px 8px", "borderBottom": "1px solid #f1f5f9", "verticalAlign": "top"}

    metrics_note = html.Article(
        className="viz-card",
        children=[
            html.Details(
                [
                    html.Summary("Примечание по метрикам"),
                    html.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Метрика", style=header_style),
                                        html.Th("Что значит", style=header_style),
                                        html.Th("Как считаем", style=header_style),
                                    ]
                                )
                            ),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(metric, style=cell_style),
                                            html.Td(desc, style=cell_style),
                                            html.Td(formula, style=cell_style),
                                        ]
                                    )
                                    for metric, desc, formula in metrics_rows
                                ]
                            ),
                        ],
                        style={
                            "width": "100%",
                            "borderCollapse": "collapse",
                            "marginTop": "10px",
                        },
                    ),
                ]
            )
        ],
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        className="viz-page",
        children=[
            get_sidebar(),
            dcc.Store(id="sales-data-store"),
            html.Div(
                style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
                children=[controls, kpi_card, leaderboard_card, profile_card, metrics_note],
            ),
        ],
    )


def _build_overall_kpi(df: pd.DataFrame) -> List[html.Div]:
    """
    Собирает KPI по всей выборке с учётом пустых данных.
    """
    if df.empty:
        return [
            _kpi_block("Выручка", "-", "Нет подходящих менеджеров."),
            _kpi_block("Обработано", "-", ""),
            _kpi_block("CR обработанных - оплату", "-", ""),
            _kpi_block("Доля потерь среди обработанных", "-", ""),
        ]

    total_revenue = df["revenue_won"].sum()
    total_processed = df["n_processed"].sum()
    avg_conv = df["cr_processed_to_paid"].replace([np.inf, -np.inf], pd.NA).mean(skipna=True)
    avg_lost = df["lost_rate_by_closed"].replace([np.inf, -np.inf], pd.NA).mean(skipna=True)

    return [
        _kpi_block("Ожидаемая выручка", _format_currency(total_revenue), "Сумма продаж по выбранному периоду."),
        _kpi_block("Обработано сделок", f"{int(total_processed):,}".replace(",", " "), "Количество обработанных сделок."),
        _kpi_block("CR обработанных в оплату", _format_pct(avg_conv), "Средняя конверсия оплаченных."),
        _kpi_block("Доля потерь среди обработанных", _format_pct(avg_lost), "Процент потерянных среди обработанных."),
    ]


@callback(
    Output("sales-kpi", "children"),
    Output("sales-leaderboard", "figure"),
    Output("sales-leaderboard-title", "children"),
    Output("sales-owner-select", "options"),
    Output("sales-owner-select", "value"),
    Output("sales-data-store", "data"),
    Input("sales-month", "value"),
    Input("sales-metric", "value"),
    Input("sales-min-processed", "value"),
    Input("sales-leaderboard", "clickData"),
    State("sales-owner-select", "value"),
)
def update_sales_overview(
    month_value: str,
    metric: str,
    min_processed: Optional[float],
    click_data: Optional[dict],
    current_owner: Optional[str],
):
    """
    Основной колбэк: считает агрегаты, обновляет KPI, график и список менеджеров.
    """
    result = owner_metrics(DEALS_DF, CALLS_DF, month=month_value or None)
    owners = result["owners"].copy()
    owners["deal_owner"] = owners["deal_owner"].fillna("Не указан")

    min_processed = int(min_processed or 0)
    owners = owners[owners["n_processed"] >= min_processed]

    figure = _empty_fig("Нет данных для выбранных фильтров.")
    options = [{"label": o, "value": o} for o in owners["deal_owner"]]
    selected_owner = current_owner
    store_data = {
        "owners": owners.to_dict("records"),
        "lost": result["lost_reason_by_owner"].fillna({"lost_reason": "Не указано"}).to_dict("records"),
    }

    label, desc = METRIC_INFO.get(metric, ("Показатель", "Описание недоступно."))
    leaderboard_title = f"Рейтинг менеджеров - {label}. {desc}"

    if owners.empty:
        kpi = _build_overall_kpi(owners)
        return kpi, figure, leaderboard_title, options, None, store_data

    owners = owners.sort_values(metric, ascending=False)
    bar_df = owners.head(TOP_N).sort_values(metric, ascending=True)
    bar_df = bar_df.assign(metric_display=bar_df[metric].apply(lambda v: _format_metric_display(metric, v)))
    custom_cols = [
        "deal_owner",
        "n_processed",
        "revenue_won",
        "cr_processed_to_paid",
        "lost_rate_by_closed",
        "calls_cnt_per_processed",
        "revenue_per_deal",
        "revenue_per_paid",
        "avg_lead_to_first_call_hours",
        "n_lost",
    ]
    fig = px.bar(
        bar_df,
        x=metric,
        y="deal_owner",
        orientation="h",
        custom_data=bar_df[custom_cols],
        title="",
        text=bar_df["metric_display"],
    )
    fig = _apply_viz_style(fig)
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=20, r=12, t=20, b=20),
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            f"{label}: %{{text}}<br>"
            "Обработанные сделки: %{customdata[1]:,.0f}<br>"
            "Ожидаемая выручка: %{customdata[2]:,.0f}<br>"
            "CR обработанных - оплату: %{customdata[3]:.2%}<br>"
            "Доля потерь среди обработанных: %{customdata[4]:.2%}<br>"
            "Звонков на обработанную: %{customdata[5]:.2f}<br>"
            "Средняя выручка на сделку: %{customdata[6]:,.0f}<br>"
            "Средняя выручка на оплату: %{customdata[7]:,.0f}<br>"
            "Средний SLA: %{customdata[8]:.1f} ч<br>"
            "Потерянные сделки: %{customdata[9]:,.0f}<br>"
            "<extra></extra>"
        ),
    )
    # Альтернативный вид (Treemap) для возможного будущего использования.
    # fig = go.Figure(
    #     go.Treemap(
    #         labels=bar_df["deal_owner"],
    #         parents=[""] * len(bar_df),
    #         values=bar_df[metric],
    #         customdata=bar_df[custom_cols],
    #         text=bar_df["metric_display"],
    #     )
    # )
    # fig = _apply_viz_style(fig)
    # fig.update_traces(
    #     texttemplate="<b>%{label}</b><br>%{text}",
    #     textfont=dict(size=18),
    #     marker=dict(line=dict(color="#ffffff", width=1)),
    #     root_color="rgba(0,0,0,0)",
    #     tiling=dict(pad=6),
    #     hovertemplate=(
    #         "<b>%{customdata[0]}</b><br>"
    #         f"{label}: %{{text}}<br>"
    #         "Обработанные сделки: %{customdata[1]:,.0f}<br>"
    #         "Ожидаемая выручка: %{customdata[2]:,.0f}<br>"
    #         "CR обработанных - оплату: %{customdata[3]:.2%}<br>"
    #         "Доля потерь среди обработанных: %{customdata[4]:.2%}<br>"
    #         "Звонков на обработанную: %{customdata[5]:.2f}<br>"
    #         "Средняя выручка на сделку: %{customdata[6]:,.0f}<br>"
    #         "Средняя выручка на оплату: %{customdata[7]:,.0f}<br>"
    #         "Средний SLA до звонка: %{customdata[8]:.1f} ч<br>"
    #         "Потерянные сделки: %{customdata[9]:,.0f}<br>"
    #         "<extra></extra>"
    #     )
    # )

    if click_data and click_data.get("points"):
        selected_owner = click_data["points"][0]["customdata"][0]

    if selected_owner not in owners["deal_owner"].values:
        selected_owner = owners["deal_owner"].iloc[-1]

    return _build_overall_kpi(owners), fig, leaderboard_title, options, selected_owner, store_data


@callback(
    Output("sales-profile-title", "children"),
    Output("sales-owner-kpi", "children"),
    Input("sales-owner-select", "value"),
    Input("sales-data-store", "data"),
)
def update_owner_profile(owner_name: Optional[str], store_data: Optional[dict]):
    """
    Формирует заголовок и KPI выбранного менеджера на основании сохранённых данных.
    """
    default_title = "Профиль менеджера: менеджер не выбран"
    if not owner_name or not store_data:
        return default_title, [_kpi_block("Нет данных", "-", "Выберите менеджера из рейтинга")]

    owners_df = pd.DataFrame(store_data.get("owners", []))
    if owners_df.empty:
        return default_title, [_kpi_block("Нет данных", "-", "Нет менеджеров в выборке")]

    row = owners_df[owners_df["deal_owner"] == owner_name]
    if row.empty:
        return default_title, [_kpi_block("Нет данных", "-", "Менеджер отсутствует в фильтре")]

    row = row.iloc[0]
    months_active = OWNER_MONTHS.get(owner_name, 0)
    title_text = f"Профиль менеджера: {owner_name} (работает - {months_active} мес.)"
    per_month_processed = row["n_processed"] / months_active if months_active else 0
    per_month_revenue = row["revenue_won"] / months_active if months_active else 0

    owner_kpi = [
        _kpi_block(
            "Обработано",
            f"{int(row['n_processed']):,}".replace(",", " "),
            f"Сделок с закрытием или звонком. В месяц ≈ {per_month_processed:,.0f}",
        ),
        _kpi_block(
            "Ожидаемая выручка",
            _format_currency(row["revenue_won"]),
            f"Начислено по выигранным сделкам. В месяц ≈ {_format_currency(per_month_revenue)}",
        ),
        _kpi_block("Средний чек", _format_currency(row.get("revenue_per_paid")), "Выручка на выигранную сделку."),
        _kpi_block("CR обработанных - оплату", _format_pct(row["cr_processed_to_paid"]), "Конверсия в оплату."),
        _kpi_block(
            "Доля потерь среди обработанных",
            _format_pct(row["lost_rate_by_closed"]),
            "Среди обработанных сделок (в среднем за период).",
        ),
        _kpi_block(
            "Звонков на сделку",
            f"{row['calls_cnt_per_processed']:.1f}" if pd.notna(row["calls_cnt_per_processed"]) else "-",
            "Среднее количество звонков на обработанную сделку.",
        ),
        _kpi_block(
            "Средний SLA",
            f"{row['avg_lead_to_first_call_hours']:.1f} ч" if pd.notna(row["avg_lead_to_first_call_hours"]) else "—",
            "Показатель SLA из Deals (часы).",
        ),
    ]

    lost_df = pd.DataFrame(store_data.get("lost", []))
    lost_df = lost_df[lost_df["deal_owner"] == owner_name]
    if lost_df.empty:
        owner_kpi.append(_kpi_block("Топ причина потерь", "-", "У менеджера нет потерянных сделок."))
        return title_text, owner_kpi

    lost_df = lost_df.sort_values("n_lost", ascending=False)
    total_lost = lost_df["n_lost"].sum()
    top_row = lost_df.iloc[0]
    share = (top_row["n_lost"] / total_lost) if total_lost else 0
    owner_kpi.append(
        _kpi_block(
            "Топ причина потерь",
            str(top_row["lost_reason"]) if pd.notna(top_row["lost_reason"]) else "-",
            f"Доля: {share:.1%}, сделок: {int(top_row['n_lost'])}",
        )
    )

    return title_text, owner_kpi
