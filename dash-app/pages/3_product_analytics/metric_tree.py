from __future__ import annotations

import math
import dash

from dash import html, dcc, register_page, callback, Input, Output, State, ALL

NODE_WIDTH = 120
NODE_HEIGHT = 36
CANVAS_WIDTH = 860
LAYER_GAP = 80

NODE_COLORS = {
    "target": "#7c3aed",
    "financial": "#3b82f6",
    "decision": "#10b981",
    "product": "#ef4444",
    "atomic": "#f97316",
}

LAYER_SPEC = [
    [("cm", "CM", "target")],
    [("ua", "UA", "decision"), ("ltv", "LTV", "product"), ("cpa", "CPA", "decision")],
    [("cltv", "CLTV", "product"), ("c1", "C1", "decision"), ("ac", "AC", "product")],
    [("b", "B", "product"), ("aov", "AOV", "decision"), ("apc", "APC", "decision"), ("cac", "CAC", "product")],
    [("t", "T", "product"), ("revenue", "Revenue", "financial")],
    [("ri", "R_I", "product")],
    [("aov_i", "AOV_I", "product")],
    [
        ("deal_contact_name", "Contact Name", "atomic"),
        ("deal_stage", "Stage", "atomic"),
        ("deal_product", "Product", "atomic"),
        ("deal_course_duration", "Course duration", "atomic"),
        ("deal_months", "Months of study", "atomic"),
        ("deal_initial", "Initial Amount", "atomic"),
    ],
    [
        ("deal_total", "Offer Total", "atomic"),
        ("deal_created", "Created Time", "atomic"),
        ("spend_spend", "Spend", "atomic"),
        ("contacts_id", "Contacts Id", "atomic"),
        ("calls_contact", "Calls CONTACTID", "atomic"),
    ],
]

EDGE_LIST = [
    ("ua", "cm"),
    ("ltv", "cm"),
    ("cpa", "cm"),
    ("cltv", "ltv"),
    ("c1", "ltv"),
    ("aov", "cltv"),
    ("apc", "cltv"),
    ("revenue", "aov"),
    ("t", "aov"),
    ("t", "apc"),
    ("b", "apc"),
    ("b", "c1"),
    ("ua", "c1"),
    ("ac", "cpa"),
    ("ua", "cpa"),
    ("ri", "revenue"),
    ("aov_i", "ri"),
    ("deal_course_duration", "aov_i"),
    ("deal_months", "aov_i"),
    ("deal_initial", "aov_i"),
    ("deal_total", "aov_i"),
    ("deal_months", "ri"),
    ("deal_months", "t"),
    ("deal_stage", "b"),
    ("deal_product", "b"),
    ("deal_contact_name", "ua"),
    ("contacts_id", "ua"),
    ("calls_contact", "ua"),
    ("deal_created", "ua"),
    ("spend_spend", "ac"),
    ("ac", "cac"),
    ("b", "cac"),
]

