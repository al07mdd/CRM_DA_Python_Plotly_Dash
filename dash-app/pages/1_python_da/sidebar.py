from dash import html, dcc


def get_sidebar():
    return html.Div(
        [
            html.H3("ДАННЫЕ"),
            dcc.Link("◉ Импорт", href="/data/import", className="tab"),
            dcc.Link("◉ Очистка и подготовка", href="/data/cleaning", className="tab"),
            dcc.Link("◉ Описательная статистика", href="/data/descriptive", className="tab"),
        ],
        style={"minWidth": "260px", "display": "flex", "flexDirection": "column", "gap": "8px"},
        className="sidebar",
    )
