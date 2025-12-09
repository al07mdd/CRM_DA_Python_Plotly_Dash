from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, List

import pandas as pd
from dash import html, dcc, dash_table, register_page, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


register_page(
    __name__,
    path="/data/descriptive",
    name="3. Описательная статистика",
    title="Описательная статистика",
    order=30,
)


# Import analytics helpers
APP_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = APP_DIR.parent
sys.path.append(str(PROJECT_ROOT))
from src.analytics_descriptive import summarize_dataset, load_clean_csv  # type: ignore


DATASETS = ["Deals", "Calls", "Spend"]


def _table_kwargs() -> dict[str, Any]:
    """
    Общие стили для таблиц: компактная вёрстка, перенос строк и выравнивание по левому краю.
    """
    return dict(
        style_table={"overflowX": "hidden", "width": "100%", "minWidth": 0},
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "padding": "6px",
            "fontFamily": "Inter, system-ui",
            "fontSize": 13,
            "maxWidth": 320,
        },
        style_header={"textAlign": "left", "fontWeight": 600},
        css=[
            {
                "selector": ".dash-cell div.dash-cell-value",
                "rule": "white-space: normal; overflow: hidden; text-overflow: ellipsis;",
            },
            {"selector": ".dash-table-container", "rule": "max-width: 100%;"},
        ],
    )


def layout():
    """
    Макет страницы: слева sidebar, справа блоки управления, числовая сводка + boxplot, категориальные распределения.
    """
    from .sidebar import get_sidebar

    options = [{"label": name, "value": name} for name in DATASETS]
    default_value = options[0]["value"] if options else None

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        children=[
            get_sidebar(),
            html.Div(
                style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
                children=[
                    html.Article(
                        [
                            html.H3("Описательная статистика (по очищенным данным)"),
                            html.Div(
                                [
                                    html.Button("Обновить отчёт", id="desc-reload-btn"),
                                    dcc.ConfirmDialog(id="desc-reload-msg"),
                                ],
                                style={"display": "flex", "gap": "12px", "margin": "6px 0 8px"},
                            ),
                            html.H3("Файл"),
                            dcc.Dropdown(
                                id="desc-dataset-select",
                                options=options,
                                value=default_value,
                                clearable=False,
                                style={"maxWidth": 320, "margin": "8px 0 0"},
                            ),
                        ]
                    ),

                    html.Article(
                        [
                            html.H3("Числовые поля"),
                            dash_table.DataTable(
                                id="desc-numeric-table",
                                **_table_kwargs(),
                            ),
                            html.Div(
                                dcc.Graph(
                                    id="desc-boxplot",
                                    config={"displayModeBar": False},
                                    style={"width": "100%"},
                                ),
                                id="desc-boxplot-wrap",
                                style={
                                    "width": "100%",
                                    "maxHeight": "calc(100vh - 350px)",
                                    "overflowY": "auto",
                                    "marginTop": "16px",
                                },
                            ),
                        ]
                    ),

                    html.Article(
                        [
                            html.H3("Категориальные поля"),
                            dash_table.DataTable(
                                id="desc-cat-desc-table",
                                **_table_kwargs(),
                            ),
                            html.Div(
                                id="desc-cat-container",
                                style={
                                    "width": "100%",
                                    "maxHeight": "calc(100vh - 350px)",
                                    "overflowY": "auto",
                                },
                            ),
                            html.Details(
                                open=False,
                                children=[
                                    html.Summary("Примечания:"),
                                    html.Ul(id="desc-insights", style={"margin": "8px 0 0 16px"}),
                                ],
                                style={"marginTop": "12px"},
                            ),
                        ]
                    ),
                ],
            ),
        ],
    )


def _df_to_records(df: pd.DataFrame) -> tuple[list[dict[str, Any]], List[dict[str, str]]]:
    """
    Преобразовать DataFrame в (data, columns) для Dash DataTable.
    Индекс переносится в отдельную колонку 'column'.
    """
    if df is None or df.empty:
        return [], []
    df = df.copy()
    df.insert(0, "column", df.index.astype(str))
    data = df.reset_index(drop=True).to_dict("records")
    cols = [
        {"name": "column", "id": "column"},
        *[{"name": c, "id": c} for c in df.columns if c != "column"],
    ]
    return data, cols


def _make_boxplot(df: pd.DataFrame, columns: List[str]) -> go.Figure:
    """
    Построить набор горизонтальных boxplot-графиков: по одному на колонку,
    каждый на своей оси (оси независимы по масштабам).
    """
    if not columns or df is None or df.empty:
        return go.Figure()
    use_cols = [c for c in columns if c in df.columns]
    if not use_cols:
        return go.Figure()
    num = df[use_cols].apply(pd.to_numeric, errors="coerce")
    rows = len(use_cols)
    height_per = 250
    gap_px = 50
    total_h = rows * height_per + max(0, rows - 1) * gap_px
    vspace = (gap_px / total_h) if total_h > 0 else 0.0
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=False, vertical_spacing=vspace)
    for i, col in enumerate(use_cols, start=1):
        s = num[col].dropna()
        if s.empty:
            continue
        fig.add_trace(
            go.Box(x=s.values, name=col, boxpoints="outliers", orientation="h", showlegend=False),
            row=i, col=1,
        )
        fig.update_yaxes(showticklabels=False, title_text=col, automargin=True, row=i, col=1)
    fig.update_layout(height=total_h, autosize=True, margin=dict(l=60, r=8, t=6, b=6))
    return fig


