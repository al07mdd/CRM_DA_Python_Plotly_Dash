from dash import dcc, html


def get_sidebar():
    return html.Div(
        [
            html.H3("Отчеты и презентации"),
            dcc.Link("Всесторонний отчет - Python DA", href="/reports/full", className="tab"),
            dcc.Link("Всесторонний отчет - юнит‑экономика", href="/reports/full-ue", className="tab"),
            dcc.Link("Презентация проекта - Python DA", href="/reports/presentation-final", className="tab"),
        ],
        style={"minWidth": "260px", "display": "flex", "flexDirection": "column", "gap": "8px"},
        className="sidebar",
    )
