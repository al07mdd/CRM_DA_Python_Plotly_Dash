from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dash import dash_table, dcc, html, register_page, callback, Input, Output, State, ctx
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _apply_viz_style(fig: go.Figure) -> go.Figure:
    """
    Единый стиль для графиков: фон, оси, шрифты, hover.
    """
    grid = "rgba(0,0,0,0.08)"
    axisline = "rgba(0,0,0,0.18)"
    font_color = "#1f2937"
    colorway = [
        "#2563eb", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#14b8a6",
        "#6366f1", "#0ea5e9", "#ec4899", "#22c55e", "#f97316", "#84cc16",
    ]
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        colorway=colorway,
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial", size=12, color=font_color),
        hoverlabel=dict(bgcolor="#fff", bordercolor="#e5e7eb", font=dict(color="#111111")),
        bargap=0.12,
        margin=dict(l=52, r=12, t=30, b=32),
        uirevision="campaigns",
        legend=dict(itemsizing="constant"),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        showline=True,
        linecolor=axisline,
        ticks="outside",
        ticklen=4,
        showspikes=False,
        automargin=True,
        title_standoff=8,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        showline=True,
        linecolor=axisline,
        ticks="outside",
        ticklen=4,
        showspikes=False,
        automargin=True,
        title_standoff=12,
    )
    try:
        fig.for_each_trace(lambda t: t.update(line=dict(width=2)) if hasattr(t, "line") else None)
    except Exception:
        pass
    return fig


register_page(
    __name__,
    path="/viz/campaigns",
    name="Эффективность кампаний",
    title="Аналитика кампаний и источников",
    order=50,
)


def _load_opts(source_metrics: pd.DataFrame, campaign_metrics: pd.DataFrame, adgroup_metrics: pd.DataFrame):
    """
    Готовит списки опций для фильтров source/campaign/adgroup.
    """
    src_opts = [{"label": s, "value": s} for s in sorted(source_metrics["source"].unique()) if s]
    camp_opts = [{"label": c, "value": c} for c in sorted(campaign_metrics["campaign"].unique()) if c]
    ad_opts = [{"label": a, "value": a} for a in sorted(adgroup_metrics["adgroup"].unique()) if a]
    return src_opts, camp_opts, ad_opts


def _scatter_sources(src_table: pd.DataFrame) -> go.Figure:
    """
    Строит два scatter-плота по источникам: spend - paid и CPC - CR.
    """
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Затраты vs оплаты (размер - лиды)", "CPC vs CR (размер - затраты)"])
    if len(src_table):
        fig1 = px.scatter(
            src_table,
            x="spend",
            y="paid",
            size="leads",
            color="source",
            hover_name="source",
            hover_data=["revenue", "cpl", "cpa"],
            size_max=60,
        )
        fig2 = px.scatter(
            src_table,
            x="cpc",
            y="cr",
            size="spend",
            color="source",
            hover_name="source",
            hover_data=["revenue", "paid", "leads"],
            size_max=40,
        )
        for tr in fig1.data:
            tr.showlegend = True
            tr.update(marker=dict(opacity=0.9, line=dict(color="rgba(0,0,0,0.25)", width=0.6), sizemin=8))
            fig.add_trace(tr, row=1, col=1)
        for tr in fig2.data:
            tr.showlegend = False
            tr.update(marker=dict(opacity=0.9, line=dict(color="rgba(0,0,0,0.25)", width=0.6), sizemin=8))
            fig.add_trace(tr, row=1, col=2)
    fig.update_xaxes(title_text="Spend", row=1, col=1)
    fig.update_yaxes(title_text="Paid (кол-во оплат)", row=1, col=1)
    fig.update_xaxes(title_text="CPC", row=1, col=2)
    fig.update_yaxes(title_text="CR (lead -> paid)", row=1, col=2)
    fig = _apply_viz_style(fig)
    return fig


