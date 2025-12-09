from dash import html, dcc


def get_sidebar():
    return html.Div(
        [
            html.H3("АНАЛИЗ"),
            dcc.Link("◉ Временные ряды", href="/viz/timeseries", className="tab"),
            dcc.Link("◉ Кампании и источники", href="/viz/campaigns", className="tab"),
            dcc.Link("◉ Отдел продаж", href="/viz/sales", className="tab"),
            dcc.Link("◉ Платежи и продукты", href="/viz/payments", className="tab"),
            dcc.Link("◉ География сделок", href="/viz/geo", className="tab"),
        ],
        style={"minWidth": "260px", "display": "flex", "flexDirection": "column", "gap": "8px"},
        className="sidebar",
    )
