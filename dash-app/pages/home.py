from __future__ import annotations

from dash import dcc, html, register_page


register_page(
    __name__,
    path="/",
    name="Главная",
    title="Анализ CRM системы онлайн-школы программирования X",
    order=0,
)

HERO_STATS = [
    {"value": "4", "label": "CRM-таблицы", "desc": "Contacts • Calls • Spend • Deals"},
    {"value": "4", "label": "глобальных раздела", "desc": "Данные · Аналитика · Юнит-экономика · Отчеты"},
]

SECTION_LINKS = [
    {
        "title": "Данные",
        "links": [
            {"label": "Импорт", "href": "/data/import"},
            {"label": "Очистка и подготовка", "href": "/data/cleaning"},
            {"label": "Описательная статистика", "href": "/data/descriptive"},
        ],
    },
    {
        "title": "Анализ",
        "links": [
            {"label": "Временные ряды", "href": "/viz/timeseries"},
            {"label": "Кампании и источники", "href": "/viz/campaigns"},
            {"label": "Отдел продаж", "href": "/viz/sales"},
            {"label": "Платежи и продукты", "href": "/viz/payments"},
            {"label": "География сделок", "href": "/viz/geo"},
        ],
    },
    {
        "title": "Юнит-экономика",
        "links": [
            {"label": "Юнит-экономика", "href": "/product/unit-economics"},
            {"label": "Точки роста бизнеса", "href": "/product/growth-points"},
            {"label": "Дерево метрик", "href": "/product/metric-tree"},
            {"label": "Проверка гипотез", "href": "/product/hypotheses"},
        ],
    },
    {
        "title": "Отчеты",
        "links": [
            {"label": "Всесторонний отчет - Python DA", "href": "/reports/full"},
            {"label": "Всесторонний отчет - юнит-экономика", "href": "/reports/full-ue"},
            {"label": "Презентация проекта - Python DA", "href": "/reports/presentation-final"},
        ],
    },
]


def _stat_block(stat: dict[str, str]) -> html.Div:
    return html.Div(
        [
            html.Div(stat["value"], style={"fontSize": "32px", "fontWeight": 800}),
            html.Div(stat["label"], style={"fontSize": "14px", "textTransform": "uppercase", "letterSpacing": "0.08em"}),
            html.Div(stat["desc"], className="muted", style={"fontSize": "13px"}),
        ],
        style={
            "minWidth": "180px",
            "padding": "12px 16px",
            "borderRadius": "12px",
            "border": "1px solid rgba(0,0,0,0.08)",
            "background": "rgba(255,255,255,0.6)",
            "boxShadow": "var(--shadow)",
        },
    )


def _section_card(card: dict[str, object]) -> html.Article:
    links = card.get("links", [])
    return html.Article(
        [
            html.H3(card["title"]),
            html.Div(
                [dcc.Link(link["label"], href=link["href"], className="tab") for link in links],
                style={"display": "flex", "flexWrap": "wrap", "gap": "8px"},
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "12px"},
    )


def layout():
    return html.Div(
        className="container",
        style={"display": "flex", "flexDirection": "column", "gap": "20px", "maxWidth": "1100px"},
        children=[
            html.Article(
                [
                    html.H1("Анализ CRM системы онлайн-школы программирования X."),
                    html.Div(
                        [_stat_block(stat) for stat in HERO_STATS],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))",
                            "gap": "16px",
                        },
                    ),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "16px"},
            ),
            html.Div(
                [_section_card(card) for card in SECTION_LINKS],
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))", "gap": "16px"},
            ),
        ],
    )