def _build_cols(df: pd.DataFrame) -> list[dict]:
    """
    Готовит колонки DataTable по датафрейму.
    """
    cols = []
    for col in df.columns:
        col_conf: dict = {"name": col, "id": col}
        if pd.api.types.is_numeric_dtype(df[col]):
            col_conf["type"] = "numeric"
        cols.append(col_conf)
    return cols


def layout():
    """
    Собирает layout страницы кампаний: фильтры, воронки, ROAS, графики.
    """
    from .sidebar import get_sidebar

    APP_DIR = Path(__file__).resolve().parents[2]
    PROJECT_ROOT = APP_DIR.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))
    from src.analytics_campaigns import load_campaign_data, compute_all_metrics  # type: ignore

    deals, spend = load_campaign_data()
    base = compute_all_metrics(deals, spend)
    base_funnel = base["funnel"]
    src_table = base["source_metrics"].sort_values(["roas", "paid"], ascending=[False, False])
    camp_table = base["campaign_metrics"]
    ad_table = base["adgroup_metrics"]
    src_opts, camp_opts, ad_opts = _load_opts(src_table, camp_table, ad_table)

    funnel_cols = [
        {"name": "Этап", "id": "этап"},
        {"name": "Количество", "id": "количество", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Конверсия в следующий этап, %", "id": "конверсия в следующий этап, %", "type": "numeric", "format": {"specifier": ".3f"}},
    ]
    roas_cols = [
        {"name": "Источник", "id": "source"},
        {"name": "ROAS", "id": "roas", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Revenue", "id": "revenue", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Spend", "id": "spend", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "CPA", "id": "cpa", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "CPL", "id": "cpl", "type": "numeric", "format": {"specifier": ",.0f"}},
    ]

    fig_scatter = _scatter_sources(src_table)

    table_css = [
        {"selector": ".dash-table-container", "rule": "padding: 0 !important; margin: 0 !important;"},
        {"selector": ".dash-spreadsheet-container", "rule": "padding: 0 !important; margin: 0 !important;"},
    ]

    metrics_table_cols = _build_cols(src_table)

    store_data = {
        "deals": deals[["id", "campaign", "source", "adgroup", "stage", "revenue_value", "is_paid"]].to_dict("records"),
        "spend": spend[["campaign", "source", "adgroup", "impressions", "clicks", "spend"]].to_dict("records"),
    }

    controls = html.Article(
        [
            html.Div(
                [
                    html.H3("Анализ эффективности кампаний", style={"margin": "0 0 4px"}),
                    html.Div(
                        [
                            html.Button("Обновить отчёт", id="camp-reload-btn"),
                        ],
                        style={"display": "flex", "gap": "8px"},
                    ),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "6px"},
            ),
            html.Div(
                [
                    dcc.Dropdown(id="camp-filter-source", options=src_opts, placeholder="Source", style={"minWidth": 180}),
                    dcc.Dropdown(id="camp-filter-campaign", options=camp_opts, placeholder="Campaign", style={"minWidth": 180}),
                    dcc.Dropdown(id="camp-filter-adgroup", options=ad_opts, placeholder="AdGroup", style={"minWidth": 180}),
                ],
                style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "justifyContent": "flex-end"},
            ),
        ],
        style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "gap": "12px", "width": "100%"},
        className="viz-controls",
    )

    baseline_card = html.Article(
        [
            html.H3("Воронка (общая)", style={"margin": "0 0 8px"}),
            dash_table.DataTable(
                id="camp-funnel-base",
                data=base_funnel.to_dict("records"),
                columns=funnel_cols,
                style_table={"overflowX": "hidden", "width": "100%", "height": "100%", "padding": "0", "margin": "0"},
                style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "Inter, system-ui", "fontSize": 13},
                style_header={"fontWeight": 600},
                css=table_css,
            ),
        ],
        className="viz-card",
        style={"flex": 1, "minWidth": "320px", "display": "flex", "flexDirection": "column", "height": "240px"},
    )

    filtered_card = html.Article(
        [
            html.H3("Воронка (+ фильтры)", style={"margin": "0 0 8px"}),
            dash_table.DataTable(
                id="camp-funnel-filtered",
                data=base_funnel.to_dict("records"),
                columns=funnel_cols,
                style_table={"overflowX": "hidden", "width": "100%", "height": "100%", "padding": "0", "margin": "0"},
                style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "Inter, system-ui", "fontSize": 13},
                style_header={"fontWeight": 600},
                css=table_css,
            ),
        ],
        className="viz-card",
        style={"flex": 1, "minWidth": "320px", "display": "flex", "flexDirection": "column", "height": "240px"},
    )

    roas_card = html.Article(
        [
            html.H3("Топ источников по окупаемости (ROAS: revenue / spend)"),
            dash_table.DataTable(
                id="camp-roas-table",
                data=src_table[["source", "roas", "revenue", "spend", "cpa", "cpl"]].to_dict("records"),
                columns=roas_cols,
                style_table={"overflowX": "hidden", "width": "100%"},
                style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "Inter, system-ui", "fontSize": 13},
                style_header={"fontWeight": 600},
            ),
        ],
        className="viz-card",
    )

    scatter_card = html.Article(
        [
            html.H3("Сравнение источников"),
            dcc.Graph(id="camp-scatter", figure=fig_scatter, className="viz-graph", config={"displayModeBar": False, "responsive": True}, style={"width": "100%", "height": "360px"}),
        ],
        className="viz-card",
    )

    metrics_card = html.Article(
        [
            html.Details(
                open=False,
                children=[
                    html.Summary("Метрики и таблицы"),
                    html.P("Справочник метрик и полные таблицы (campaign/source/adgroup)."),
                    dash_table.DataTable(
                        data=[
                            {"Метрика": "ctr (click-through rate)", "Суть": "Клики / показы", "Формула": "clicks / impressions"},
                            {"Метрика": "cpc (cost per click)", "Суть": "Стоимость клика", "Формула": "spend / clicks"},
                            {"Метрика": "cpl (cost per lead)", "Суть": "Стоимость лида", "Формула": "spend / leads"},
                            {"Метрика": "cpa (cost per acquisition)", "Суть": "Стоимость оплаты", "Формула": "spend / paid"},
                            {"Метрика": "cr (lead / paid conversion rate)", "Суть": "Конверсия лид / оплата", "Формула": "paid / leads"},
                            {"Метрика": "roas (return on ad spend)", "Суть": "Окупаемость расходов", "Формула": "revenue / spend"},
                            {"Метрика": "click_to_lead", "Суть": "Конверсия кликов в лиды", "Формула": "leads / clicks"},
                            {"Метрика": "lead_to_paid", "Суть": "Конверсия лидов в оплату", "Формула": "paid / leads"},
                        ],
                        columns=[{"name": c, "id": c} for c in ["Метрика", "Суть", "Формула"]],
                        style_table={"overflowX": "auto", "width": "100%"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "6px",
                            "fontFamily": "Inter, system-ui",
                            "fontSize": 13,
                            "minWidth": "120px",
                            "width": "auto",
                            "maxWidth": "280px",
                            "whiteSpace": "normal",
                        },
                        style_header={"fontWeight": 600},
                    ),
                    html.Div(
                        [
                            dcc.RadioItems(
                                id="camp-metrics-kind",
                                options=[
                                    {"label": "Source", "value": "source"},
                                    {"label": "Campaign", "value": "campaign"},
                                    {"label": "AdGroup", "value": "adgroup"},
                                ],
                                value="source",
                                inline=True,
                                style={"margin": "6px 0"},
                            ),
                            dash_table.DataTable(
                                id="camp-metrics-table",
                                data=src_table.to_dict("records"),
                                columns=metrics_table_cols,
                                style_table={"overflowX": "auto", "width": "100%"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "6px",
                                    "fontFamily": "Inter, system-ui",
                                    "fontSize": 13,
                                    "minWidth": "60px",
                                    "width": "auto",
                                    "maxWidth": "160px",
                                    "whiteSpace": "normal",
                                },
                                style_header={"fontWeight": 600},
                                style_data_conditional=[
                                    {"if": {"column_id": "campaign"}, "maxWidth": "160px", "whiteSpace": "normal"},
                                    {"if": {"column_id": "adgroup"}, "maxWidth": "160px", "whiteSpace": "normal"},
                                ],
                            ),
                        ]
                    ),
                ],
            )
        ],
        className="viz-card",
        style={"maxWidth": "1500px", "overflowX": "auto"},
    )

    right_col = html.Div(
        style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            dcc.Store(id="camp-data", data=store_data),
            controls,
            html.Div(
                style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "alignItems": "stretch"},
                children=[baseline_card, filtered_card],
            ),
            roas_card,
            scatter_card,
            metrics_card,
        ],
    )

    return html.Div(style={"display": "flex", "gap": "16px"}, className="viz-page", children=[get_sidebar(), right_col])


