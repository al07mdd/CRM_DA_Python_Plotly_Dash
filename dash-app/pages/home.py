from __future__ import annotations

from dash import dcc, html, register_page, callback, Input, Output, no_update


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

HERO_STATS_EN = [
    {"value": "4", "label": "CRM SOURCES", "desc": "Contacts, Calls, Spend, Deals"},
    {"value": "4", "label": "CORE DASHBOARDS", "desc": "Marketing, Sales, Product, Final deck"},
]

HERO_STATS_DE = [
    {"value": "4", "label": "CRM-QUELLEN", "desc": "Kontakte, Anrufe, Ausgaben, Deals"},
    {"value": "4", "label": "KERNDASHBOARDS", "desc": "Marketing, Vertrieb, Produkt, Abschlussfolien"},
]

SECTION_LINKS_EN = [
    {
        "title": "Data",
        "links": [
            {"label": "Import", "href": "/data/import"},
            {"label": "Cleaning", "href": "/data/cleaning"},
            {"label": "Descriptive statistics", "href": "/data/descriptive"},
        ],
    },
    {
        "title": "Visualizations",
        "links": [
            {"label": "Time series", "href": "/viz/timeseries"},
            {"label": "Campaigns", "href": "/viz/campaigns"},
            {"label": "Sales", "href": "/viz/sales"},
            {"label": "Payments", "href": "/viz/payments"},
            {"label": "Geo", "href": "/viz/geo"},
        ],
    },
    {
        "title": "Product analytics",
        "links": [
            {"label": "Unit economics", "href": "/product/unit-economics"},
            {"label": "Growth points", "href": "/product/growth-points"},
            {"label": "Metric tree", "href": "/product/metric-tree"},
            {"label": "Hypotheses", "href": "/product/hypotheses"},
        ],
    },
    {
        "title": "Reports",
        "links": [
            {"label": "Full report - Python DA", "href": "/reports/full"},
            {"label": "Full report - Unit Economics", "href": "/reports/full-ue"},
            {"label": "Final presentation - Python DA", "href": "/reports/presentation-final"},
        ],
    },
]

SECTION_LINKS_DE = [
    {
        "title": "Daten",
        "links": [
            {"label": "Import", "href": "/data/import"},
            {"label": "Bereinigung", "href": "/data/cleaning"},
            {"label": "Deskriptive Statistik", "href": "/data/descriptive"},
        ],
    },
    {
        "title": "Visualisierungen",
        "links": [
            {"label": "Zeitreihen", "href": "/viz/timeseries"},
            {"label": "Kampagnen", "href": "/viz/campaigns"},
            {"label": "Vertrieb", "href": "/viz/sales"},
            {"label": "Zahlungen", "href": "/viz/payments"},
            {"label": "Geo", "href": "/viz/geo"},
        ],
    },
    {
        "title": "Produktanalytik",
        "links": [
            {"label": "Unit Economics", "href": "/product/unit-economics"},
            {"label": "Wachstumspunkte", "href": "/product/growth-points"},
            {"label": "Metrikbaum", "href": "/product/metric-tree"},
            {"label": "Hypothesen", "href": "/product/hypotheses"},
        ],
    },
    {
        "title": "Berichte",
        "links": [
            {"label": "Vollständiger Bericht - Python DA", "href": "/reports/full"},
            {"label": "Vollständiger Bericht - Unit Economics", "href": "/reports/full-ue"},
            {"label": "Abschlusspräsentation - Python DA", "href": "/reports/presentation-final"},
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
            html.Div(
                [
                    dcc.RadioItems(
                        id="home-lang-selector",
                        options=[
                            {"label": "RU", "value": "ru"},
                            {"label": "EN", "value": "en"},
                            {"label": "DE", "value": "de"},
                        ],
                        value="ru",
                        inline=True,
                        style={"fontSize": "13px"},
                    ),
                ],
                style={"alignSelf": "flex-end", "display": "flex", "flexDirection": "column", "gap": "4px"},
            ),
            html.Article(
                [
                    html.H1(
                        "Анализ CRM системы онлайн-школы программирования X.",
                        id="home-hero-title",
                    ),
                    html.Div(
                        [_stat_block(stat) for stat in HERO_STATS],
                        id="home-hero-stats",
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
                id="home-section-cards",
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))", "gap": "16px"},
            ),
        ],
    )


@callback(Output("app-lang", "data"), Input("home-lang-selector", "value"))
def _set_app_language(lang_value: str | None) -> str:
    if not lang_value:
        return "ru"
    return lang_value


@callback(
    Output("home-hero-title", "children"),
    Output("home-hero-stats", "children"),
    Output("home-section-cards", "children"),
    Input("app-lang", "data"),
)
def _update_home_texts(lang_value: str | None):
    lang = lang_value or "ru"

    if lang == "en":
        title = "Analysis of the CRM system of programming online school X."
        stats = [_stat_block(stat) for stat in HERO_STATS_EN]
        sections = [_section_card(card) for card in SECTION_LINKS_EN]
    elif lang == "de":
        title = "Analyse des CRM-Systems der Programmierschule X."
        stats = [_stat_block(stat) for stat in HERO_STATS_DE]
        sections = [_section_card(card) for card in SECTION_LINKS_DE]
    else:
        title = "Анализ CRM системы онлайн-школы программирования X."
        stats = [_stat_block(stat) for stat in HERO_STATS]
        sections = [_section_card(card) for card in SECTION_LINKS]

    return title, stats, sections

