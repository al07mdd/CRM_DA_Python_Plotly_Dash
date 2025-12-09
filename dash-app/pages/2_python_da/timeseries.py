from __future__ import annotations

from pathlib import Path
import sys

from dash import html, dcc, register_page, callback, Input, Output, State, no_update, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _apply_viz_style(fig: go.Figure) -> go.Figure:
    """
    Применяет стиль, похожий на панель мониторинга, к фигуре Plotly (только раздел визуализации).
    Также добавляет отступ заголовков осей и автоматические поля, чтобы избежать наложения заголовка оси y и меток.
    """
    grid = "rgba(0,0,0,0.08)"
    axisline = "rgba(0,0,0,0.18)"
    font_color = "#1f2937"
    colorway = ["#2563eb", "#10b981", "#ef4444", "#f59e0b", "#8b5cf6", "#14b8a6"]
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        colorway=colorway,
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial", size=12, color=font_color),
        hoverlabel=dict(bgcolor="#fff", bordercolor="#e5e7eb", font=dict(color="#111111")),
        bargap=0.12,
        uirevision="ts",
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        showline=True,
        linecolor=axisline,
        ticks="outside",
        ticklen=4,
        showspikes=False,  # убираем направляющие (spikelines) по X
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
        showspikes=False,  # убираем направляющие (spikelines) по Y
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
    path="/viz/timeseries",
    name="Временные ряды",
    title="Визуализации - Временные ряды",
    order=40,
)


def layout():
    """
    Формирует страницу с контролами выбора месяцев и набором графиков/таблиц для временных рядов.
    """
    """
    Страница временных рядов: контролы (месяцы), 3 графика на своих слоях, примечания, прокрутка справа.
    """
    from .sidebar import get_sidebar

    # Подключаем src.*
    APP_DIR = Path(__file__).resolve().parents[2]
    PROJECT_ROOT = APP_DIR.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))
    from src.analytics_timeseries import (  # type: ignore
        load_deals_calls,
        make_daily_series,
        make_closed_daily,
        make_ttc_series,
        ttc_hist_counts,
    )

    # Предзагрузка для опций фильтра месяца
    deals, calls = load_deals_calls()
    daily = make_daily_series(deals, calls)
    months = sorted({d.strftime('%Y-%m') for d in pd.to_datetime(daily['date'])})
    month_opts = [{"label": m, "value": m} for m in months]

    controls = html.Article(
        [
            # Одна строка: слева заголовок+кнопка (колонка), справа фильтр (по правому верхнему краю)
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Анализ временных рядов", style={"margin": "0 0 4px"}),
                            html.Div(
                                [
                                    html.Button("Обновить отчёт", id="ts-reload-btn"),
                                    html.Button("Квартал (последние 3 мес.)", id="ts-q-last", style={"marginLeft": "8px"}),
                                ],
                                style={"display": "flex", "gap": "8px"},
                            ),
                            dcc.ConfirmDialog(id="ts-reload-msg"),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
                    ),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="ts-months",
                                options=month_opts,
                                value=[],
                                multi=True,
                                placeholder="Месяцы (по умолчанию: все)",
                                style={"minWidth": 260, "maxWidth": 420},
                            )
                        ],
                        style={"display": "flex", "justifyContent": "flex-end", "alignItems": "flex-start"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "gap": "12px",
                    "width": "100%",
                },
            ),
        ],
        # Минимизируем высоту слоя заголовка; класс отвечает за sticky-стили
        style={"padding": "6px 12px 6px"},
        className="viz-controls",
    )

    # Пустая фигура-заглушка. Высоту задаём на контейнере dcc.Graph.
    fig_empty = go.Figure(); fig_empty.update_layout(autosize=True, margin=dict(l=64, r=12, t=6, b=0), uirevision="ts")

    right_col = html.Div(
        style={
            "flex": 1,
            "display": "flex",
            "flexDirection": "column",
            "gap": "16px",
        },
        children=[
            controls,
            html.Div(
                id="ts-scroll",
                style={
                    "width": "100%",
                },
                children=[
                    html.Article([
                        html.H3("Сделки vs звонки (ежедневно) + Конверсия (сделки/звонки, %)"),
                        dcc.Graph(id="ts-fig", figure=fig_empty, className="viz-graph viz-graph-tall", config={"displayModeBar": False, "responsive": True}, style={"width": "100%", "height": "350px", "marginTop": "6px"}),
                    ], className="viz-card"),
                    html.Article([
                        html.H3("Закрытые сделки"),
                        dcc.Graph(id="ts-closed", figure=fig_empty, className="viz-graph", config={"displayModeBar": False, "responsive": True}, style={"width": "100%", "height": "260px"}),
                    ], className="viz-card"),
                    html.Article([
                        html.H3("Сводка по суточным рядам"),
                        dash_table.DataTable(
                            id="ts-daily-table",
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
                                {"selector": ".dash-cell div.dash-cell-value", "rule": "white-space: normal; overflow: hidden; text-overflow: ellipsis;"},
                                {"selector": ".dash-table-container", "rule": "max-width: 100%;"},
                            ],
                        ),
                    ], className="viz-card"),
                    html.Article([
                        html.H3("Сделки и звонки (суточные значения)"),
                        dcc.Graph(id="ts-box", figure=fig_empty, className="viz-graph", config={"displayModeBar": False, "responsive": True}, style={"width": "100%", "height": "260px"}),
                    ], className="viz-card"),
                    html.Article([
                        html.H3("Распределение time-to-close"),
                        dcc.Graph(id="ts-ttc", figure=fig_empty, className="viz-graph", config={"displayModeBar": False, "responsive": True}, style={"width": "100%", "height": "260px"}),
                    ], className="viz-card"),
                    # Примечания - отдельный слой-карточка, скрывающийся по умолчанию
                    html.Article(
                        [
                            html.Details(
                                open=False,
                                children=[
                                    html.Summary("Примечания"),
                                    html.Ul(id="ts-notes", style={"margin": "8px 0 0 16px"}),
                                ],
                            )
                        ],
                        style={"marginTop": "8px"},
                    ),
                ],
            )
        ],
    )

    return html.Div(style={"display": "flex", "gap": "16px"}, className="viz-page", children=[get_sidebar(), right_col])


