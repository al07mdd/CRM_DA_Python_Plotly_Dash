from __future__ import annotations

from dash import dcc, html, callback, Input, Output


SIDEBAR_CHILDREN_RU = [
    html.H3("Отчеты и презентации"),
    dcc.Link("Всесторонний отчет - Python DA", href="/reports/full", className="tab"),
            dcc.Link("Всесторонний отчет - юнит‑экономика", href="/reports/full-ue", className="tab"),
            dcc.Link("Презентация проекта - Python DA", href="/reports/presentation-final", className="tab"),
]

SIDEBAR_CHILDREN_EN = [
    html.H3("Reports & presentations"),
    dcc.Link("Full report - Python DA", href="/reports/full", className="tab"),
    dcc.Link("Full report - Unit Economics", href="/reports/full-ue", className="tab"),
    dcc.Link("Final presentation - Python DA", href="/reports/presentation-final", className="tab"),
]

SIDEBAR_CHILDREN_DE = [
    html.H3("Berichte & Präsentationen"),
    dcc.Link("Vollständiger Bericht - Python DA", href="/reports/full", className="tab"),
    dcc.Link("Vollständiger Bericht - Unit Economics", href="/reports/full-ue", className="tab"),
    dcc.Link("Abschlusspräsentation - Python DA", href="/reports/presentation-final", className="tab"),
]


def get_sidebar():
    return html.Div(
        SIDEBAR_CHILDREN_RU,
        id="reports-sidebar",
        style={"minWidth": "260px", "display": "flex", "flexDirection": "column", "gap": "8px"},
        className="sidebar",
    )


@callback(Output("reports-sidebar", "children"), Input("app-lang", "data"))
def _update_reports_sidebar(lang_value: str | None):
    lang = lang_value or "ru"
    if lang == "en":
        return SIDEBAR_CHILDREN_EN
    if lang == "de":
        return SIDEBAR_CHILDREN_DE
    return SIDEBAR_CHILDREN_RU