NODE_INFO = {
    "cm": {
        "title": "CM",
        "essence": "Маржинальная прибыль",
        "formula": "CM = UA * (LTV - CPA)",
    },
    "ua": {
        "title": "UA - юниты",
        "essence": "Сколько уникальных людей узнали о нас и могут стать клиентами",
        "formula": "UA = max(unique(Deals.Contact Name), unique(Contacts.Id), unique(Calls.CONTACTID))",
    },
    "ltv": {
        "title": "LTV - прибыль на юнит",
        "essence": "Средняя валовая прибыль на юнит (учитывает C1)",
        "formula": "LTV = CLTV * C1",
    },
    "cpa": {
        "title": "CPA - стоимость юнита",
        "essence": "Стоимость привлечения одного потенциального клиента",
        "formula": "CPA = AC / UA",
    },
    "cltv": {
        "title": "CLTV - прибыль на клиента",
        "essence": "Средняя валовая прибыль на клиента (не учитывает C1)",
        "formula": "CLTV = AOV * APC",
    },
    "c1": {
        "title": "C1 - конверсия",
        "essence": "Доля юнитов, ставших покупателями",
        "formula": "C1 = B / UA",
    },
    "aov": {
        "title": "AOV - средний чек",
        "essence": "Средняя выручка за транзакцию",
        "formula": "AOV = Revenue / T",
    },
    "apc": {
        "title": "APC - платежей на клиента",
        "essence": "Среднее количество транзакций на одного клиента",
        "formula": "APC = T / B",
    },
    "b": {
        "title": "B - клиенты",
        "essence": "Количество покупателей (Deals.Stage = 'payment done')",
        "formula": "B = unique(Deals.Id)",
    },
    "ac": {
        "title": "AC - маркетинговый бюджет",
        "essence": "Сколько денег потратили на привлечение клиентов",
        "formula": "AC = sum(Spend.Spend)",
    },
    "t": {
        "title": "T - транзакции",
        "essence": "Сумма месяцев обучения (платежей)",
        "formula": "T = sum(Deals.Months of study)",
    },
    "revenue": {
        "title": "Revenue - выручка",
        "essence": "Суммарная выручка по клиентам",
        "formula": "Revenue = sum(R_I)",
    },
    "ri": {
        "title": "R_I - выручка студента",
        "essence": "Сколько приносит конкретный клиент за обучение",
        "formula": "R_I = AOV_I * Months of study",
    },
    "aov_i": {
        "title": "AOV_I - средний чек сделки",
        "essence": "Средний платеж по сделке с учетом первого платежа, остатка и длительности обучения",
        "formula": "IF(Offer Total Amount - Initial Amount Paid > 0; ((Months of study - 1) * (Offer Total Amount - Initial Amount Paid) / (Course duration - 1) + Initial Amount Paid) / Months of study; Offer Total Amount / Course duration)",
    },
    "cac": {
        "title": "CAC - стоимость клиента",
        "essence": "Стоимость привлечения одного клиента",
        "formula": "CAC = AC / B",
    },
    "deal_contact_name": {
        "title": "Deals: Contact Name",
        "essence": "Идентификатор контакта; (источник для поиска UA)",
        "formula": "Источник: Deals",
    },
    "deal_stage": {"title": "Deals: Stage", "essence": "Фильтр покупателей (payment done)", "formula": "Используется в B"},
    "deal_product": {"title": "Deals: Product", "essence": "Сегментация по продуктам", "formula": "Используется в отчетах"},
    "deal_course_duration": {
        "title": "Deals: Course duration",
        "essence": "Длительность курса, влияет на AOV_I",
        "formula": "Источник: Deals",
    },
    "deal_months": {
        "title": "Deals: Months of study",
        "essence": "Количество месяцев обучения; суммируется в T",
        "formula": "Источник транзакций",
    },
    "deal_initial": {
        "title": "Deals: Initial Amount Paid",
        "essence": "Первоначальный платеж для формулы AOV_I",
        "formula": "Источник: Deals",
    },
    "deal_total": {
        "title": "Deals: Offer Total Amount",
        "essence": "Полная стоимость курса; участвует в AOV_I",
        "formula": "Источник: Deals",
    },
    "deal_created": {
        "title": "Deals: Created Time",
        "essence": "Дата создания сделки; нужна для анализа периода и темпа UA",
        "formula": "Используется в планировании тестов",
    },
    "spend_spend": {"title": "Spend: Spend", "essence": "Расходы на рекламу; источник AC", "formula": "Источник: Spend"},
    "contacts_id": {"title": "Contacts: Id", "essence": "Идентификатор контакта; (источник для поиска UA)", "formula": "Контакты"},
    "calls_contact": {
        "title": "Calls: CONTACTID",
        "essence": "Идентификатор контакта; (источник для поиска UA)",
        "formula": "Calls",
    },
}


def _generate_nodes():
    """
    Формирует координаты всех нод по слоям дерева.
    """
    nodes = []
    for layer_index, layer in enumerate(LAYER_SPEC):
        y = 20 + layer_index * LAYER_GAP
        count = len(layer)
        for order, (node_id, label, kind) in enumerate(layer):
            center = (order + 1) * CANVAS_WIDTH / (count + 1)
            x = center - NODE_WIDTH / 2
            nodes.append({"id": node_id, "label": label, "kind": kind, "x": x, "y": y})
    return nodes


NODES = _generate_nodes()


def _relations_map():
    """
    Возвращает словарь связей: для каждой метрики список соседей.
    """
    relations = {node["id"]: set() for node in NODES}
    for src, dst in EDGE_LIST:
        relations.setdefault(src, set()).add(dst)
        relations.setdefault(dst, set()).add(src)
    return relations


RELATIONS = _relations_map()