@callback(
    Output("camp-data", "data"),
    Output("camp-funnel-filtered", "data"),
    Output("camp-roas-table", "data"),
    Output("camp-scatter", "figure"),
    Output("camp-metrics-table", "data"),
    Output("camp-metrics-table", "columns"),
    Input("camp-filter-source", "value"),
    Input("camp-filter-campaign", "value"),
    Input("camp-filter-adgroup", "value"),
    Input("camp-reload-btn", "n_clicks"),
    Input("camp-metrics-kind", "value"),
    State("camp-data", "data"),
)
def _update_campaigns(
    source: str | None,
    campaign: str | None,
    adgroup: str | None,
    _n_clicks: int | None,
    kind: str,
    store: dict | None,
):
    """
    Возвращает метрики по фильтрам; данные перечитываются только по кнопке или при пустом store.
    """
    APP_DIR = Path(__file__).resolve().parents[2]
    PROJECT_ROOT = APP_DIR.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))
    from src.analytics_campaigns import load_campaign_data, compute_all_metrics  # type: ignore

    need_reload = store is None or ctx.triggered_id == "camp-reload-btn"
    if need_reload:
        deals, spend = load_campaign_data()
        store = {
            "deals": deals[["id", "campaign", "source", "adgroup", "stage", "revenue_value", "is_paid"]].to_dict("records"),
            "spend": spend[["campaign", "source", "adgroup", "impressions", "clicks", "spend"]].to_dict("records"),
        }
    else:
        deals = pd.DataFrame(store.get("deals", []))
        spend = pd.DataFrame(store.get("spend", []))

    metrics = compute_all_metrics(deals, spend, source=source, campaign=campaign, adgroup=adgroup)

    funnel_filtered = metrics["funnel"]
    src_table = metrics["source_metrics"].sort_values(["roas", "paid"], ascending=[False, False])
    camp_table = metrics["campaign_metrics"]
    ad_table = metrics["adgroup_metrics"]

    roas_data = src_table[["source", "roas", "revenue", "spend", "cpa", "cpl"]].to_dict("records")
    fig = _scatter_sources(src_table)

    if kind == "campaign":
        tbl = camp_table
    elif kind == "adgroup":
        tbl = ad_table
    else:
        tbl = src_table
    tbl_out = tbl.copy()
    tbl_out = tbl_out.drop(columns=["full_conversion", "avg_payment"], errors="ignore")
    for col in tbl_out.select_dtypes(include=["float", "float64", "float32"]).columns:
        tbl_out[col] = tbl_out[col].round(2)
    metrics_cols = _build_cols(tbl_out)

    return store, funnel_filtered.to_dict("records"), roas_data, fig, tbl_out.to_dict("records"), metrics_cols
