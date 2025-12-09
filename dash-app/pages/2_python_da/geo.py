from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import List, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, register_page, callback, Input, Output


def _apply_viz_style(fig: go.Figure) -> go.Figure:
    """
    Базовое оформление графиков
    """
    grid = "rgba(0,0,0,0.08)"
    axisline = "rgba(0,0,0,0.18)"
    font_color = "#1f2937"
    colorway = ["#2563eb", "#10b981", "#ef4444", "#f59e0b", "#8b5cf6", "#14b8a6"]
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#fff", bordercolor="#e5e7eb", font=dict(color="#111111")),
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial", size=12, color=font_color),
        colorway=colorway,
        uirevision="geo",
    )
    fig.update_xaxes(showgrid=True, gridcolor=grid, zeroline=False, showline=True, linecolor=axisline, ticks="outside", ticklen=4)
    fig.update_yaxes(showgrid=True, gridcolor=grid, zeroline=False, showline=True, linecolor=axisline, ticks="outside", ticklen=4)
    return fig


register_page(
    __name__,
    path="/viz/geo",
    name="География",
    title="География сделок",
    order=80,
)


def _project_root() -> Path:
    app_dir = Path(__file__).resolve().parents[2]
    root = app_dir.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    return root


def _load_states_geojson() -> dict | None:
    root = _project_root()
    path = root / "data" / "temp" / "lands_de_border.geojson"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _empty_map(message: str) -> go.Figure:
    """
    Пустая карта с сообщением.
    """
    fig = go.Figure()
    fig.update_layout(
        annotations=[dict(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)],
        margin=dict(l=24, r=12, t=12, b=12),
        height=620,
    )
    fig.update_geos(showland=True, showcountries=True, showsubunits=True, showcoastlines=True)
    return _apply_viz_style(fig)


def _build_geo_fig(df: pd.DataFrame, states_geojson: dict | None = None) -> go.Figure:
    """
    Карта точек по городам с контуром земель (если доступен geojson).
    """
    if df is None or df.empty:
        return _empty_map("Нет данных для отображения")
    if "win_rate" in df.columns:
        df = df.copy()
        df["win_rate"] = pd.to_numeric(df["win_rate"], errors="coerce")
    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        size="deals",
        color="win_rate",
        hover_name="City",
        hover_data={"deals": True, "paid": True, "win_rate": ":.0%", "lat": False, "lon": False},
        projection="mercator",
        scope="europe",
        color_continuous_scale="Bluered",
        range_color=(0, 1),
        size_max=22,
    )
    if states_geojson:
        fig.add_trace(
            go.Choropleth(
                geojson=states_geojson,
                featureidkey="properties.name",
                locations=[f["properties"]["name"] for f in states_geojson.get("features", [])],
                z=[1] * len(states_geojson.get("features", [])),
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                hoverinfo="skip",
                hovertemplate=None,
                marker_line_color="gray",
                marker_line_width=0.3,
            )
        )
    fig.update_geos(
        fitbounds="locations",
        projection_type="mercator",
        lataxis_range=[47, 55.5],
        lonaxis_range=[5, 16.5],
        showland=False,
        showcountries=False,
        showsubunits=False,
        showcoastlines=False,
        showframe=False,
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(height=620, margin=dict(l=24, r=12, t=8, b=12), title=None)
    return _apply_viz_style(fig)


def _level_options(levels: List[str]) -> List[Dict[str, str]]:
    return [{"label": lvl, "value": lvl} for lvl in levels]


def layout():
    from .sidebar import get_sidebar

    _project_root()
    from src.analytics_geo import load_deals, load_city_coords, city_options, make_city_summary  # type: ignore

    deals = load_deals()
    coords = load_city_coords()
    level_list = city_options(deals)
    level_opts = _level_options(level_list)
    default_level = "B1" if "B1" in level_list else (level_list[0] if level_list else None)
    fig_placeholder = _empty_map("Загрузите данные, чтобы увидеть карту")
    states_geojson = _load_states_geojson()

    controls = html.Article(
        className="viz-controls",
        style={"padding": "6px 12px 6px"},
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "gap": "12px"},
                children=[
                    html.Div(
                        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
                        children=[
                            html.H3("Анализ географии сделок", style={"margin": "0"}),
                            html.Button("Обновить отчет", id="geo-reload-btn"),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
                        children=[
                            html.Label("Уровень языка:", style={"fontWeight": 600}),
                            dcc.Dropdown(
                                id="geo-level",
                                options=level_opts,
                                value=default_level,
                                placeholder="Выберите уровень",
                                style={"minWidth": 180},
                                clearable=True,
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    cards = html.Div(
        style={"width": "100%", "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            html.Article(
                className="viz-card",
                children=[
                    html.H3("Сделки по городам Германии (размер - сделки, цвет - доля оплат)"),
                    dcc.Graph(
                        id="geo-deals-fig",
                        figure=fig_placeholder,
                        className="viz-graph viz-graph-tall",
                        config={"displayModeBar": False},
                        style={"width": "100%", "height": "620px", "marginTop": "6px"},
                    ),
                ],
            ),
            html.Article(
                className="viz-card",
                children=[
                    html.H3(id="geo-level-title", children="Сделки по городам (фильтр по уровню языка)"),
                    dcc.Graph(
                        id="geo-level-fig",
                        figure=fig_placeholder,
                        className="viz-graph viz-graph-tall",
                        config={"displayModeBar": False},
                        style={"width": "100%", "height": "620px", "marginTop": "6px"},
                    ),
                ],
            ),
        ],
    )

    right_col = html.Div(
        style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px", "maxWidth": "1500px"},
        children=[controls, cards],
    )
    return html.Div(
        style={"display": "flex", "gap": "16px", "justifyContent": "center"},
        className="viz-page",
        children=[get_sidebar(), right_col],
    )


@callback(
    Output("geo-level", "options"),
    Output("geo-level", "value"),
    Output("geo-level-title", "children"),
    Output("geo-deals-fig", "figure"),
    Output("geo-level-fig", "figure"),
    Input("geo-level", "value"),
    Input("geo-reload-btn", "n_clicks"),
    prevent_initial_call=False,
)
def _update_maps(level_value: str | None, _n_clicks: int | None):  # type: ignore
    _project_root()
    from src.analytics_geo import load_deals, load_city_coords, city_options, make_city_summary, make_level_city_summary  # type: ignore

    states_geojson = _load_states_geojson()
    deals = load_deals()
    coords = load_city_coords()
    level_list = city_options(deals)
    level_opts = _level_options(level_list)
    default_level = "B1" if "B1" in level_list else (level_list[0] if level_list else None)

    level_use = level_value if level_value in level_list else default_level

    city_df = make_city_summary(deals, coords)
    deals_fig = _build_geo_fig(city_df, states_geojson)

    level_df = make_level_city_summary(deals, coords, level_use)
    level_fig = _build_geo_fig(level_df, states_geojson)

    title = f"Сделки по городам - уровень {level_use or 'N/A'} (размер - сделки, цвет - доля оплат)"

    return level_opts, level_use, title, deals_fig, level_fig
