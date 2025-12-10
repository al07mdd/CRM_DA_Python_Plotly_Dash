from __future__ import annotations

from pathlib import Path
import sys
from dash import Dash, dcc, html, page_container, Input, Output, callback


# Paths
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
ASSETS_DIR = APP_DIR / "assets"

# Make project modules importable for pages that need src.io/features
sys.path.append(str(PROJECT_ROOT))


def top_nav():
    return html.Nav(
        [
            dcc.Link("1️⃣ ДАННЫЕ", href="/data/import", className="tab"),
            dcc.Link("2️⃣ АНАЛИЗ", href="/viz/timeseries", className="tab"),
            dcc.Link("3️⃣ ЮНИТ-ЭКОНОМИКА", href="/product/unit-economics", className="tab"),
            dcc.Link("4️⃣ ОТЧЕТЫ И ПРЕЗЕНТАЦИИ", href="/reports/full", className="tab"),
        ],
    )


def filters_bar():
    # Placeholder for global filters; responsive grid
    return html.Div(
        [
            dcc.Dropdown(
                id="filter-period",
                options=[
                    {"label": "Все", "value": "all"},
                    {"label": "Последние 30 дней", "value": "30d"},
                    {"label": "Последние 90 дней", "value": "90d"},
                ],
                placeholder="Период",
            ),
            dcc.Dropdown(id="filter-source", placeholder="Источник"),
            dcc.Dropdown(id="filter-product", placeholder="Продукт"),
            dcc.Dropdown(id="filter-city", placeholder="Город"),
            dcc.Dropdown(id="filter-stage", placeholder="Стадия сделки"),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(160px, 1fr))",
            "gap": "10px",
            "margin": "12px 0",
            "width": "100%",
        },
    )


app = Dash(
    __name__,
    use_pages=True,
    title="Final Project - Dash App",
    assets_folder=str(ASSETS_DIR),
    suppress_callback_exceptions=True,
)


app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(id="app-lang", storage_type="session", data="ru"),
        html.Header(
            [
                html.Div(
                    [
                        html.H1("CRM Data Analysis & Unit Economics"),
                        html.Div(top_nav(), id="top-nav", className="top-nav"),
                    ],
                    className="header-inner",
                )
            ]
        ),
        # Content section without container wrapper to align with fixed sidebar pages
        html.Section([page_container]),
        html.Footer(
            [
                html.Div(
                    [
                        html.Small(
                            [
                                "Developed with Python & Plotly Dash | ",
                                html.A("1733lt@gmail.com", href="mailto:1733lt@gmail.com"),
                                " | GitHub: ",
                                html.A("al07mdd", href="https://github.com/al07mdd", target="_blank"),
                                " | 2025",
                            ]
                        )
                    ],
                    className="container",
                )
            ]
        ),
    ]
)


@callback(Output("top-nav", "className"), Input("url", "pathname"))
def _highlight_top_section(pathname: str | None) -> str:
    base = "top-nav"
    if not pathname:
        return base
    try:
        if pathname.startswith("/data"):
            return f"{base} sec-data"
        if pathname.startswith("/viz"):
            return f"{base} sec-viz"
        if pathname.startswith("/product"):
            return f"{base} sec-product"
        if pathname.startswith("/reports"):
            return f"{base} sec-reports"
    except Exception:
        pass
    return base


def _top_nav_links_en() -> html.Nav:
    return html.Nav(
        [
            dcc.Link("1️⃣ DATA", href="/data/import", className="tab"),
            dcc.Link("2️⃣ VISUALIZATIONS", href="/viz/timeseries", className="tab"),
            dcc.Link("3️⃣ PRODUCT ANALYTICS", href="/product/unit-economics", className="tab"),
            dcc.Link("4️⃣ REPORTS", href="/reports/full", className="tab"),
        ],
    )


def _top_nav_links_de() -> html.Nav:
    return html.Nav(
        [
            dcc.Link("1️⃣ DATEN", href="/data/import", className="tab"),
            dcc.Link("2️⃣ VISUALISIERUNGEN", href="/viz/timeseries", className="tab"),
            dcc.Link("3️⃣ PRODUKTANALYTIK", href="/product/unit-economics", className="tab"),
            dcc.Link("4️⃣ BERICHTE", href="/reports/full", className="tab"),
        ],
    )


@callback(Output("top-nav", "children"), Input("app-lang", "data"))
def _update_top_nav(lang_value: str | None):
    lang = lang_value or "ru"
    if lang == "en":
        return _top_nav_links_en()
    if lang == "de":
        return _top_nav_links_de()
    # Russian or unknown: keep original nav
    return top_nav()


if __name__ == "__main__":
    app.run(debug=True)