def _filter_by_months(daily: pd.DataFrame, deals: pd.DataFrame, months: list[str] | None):
    """
    Вернуть отфильтрованные daily и deals по выбранным месяцам ['YYYY-MM'] (или исходные, если пусто).
    """
    if not months:
        return daily, deals
    mset = set(months)
    mask_daily = pd.to_datetime(daily['date']).dt.strftime('%Y-%m').isin(mset)
    mask_deals = pd.to_datetime(deals['created_time']).dt.strftime('%Y-%m').isin(mset) | pd.to_datetime(deals['closing_date']).dt.strftime('%Y-%m').isin(mset)
    return daily[mask_daily], deals[mask_deals]


@callback(
    Output("ts-fig", "figure"),
    Output("ts-closed", "figure"),
    Output("ts-ttc", "figure"),
    Output("ts-daily-table", "data"),
    Output("ts-daily-table", "columns"),
    Output("ts-box", "figure"),
    Output("ts-notes", "children"),
    Input("ts-months", "value"),
    Input("ts-reload-btn", "n_clicks"),
    prevent_initial_call=False,
)
def _update_timeseries(selected_months: list[str] | None, _n_clicks: int | None):
    """
    Пересчитывает все графики и таблицы при изменении фильтров или нажатии кнопки.
    """
    from src.analytics_timeseries import load_deals_calls, make_daily_series, make_closed_daily, make_ttc_series, ttc_hist_counts, calls_duration_stats, overall_period_and_conversion  # type: ignore

    deals, calls = load_deals_calls()
    daily_all = make_daily_series(deals, calls)
    daily, deals_f = _filter_by_months(daily_all, deals, selected_months)
    # Вариант: закрытия/TTC по условию created_date ИЛИ closing_date в фильтре
    # closed_daily = make_closed_daily(deals_f, upper=daily['date'].max() if len(daily) else None)
    # ttc_valid = make_ttc_series(deals_f)

    # Вариант: для закрытий и TTC фильтруем только по месяцу closing_date
    if selected_months:
        mset = set(selected_months)
        deals_f_closed = deals[pd.to_datetime(deals["closing_date"]).dt.strftime("%Y-%m").isin(mset)]
    else:
        deals_f_closed = deals
    closed_daily = make_closed_daily(deals_f_closed, upper=daily['date'].max() if len(daily) else None)
    ttc_valid = make_ttc_series(deals_f_closed)
    deals_paid_closed = deals_f_closed[deals_f_closed["Stage"].eq("payment done")]
    ttc_paid = make_ttc_series(deals_paid_closed)
    # Категориальное распределение TTC по фиксированным корзинам
    ttc_bins = ttc_hist_counts(ttc_valid)
    ttc_bins_paid = ttc_hist_counts(ttc_paid)

    # 1) Создано/Звонки + конверсия
    # графики без заголовков внутри (названия снаружи в слоях)
    fig_ts = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.55, 0.45],
        # subplot_titles=["Создано vs звонки", "Конверсия (сделки/звонки), %"],
    )
    if len(daily):
        fig_ts.add_trace(go.Scatter(x=daily['date'], y=daily['deals_created'], name='Создано (сделки)', mode='lines'), row=1, col=1)
        fig_ts.add_trace(go.Scatter(x=daily['date'], y=daily['calls_total'], name='Звонки', mode='lines'), row=1, col=1)
        fig_ts.add_trace(go.Scatter(x=daily['date'], y=daily['deal_rate_pct'], name='Конверсия, %', mode='lines',
                                    line=dict(color='firebrick'),
                                    hovertemplate='Дата: %{x}<br>Конверсия: %{y:.1f}%<extra></extra>'), row=2, col=1)
    fig_ts.update_yaxes(title_text='Количество', row=1, col=1)
    fig_ts.update_yaxes(title_text='Конверсия, %', row=2, col=1)
    fig_ts.update_xaxes(title_text='Дата', row=2, col=1)
    # fig_ts.update_layout(title='Ежедневно: создано и звонки + конверсия', legend_title_text='Серия')  # без заголовка
    fig_ts.update_layout(legend_title_text='Серия', autosize=True, margin=dict(l=64, r=12, t=6, b=0), uirevision="ts")
    fig_ts = _apply_viz_style(fig_ts)

    # 2) Закрытые сделки
    fig_closed = px.line(closed_daily, x='closing_date', y='deals_closed')  # без заголовка
    fig_closed.update_layout(xaxis_title='Дата', yaxis_title='Количество', autosize=True, margin=dict(l=64, r=12, t=6, b=0), uirevision="ts")
    fig_closed = _apply_viz_style(fig_closed)

    # 3) Табличные сводки по суточным рядам
    def _daily_stats(df: pd.DataFrame, value_col: str, label: str) -> dict:
        if df is None or df.empty:
            return {"series": label, "date_from": None, "date_to": None, "days": 0, "total": 0,
                    "per_day_mean": None, "per_day_median": None, "per_day_min": None, "per_day_max": None}
        s = df[value_col]
        return {
            "series": label,
            "date_from": pd.to_datetime(df['date']).min().date(),
            "date_to": pd.to_datetime(df['date']).max().date(),
            "days": int(len(df)),
            "total": float(s.sum()),
            "per_day_mean": float(s.mean()),
            "per_day_median": float(s.median()),
            "per_day_min": float(s.min()),
            "per_day_max": float(s.max()),
        }
    stats_df = pd.DataFrame([
        _daily_stats(daily, 'deals_created', 'deals_created'),
        _daily_stats(daily, 'calls_total', 'calls_total'),
    ])
    table_data = stats_df.to_dict("records")
    table_cols = [{"name": c, "id": c} for c in stats_df.columns]

    # 4) Боксплоты: суточные значения (два субплота)
    fig_box = make_subplots(rows=1, cols=2)
    if len(daily):
        fig_box.add_trace(go.Box(y=daily['deals_created'], name='deals_created', boxpoints='outliers'), row=1, col=1)
        fig_box.add_trace(go.Box(y=daily['calls_total'], name='calls_total', boxpoints='outliers'), row=1, col=2)
    fig_box.update_yaxes(title_text='Суточное количество', row=1, col=1)
    fig_box.update_yaxes(title_text='Суточное количество', row=1, col=2)
    fig_box.update_layout(autosize=True, margin=dict(l=64, r=12, t=6, b=0), uirevision="ts")
    fig_box = _apply_viz_style(fig_box)

    # 5) TTC: фиксированные корзины (0-3, 4-7, ...), чтобы совпадать с табличной сводкой
    fig_ttc = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.55, 0.45],
    )
    if len(ttc_bins):
        fig_ttc.add_bar(
            x=ttc_bins.index.astype(str),
            y=ttc_bins.values,
            name='TTC bins (all deals)',
            marker=dict(color="rgb(180, 189, 250)", line=dict(color="rgba(70, 80, 200, 0.9)", width=2)),
            row=1,
            col=1,
        )
    if len(ttc_bins_paid):
        fig_ttc.add_bar(
            x=ttc_bins_paid.index.astype(str),
            y=ttc_bins_paid.values,
            name='TTC bins (payment done)',
            marker=dict(color="rgb(99, 110, 250)", line=dict(color="rgba(40, 50, 160, 0.9)", width=2)),
            row=2,
            col=1,
        )
    fig_ttc.update_yaxes(title_text='Все Сделки', row=1, col=1)
    fig_ttc.update_yaxes(title_text='Оплаченные Сделки', row=2, col=1)
    fig_ttc.update_xaxes(title_text='Дни', row=2, col=1)
    fig_ttc.update_layout(showlegend=False, autosize=True, margin=dict(l=64, r=12, t=6, b=0), uirevision="ts")
    fig_ttc = _apply_viz_style(fig_ttc)

    # Примечания
    notes = []
    meta = overall_period_and_conversion(daily)
    if meta:
        notes.append(html.Li(f"Период данных: {meta['date_from']} - {meta['date_to']}"))
        notes.append(html.Li(f"Создано сделок: {meta['deals_sum']}; звонков: {meta['calls_sum']}; конверсия ~ {meta['conv_overall']:.1f}%"))
    if len(ttc_valid):
        med = float(ttc_valid.median()); p90 = float(ttc_valid.quantile(0.90))
        notes.append(html.Li(f"Time-to-close (дни): медиана {med:.1f}; 90-й перцентиль {p90:.1f} (по {len(ttc_valid)} сделкам)"))
    # Добавим сведения по длительности звонков (сек/мин), если доступны
    cstats = calls_duration_stats(calls)
    if cstats:
        notes.append(
            html.Li(
                f"Длительность звонка: медиана {cstats['med_s']:.0f} сек ({cstats['med_m']:.1f} мин); "
                f"90-й перцентиль {cstats['p90_s']:.0f} сек ({cstats['p90_m']:.1f} мин) (по {int(cstats['n'])} звонкам)"
            )
        )

    return fig_ts, fig_closed, fig_ttc, table_data, table_cols, fig_box, notes


