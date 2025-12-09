from dash import html, dcc


def get_sidebar():
    return html.Div(
        [
            html.H3("ЮНИТ-ЭКОНОМИКА"),
            dcc.Link("◉ Юнит-экономика", href="/product/unit-economics", className="tab"),
            dcc.Link("◉ Точки роста бизнеса", href="/product/growth-points", className="tab"),
            dcc.Link("◉ Дерево метрик", href="/product/metric-tree", className="tab"),
            dcc.Link("◉ Проверка гипотез", href="/product/hypotheses", className="tab"),
        ],
        style={"minWidth": "260px", "display": "flex", "flexDirection": "column", "gap": "8px"},
        className="sidebar",
    )