def _edge_divs(selected_id: str | None):
    """
    Рисует линии между нодами и подсвечивает активные связи.
    """
    node_lookup = {node["id"]: node for node in NODES}
    edges = []
    for src, dst in EDGE_LIST:
        s = node_lookup[src]
        t = node_lookup[dst]
        start_x = s["x"] + NODE_WIDTH / 2
        start_y = s["y"] + NODE_HEIGHT
        end_x = t["x"] + NODE_WIDTH / 2
        end_y = t["y"]
        dx = end_x - start_x
        dy = end_y - start_y
        length = (dx**2 + dy**2) ** 0.5
        angle = math.degrees(math.atan2(dy, dx))
        color = "#94a3b8"
        width = 1
        if selected_id:
            if src == selected_id:
                color = "#f97316"
                width = 2
            elif dst == selected_id:
                color = "#0ea5e9"
                width = 2
        edges.append(
            html.Div(
                style={
                    "position": "absolute",
                    "left": f"{start_x}px",
                    "top": f"{start_y}px",
                    "width": f"{length}px",
                    "borderTop": f"{width}px dotted {color}",
                    "transformOrigin": "0 0",
                    "transform": f"rotate({angle}deg)",
                    "opacity": 0.95 if width == 2 else 0.65,
                }
            )
        )
    return edges


def _node_divs(selected_id: str | None):
    """
    Создает кнопки-ноды и подсвечивает выбранные и связанные метрики.
    """
    nodes = []
    related = RELATIONS.get(selected_id, set()) if selected_id else set()
    for node in NODES:
        is_selected = node["id"] == selected_id
        is_related = node["id"] in related
        style = {
            "position": "absolute",
            "left": f"{node['x']}px",
            "top": f"{node['y']}px",
            "width": f"{NODE_WIDTH}px",
            "height": f"{NODE_HEIGHT}px",
            "borderRadius": "8px",
            "backgroundColor": NODE_COLORS.get(node["kind"], "#1f2937"),
            "color": "#fff",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "fontWeight": 600,
            "fontSize": "13px",
            "boxShadow": "0 4px 10px rgba(0,0,0,0.2)",
            "cursor": "pointer",
            "border": "2px solid transparent",
            "opacity": 1.0 if (is_selected or is_related or not selected_id) else 0.45,
        }
        if is_selected:
            style["border"] = "2px solid #f97316"
        elif is_related:
            style["border"] = "2px solid rgba(249,115,22,0.6)"
        nodes.append(
            html.Button(
                node["label"],
                id={"type": "metric-node", "id": node["id"]},
                n_clicks=0,
                style=style,
                className="metric-node",
            )
        )
    return nodes


def _canvas_elements(selected_id: str | None):
    """
    Комбинирует линии и ноды для текущего выбора.
    """
    return _edge_divs(selected_id) + _node_divs(selected_id)


def _canvas_container(selected_id: str | None):
    """
    Оборачивает элементы дерева в контейнер фиксированного размера.
    """
    return html.Div(
        _canvas_elements(selected_id),
        id="metric-tree-canvas",
        style={
            "position": "relative",
            "minHeight": "700px",
            "width": "100%",
            "maxWidth": "880px",
            "maxHeight": "720px",
            "margin": "0 auto",
        },
    )


def _metric_sections():
    """
    Готовит таблицы для примечания.
    """
    sections = []
    blocks = [
        ("Целевая метрика", ["cm"]),
        ("Метрики принятия решений (UE)", ["ua", "c1", "cpa", "aov", "apc"]),
        ("Финансовые метрики", ["revenue"]),
        ("Продуктовые метрики", ["b", "ac", "t", "cac", "cltv", "ltv", "aov_i", "ri"]),
        (
            "Атомные метрики (данные)",
            [
                "deal_contact_name",
                "deal_stage",
                "deal_product",
                "deal_course_duration",
                "deal_months",
                "deal_initial",
                "deal_total",
                "deal_created",
                "spend_spend",
                "contacts_id",
                "calls_contact",
            ],
        ),
    ]
    for title, keys in blocks:
        rows = []
        for key in keys:
            info = NODE_INFO.get(key, {})
            rows.append(
                {
                    "title": info.get("title", key),
                    "essence": info.get("essence", "-"),
                    "formula": info.get("formula", "-"),
                }
            )
        table = html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Метрика", style={"width": "30%", "border": "1px solid #e5e7eb", "padding": "6px"}),
                            html.Th("Суть", style={"width": "40%", "border": "1px solid #e5e7eb", "padding": "6px"}),
                            html.Th("Формула / как получаем", style={"width": "30%", "border": "1px solid #e5e7eb", "padding": "6px"}),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(row["title"], style={"border": "1px solid #e5e7eb", "padding": "6px", "fontWeight": 600}),
                                html.Td(row["essence"], style={"border": "1px solid #e5e7eb", "padding": "6px"}),
                                html.Td(
                                    row["formula"],
                                    style={"border": "1px solid #e5e7eb", "padding": "6px", "fontFamily": "monospace", "fontSize": "13px"},
                                ),
                            ]
                        )
                        for row in rows
                    ]
                ),
            ],
            style={"borderCollapse": "collapse", "width": "100%"},
        )
        sections.append(
            html.Div(
                [html.H4(title, style={"marginBottom": "6px"}), table],
                style={"marginTop": "12px"},
            )
        )

    growth_rows = [
        ("UA", "Увеличить охват / трафик (напр., +10%)"),
        ("C1", "Повысить конверсию лидов в оплату"),
        ("CPA", "Снизить стоимость привлечения юнита"),
        ("AOV", "Повысить средний чек"),
        ("APC", "Увеличить число платежей на клиента (число месяцев обучения)"),
    ]
    growth_table = html.Table(
        [
            html.Thead(html.Tr([html.Th("Метрика"), html.Th("Рычаг")])) ,
            html.Tbody([html.Tr([html.Td(name), html.Td(desc)]) for name, desc in growth_rows]),
        ],
        style={"borderCollapse": "collapse", "width": "100%"},
    )
    sections.append(
        html.Div(
            [
                html.H4("Метрики для поиска точек роста CM", style={"marginBottom": "6px"}),
                growth_table,
            ],
            style={"marginTop": "12px"},
        )
    )
    return sections