def _make_bars_grid(df: pd.DataFrame | None, columns: List[str], top: int = 20) -> go.Figure:
    """
    Единый Figure для категориальных баров: вертикальные подграфики
    (по одному на колонку), одна колонка и независимые оси.
    """
    if df is None or not columns:
        return go.Figure()
    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols:
        return go.Figure()
    rows = len(valid_cols)
    height_per = 250
    gap_px = 50
    total_h = rows * height_per + (rows - 1) * gap_px
    vspace = (gap_px / total_h) if total_h > 0 else 0.0
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=False, vertical_spacing=vspace)
    for i, col in enumerate(valid_cols, start=1):
        s = df[col].value_counts(dropna=False).head(top)
        cats = s.index.astype(str)
        vals = s.values
        share = (s / s.sum() * 100).round(2)
        custom = [[p] for p in share.values]
        fig.add_trace(
            go.Bar(
                x=vals,
                y=cats,
                orientation="h",
                showlegend=False,
                customdata=custom,
                hovertemplate="%{y}   %{x}   %{customdata[0]}%<extra></extra>",
            ),
            row=i, col=1,
        )
        fig.update_yaxes(autorange="reversed", title_text=col, tickfont=dict(size=11), automargin=True, row=i, col=1)
    fig.update_layout(height=total_h, bargap=0.25, margin=dict(l=60, r=12, t=12, b=8))
    return fig


def _parse_notes_descriptions() -> dict[str, dict[str, str]]:
    """
    Разобрать notes/notes.txt и извлечь описания полей по датасетам
    (как на шаге 2). Разделители - блоки '=================' и пометки '(=...)'.
    Возвращает словарь: {dataset -> {column -> description}}.
    """
    notes_path = PROJECT_ROOT / "notes" / "notes.txt"
    result: dict[str, dict[str, str]] = {"Contacts": {}, "Calls": {}, "Spend": {}, "Deals": {}}
    try:
        if notes_path.exists():
            try:
                text = notes_path.read_text(encoding="utf-8")
            except Exception:
                text = notes_path.read_text(encoding="cp1251")
        else:
            text = ""
    except Exception:
        return result

    current: str | None = None
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if "=================" in ln:
            if "Contacts" in ln:
                current = "Contacts"; continue
            if "Calls" in ln:
                current = "Calls"; continue
            if "Spend" in ln:
                current = "Spend"; continue
            if "Deals" in ln:
                current = "Deals"; continue
            current = None
            continue
        if not current or ":" not in ln:
            continue
        field, desc = ln.split(":", 1)
        field = field.strip()
        if len(field) >= 3 and field[1] == "." and field[2] == " ":
            field = field[3:]
        desc = desc.strip()
        primary = field.split("(")[0].strip()
        if primary:
            result[current][primary] = desc
        result[current][field] = desc
        if "(=" in field and ")" in field:
            try:
                alias = field[field.index("(=") + 2 : field.index(")")].strip()
                if alias:
                    result[current][alias] = desc
            except Exception:
                pass
    return result