@callback(
    Output("ts-reload-msg", "displayed"),
    Output("ts-reload-msg", "message"),
    Input("ts-reload-btn", "n_clicks"),
    prevent_initial_call=True,
)
def _confirm_reload(n_clicks: int | None):
    """
    Кнопка «Обновить отчёт»: перечитываем Deals/Calls из data/clean и сообщаем пользователю.
    """
    if not n_clicks:
        return False, ""
    try:
        from src.analytics_timeseries import load_deals_calls, make_daily_series  # type: ignore

        deals, calls = load_deals_calls()
        make_daily_series(deals, calls)
        return True, "Данные перечитаны: графики используют актуальные Deals/Calls из data/clean. Используйте фильтр месяцев при необходимости."
    except Exception as exc:  # noqa: BLE001
        return True, f"Не удалось перечитать данные: {exc}"


@callback(Output("ts-months", "value"), Input("ts-q-last", "n_clicks"), State("ts-months", "options"))
def _set_last_quarter(n_clicks: int | None, options: list[dict] | None):
    """
    Заполняет селектор последними тремя месяцами из списка опций.
    """
    if not n_clicks:
        return no_update
    # Берем последние 3 месяца по списку опций (они отсортированы в layout)
    opts = options or []
    values = [o.get("value") for o in opts if o.get("value")]
    if len(values) >= 3:
        return values[-3:]
    return values