def _build_tooltip(selected_id: str | None):
    """
    Создает содержимое подсказки для выбранной метрики.
    """
    if not selected_id:
        return html.Div(
            [
                html.H4("Выберите метрику", style={"margin": "0"}),
                html.P("Нажмите на любую метрику в дереве, чтобы увидеть описание.", style={"margin": "4px 0"}),
            ]
        )
    info = NODE_INFO.get(selected_id, NODE_INFO["cm"])
    related = ", ".join(sorted(RELATIONS.get(selected_id, []))) or "-"
    return html.Div(
        [
            html.H4(info["title"], style={"margin": "0"}),
            html.P(info["essence"], style={"margin": "4px 0 6px"}),
            html.Code(info["formula"], style={"display": "block", "whiteSpace": "pre-wrap", "fontSize": "12px"}),
            html.Small(f"Связанные метрики: {related}"),
        ]
    )


register_page(
    __name__,
    path="/product/metric-tree",
    name="Metric Tree",
    title="Unit Economics Metric Tree",
    order=110,
)


def layout():
    """
    Собирает страницу дерева метрик Dash.
    """
    from .sidebar import get_sidebar

    notes = html.Details(
        open=False,
        children=[
            html.Summary("Метрики и формулы"),
            html.Div(_metric_sections(), style={"marginTop": "12px", "display": "flex", "flexDirection": "column", "gap": "8px"}),
        ],
    )

    right_col = html.Div(
        style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            html.Article(
                className="viz-card",
                children=[
                    html.H3("Дерево метрик юнит-экономики"),
                    html.Div(
                        [
                            _canvas_container(None),
                            html.Div(
                                id="metric-tooltip",
                                children=_build_tooltip(None),
                                style={
                                    "position": "absolute",
                                    "top": "24px",
                                    "right": "24px",
                                    "width": "300px",
                                    "backgroundColor": "#fff",
                                    "border": "1px solid #e5e7eb",
                                    "borderRadius": "10px",
                                    "padding": "12px",
                                    "boxShadow": "0 8px 24px rgba(0,0,0,0.08)",
                                    "fontSize": "13px",
                                },
                            ),
                            dcc.Store(id="metric-tree-selection", data=None),
                        ],
                        style={"position": "relative"},
                    ),
                ],
            ),
            html.Article(className="viz-card", children=[notes]),
        ],
    )

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        className="viz-page",
        children=[get_sidebar(), right_col],
    )


@callback(
    Output("metric-tree-selection", "data"),
    Input({"type": "metric-node", "id": ALL}, "n_clicks"),
    State("metric-tree-selection", "data"),
    prevent_initial_call=True,
)
def _select_node(_clicks, current):
    """
    Сохраняет выбранную метрику (с возможностью снять выбор).
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return current
    trigger = ctx.triggered_id
    if isinstance(trigger, dict):
        node_id = trigger.get("id")
        if node_id:
            return node_id if node_id != current else None
    return current


@callback(
    Output("metric-tree-canvas", "children"),
    Output("metric-tooltip", "children"),
    Input("metric-tree-selection", "data"),
)
def _update_tree(selected_id):
    """
    Перерисовывает дерево и подсказку при выборе ноды.
    """
    return _canvas_elements(selected_id), _build_tooltip(selected_id)