@callback(
    Output("desc-numeric-table", "data"),
    Output("desc-numeric-table", "columns"),
    Output("desc-boxplot", "figure"),
    Output("desc-cat-desc-table", "data"),
    Output("desc-cat-desc-table", "columns"),
    Output("desc-insights", "children"),
    Output("desc-cat-container", "children"),
    Output("desc-cat-container", "style"),
    Input("desc-dataset-select", "value"),
)
def update_descriptive(dataset_name: str | None):
    """
    Обновить данные для выбранного набора: таблицу сводной статистики (с description),
    boxplot по числовым полям, фигуру для категориальных баров и авто‑наблюдения.
    """
    if not dataset_name:
        return [], [], go.Figure(), [], [], [], [], {"width": "100%"}
    info = summarize_dataset(dataset_name)
    # Numeric table + descriptions
    num_df = info.get("numeric_summary") if isinstance(info, dict) else pd.DataFrame()
    if isinstance(num_df, pd.DataFrame) and not num_df.empty:
        desc_map = _parse_notes_descriptions().get(dataset_name, {})
        desc_series = pd.Series({idx: desc_map.get(str(idx), "") for idx in num_df.index})
        num_df = num_df.copy()
        num_df.insert(0, "description", desc_series)
    data, columns = _df_to_records(num_df if isinstance(num_df, pd.DataFrame) else pd.DataFrame())
    # Boxplot
    df = load_clean_csv(dataset_name)
    box_cols = info.get("numeric_cols", []) if isinstance(info, dict) else []
    fig_box = _make_boxplot(df, box_cols) if df is not None else go.Figure()
    # Categorical charts
    cat_cols = info.get("categorical_cols", []) if isinstance(info, dict) else []
    fig_bars = _make_bars_grid(df, cat_cols, top=20)
    cats = [dcc.Graph(figure=fig_bars, config={"displayModeBar": False}, style={"width": "100%"})]
    grid_style = {"width": "100%", "maxHeight": "calc(100vh - 350px)", "overflowY": "auto"}
    # Category descriptions (only used ones)
    valid_cat = [c for c in cat_cols if df is not None and c in df.columns]
    if valid_cat:
        desc_map = _parse_notes_descriptions().get(dataset_name, {})
        cat_desc_df = pd.DataFrame({"description": [desc_map.get(str(c), "") for c in valid_cat]}, index=valid_cat)
    else:
        cat_desc_df = pd.DataFrame()
    cat_desc_data, cat_desc_columns = _df_to_records(cat_desc_df)

    # Auto-insights (simple rules)
    insights: list[str] = []
    try:
        # Categorical: dominance, fragmentation, NaNs
        cat_map = info.get("categorical", {}) if isinstance(info, dict) else {}
        for c in cat_cols:
            freq = cat_map.get(c)
            if isinstance(freq, pd.DataFrame) and not freq.empty:
                if "percent" in freq.columns:
                    top_val = str(freq.index[0])
                    top_pct = float(freq.iloc[0]["percent"])
                    if top_pct >= 50:
                        insights.append(f"В {c} лидирует {top_val} ≈{round(top_pct)}%")
                    top10 = float(freq["percent"].head(10).sum())
                    if top10 < 70:
                        insights.append(f"В {c} много редких значений: топ-10 ≈{round(top10)}%")
            if df is not None and isinstance(df, pd.DataFrame) and c in df.columns:
                nan_share = float(df[c].isna().mean() * 100.0)
                if nan_share >= 20:
                    insights.append(f"Пропуски в {c}: {round(nan_share)}%")

        # Numeric: skewness, zeros as mode, wide range
        stats_df = info.get("numeric_summary") if isinstance(info, dict) else None
        if isinstance(stats_df, pd.DataFrame) and not stats_df.empty:
            for col, row in stats_df.iterrows():
                try:
                    mean = float(row.get("mean", float("nan")))
                    median = float(row.get("median", float("nan")))
                    mode_v = float(row.get("mode", float("nan")))
                    rng = float(row.get("range", float("nan")))
                except Exception:
                    continue
                if pd.notna(mean) and pd.notna(median) and median > 0 and mean >= 2 * median:
                    insights.append(f"Скошенность вправо в {col}: mean ({round(mean)}) > median ({round(median)})")
                if pd.notna(mode_v) and mode_v == 0 and ((pd.notna(median) and median == 0) or (pd.notna(mean) and mean > 0 and median / mean < 0.3)):
                    insights.append(f"Мода = 0 в {col} - много нулей/коротких значений")
                if pd.notna(rng) and pd.notna(median) and median > 0 and rng > 5 * median:
                    insights.append(f"Широкий разброс в {col} - см. boxplot")
    except Exception:
        insights = []
    insights = insights[:6]
    insight_children = [html.Li(t) for t in insights]

    return data, columns, fig_box, cat_desc_data, cat_desc_columns, insight_children, cats, grid_style

# ==============================================================================================
# ОПИСАТЕЛЬНАЯ СТАТИСТИКА: 

# Категории:
# Доминирование: топ‑1 ≥ 50% → «В <колонка> лидирует <значение> ≈<Y>% (доминирование)».
# Дробность: сумма топ‑10 < 70% → «В <колонка> много редких значений: топ‑10 ≈<T>%».
# Пропуски: NaN ≥ 20% → «Пропуски в <колонка>: <P>% - обратите внимание».

# Числа (mean/median/mode/range):
# Скошенность: mean ≥ 2 * median → «Скошенность вправо в <метрика>: mean (M) ≫ median (Md)».
# Нули: mode = 0 и median = 0 или median/mean < 0.3 → «Мода=0 → много нулей/коротких значений».
# Разброс: range > 5 * median → «Широкий разброс… → см. boxplot».

# ==============================================================================================

@callback(
    Output("desc-reload-msg", "displayed"),
    Output("desc-reload-msg", "message"),
    Input("desc-reload-btn", "n_clicks"),
    State("desc-dataset-select", "value"),
    prevent_initial_call=True,
)
def reload_desc_report(n_clicks: int, selected_dataset: str | None):
    """
    Кнопка «Обновить»: заново перечитываем текущий набор (без кеша) и показываем подтверждение.
    """
    dataset = selected_dataset or (DATASETS[0] if DATASETS else None)
    if not dataset:
        return True, "Нет выбранного набора - выберите файл для обновления."
    try:
        summarize_dataset(dataset)
        msg = f"Данные обновлены: пересчитан набор «{dataset}». При необходимости переключите файл."
    except Exception as exc:  # noqa: BLE001
        msg = f"Не удалось перечитать «{dataset}»: {exc}"
    return True, msg
