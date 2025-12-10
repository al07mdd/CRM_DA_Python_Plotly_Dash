from dash import html, register_page, callback, Input, Output


register_page(
    __name__,
    path="/reports/presentation-final",
    name="Финальная презентация проекта",
    title="Final Project - Финальная презентация",
    order=160,
)


def _slide(title: str, paragraphs: list[str], image_name: str | None = None) -> html.Article:
    children: list[html.Component] = [html.H3(title)]
    for p in paragraphs:
        children.append(html.P(p))
    if image_name:
        children.append(
            html.Img(
                src=f"/assets/presentation/{image_name}",
                alt=title,
                style={
                    "display": "block",
                    "maxWidth": "900px",
                    "width": "100%",
                    "margin": "12px auto 0",
                    "borderRadius": "12px",
                },
            )
        )
    return html.Article(children, className="viz-card")


def layout():
    from .sidebar import get_sidebar

    slides = [
        _slide(
            "Контекст и цель проекта",
            [
                "Заказчик - онлайн-школа программирования X, которая ведет учет лидов и сделок в CRM.",
                "Исходная проблема: данные разбросаны по выгрузкам Contacts, Calls, Deals и Spend, качество выгрузок нестабильно, нет единой управленческой отчетности.",
                "Цель: построить воспроизводимый рабочий процес Python DA и дашборд Dash, который отвечает на ключевые вопросы маркетинга и отдела продаж.",
            ],
            "01_intro.png",
        ),
        _slide(
            "Данные и структура CRM",
            [
                "В проекте используются четыре основные таблицы: Contacts, Calls, Deals и Spend.",
                "Contacts - хранит информацию о контактах (Id, ответственный менеджер, время создания и обновления, город, уровень языка, страница обращения).",
                "Calls - содержит историю звонков и ссылается на контакты через поле CONTACTID, что позволяет считать активность по каждому лиду и сделке.",
                "Deals - описывает сделки, связывает их с контактами и продуктами и фиксирует этап воронки, суммы и формат обучения.",
                "Spend - хранит рекламные расходы по источникам и кампаниям, которые затем сопоставляются с полями Source/Campaign/AdGroup в Deals.",
                "Структура и связи подробно описаны в DATA_SCHEMA.md; сырые данные из `data/raw` не попадают в репозиторий и используются только локально.",
            ],
        ),
        _slide(
            "Общий рабочий процес Python DA",
            [
                "Шаг 1 - импорт: src.simple_import через src.io.load_table читает выгрузки Contacts, Calls, Deals, Spend, проверяет схему и качество данных и формирует отчёт `reports/import_checklist.*`.",
                "Шаг 2 - очистка: src.cleaning приводит типы, нормализует категории, убирает шум и создаёт ключевые признаки (флаг оплаты, длительность сделки, SLA до первого контакта и др.), результат - parquet-файлы в `data/clean`.",
                "Шаг 3 - аналитика: модули src.analytics_* строят метрики и визуализации для разных задач (описательная статистика, временные ряды, кампании, продажи, платежи, география, юнит-экономика).",
                "Шаг 4 - визуализация: Dash-приложение (`dash-app/`) подключает эти визуализации и отображает их в разделах /data, /viz, /product и /reports для презентации результатов.",
            ],
        ),
        _slide(
            "Контроль импорта и очистки",
            [
                "Страница `/data/import` показывает, какие файлы загружены, сколько в них строк и столбцов, и какова доля пропусков по каждому полю.",
                "Страница `/data/cleaning` фиксирует все шаги очистки: какие преобразования выполнены, какие признаки добавлены и какие решения приняты по аномалиям и дубликатам.",
                "Эти два экрана дают прозрачность качества данных до того, как мы переходим к аналитике и визуализации.",
            ],
            "04_import_cleaning.png",
        ),
        _slide(
            "Временные ряды и воронка во времени",
            [
                "Раздел `/viz/timeseries` показывает, как во времени ведут себя основные показатели: сколько сделок создается, сколько совершается звонков и как меняется конверсия.",
                "Отдельные графики отражают, когда сделки доходят до оплаты и как распределено время до закрытия (time-to-close) для разных периодов.",
                "Фильтрация по месяцам позволяет сравнивать динамику до и после изменений во воронке или запусков кампаний.",
            ],
            "05_timeseries.png",
        ),
        _slide(
            "Эффективность кампаний и источников",
            [
                "Раздел `/viz/campaigns` объединяет Deals и Spend и считает воронку и ключевые маркетинговые метрики: CPL, CPA, ROAS, конверсию из лида в оплату.",
                "Фильтры по источнику, кампании и adgroup позволяют сравнивать сегменты между собой и видеть, как меняются показатели при смене фокуса.",
                "На основе этих метрик можно понять, какие каналы и кампании стоит масштабировать, а какие - оптимизировать или выключать.",
            ],
            "06_campaigns.png",
        ),
        _slide(
            "Работа отдела продаж",
            [
                "Раздел `/viz/sales` соединяет сделки и звонки и показывает, как менеджеры работают с лидами: сколько звонков приходится на одну обработанную сделку, как быстро происходит первый контакт и какие результаты по оплатам у каждого менеджера.",
                "Показатели считаются по каждому сотруднику, поэтому можно выделить сильных исполнителей и узкие места в процессе обработки лидов.",
                "Эта страница служит основой для управленческих решений по SLA, нагрузке и качеству работы команды продаж.",
            ],
            "07_sales.png",
        ),
        _slide(
            "Платежи и продуктовый портфель",
            [
                "Раздел `/viz/payments` анализирует сделки по продуктам, форматам оплаты и типам обучения.",
                "Treemap-диаграмма показывает, как распределяются сделки и выручка между различными комбинациями «тип оплаты - продукт - формат обучения».",
                "По этой странице можно оценить структуру продуктового портфеля, долю ключевых программ и влияние форматов оплаты на итоговый результат.",
            ],
            "08_payments.png",
        ),
        _slide(
            "География спроса",
            [
                "Раздел `/viz/geo` показывает карту с количеством сделок, оплат и конверсией по городам и уровням языка.",
                "Гео-аналитика помогает понять, где сконцентрирован спрос, какие регионы растут быстрее и где есть потенциал для локальных активностей.",
                "Эти выводы можно использовать для настройки региональных кампаний и офлайн-инициатив.",
            ],
            "09_geo.png",
        ),
        _slide(
            "Итоги и следующие шаги",
            [
                "Построен воспроизводимый пайплайн: при новой выгрузке из CRM достаточно обновить файлы в `data/raw` и запустить скрипты - дашборд обновится автоматически.",
                "Дашборд отвечает на ключевые вопросы: как устроена воронка во времени, какие источники и кампании окупаются, как работает отдел продаж, какие продукты и форматы оплаты дают основную выручку и где географические точки роста.",
                "Следующие шаги: развитие блока unit economics, добавление оповещений по SLA и автоматизация обновления данных по расписанию.",
            ],
            "10_summary.png",
        ),
    ]

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        children=[
            get_sidebar(),
            html.Div(
                id="presentation-slides",
                style={"flex": 1, "display": "flex", "flexDirection": "column", "gap": "16px"},
                children=slides,
            ),
        ],
    )


@callback(Output("presentation-slides", "children"), Input("app-lang", "data"))
def _update_presentation_slides(lang_value: str | None):
    lang = lang_value or "ru"

    if lang == "en":
        slides_en = [
    _slide(
        "Context and Project Goal",
        [
            "The client is an online programming school X that tracks leads and deals in a CRM.",
            "The initial challenge: data is scattered across four exports – Contacts, Calls, Deals and Spend; data quality is unstable, and there is no unified management reporting.",
            "Goal: build a reproducible Python DA workflow and a Dash dashboard that answers the key questions of the marketing and sales teams.",
        ],
        "01_intro.png",
    ),
    _slide(
        "Data and CRM Structure",
        [
            "The project uses four main tables: Contacts, Calls, Deals and Spend.",
            "Contacts - stores information about contacts (Id, assigned manager, creation and update timestamps, city, language level, landing page).",
            "Calls - contains the call history and links to contacts via CONTACTID, enabling us to measure activity per lead and per deal.",
            "Deals - describes deals, links them to contacts and products, and captures funnel stage, amounts and learning format.",
            "Spend - stores advertising expenses by sources and campaigns, which are then matched to the Source/Campaign/AdGroup fields in Deals.",
            "The structure and relationships are described in DATA_SCHEMA.md; raw data from `data/raw` is not included in the repository and is used only locally.",
        ],
    ),
    _slide(
        "Overall Python DA Workflow",
        [
            "Step 1 - Import: `src.simple_import` via `src.io.load_table` reads the exports Contacts, Calls, Deals and Spend, checks schema and data quality, and generates the report `reports/import_checklist.*`.",
            "Step 2 - Cleaning: `src.cleaning` adjusts data types, normalizes categories, removes noise and creates key features (payment flag, deal duration, SLA until first contact etc.); results are stored as parquet files in `data/clean`.",
            "Step 3 - Analytics: the `src.analytics_*` modules compute metrics and visualizations for multiple tasks (descriptive stats, time series, campaigns, sales, payments, geography, unit economics).",
            "Step 4 - Visualization: the Dash application (`dash-app/`) uses these visualizations and displays them in /data, /viz, /product and /reports for presenting results.",
        ],
    ),
    _slide(
        "Import and Cleaning Control",
        [
            "The `/data/import` page shows which files are loaded, how many rows and columns they contain, and the share of missing values per field.",
            "The `/data/cleaning` page documents all cleaning steps: what transformations were applied, which features were added, and how anomalies and duplicates were handled.",
            "These two screens provide transparency on data quality before moving to analytics and visualization.",
        ],
        "04_import_cleaning.png",
    ),
    _slide(
        "Time Series and Funnel Dynamics Over Time",
        [
            "The `/viz/timeseries` section shows how the main metrics behave over time: how many deals are created, how many calls are made, and how conversion changes.",
            "Separate charts show when deals reach payment and how time-to-close is distributed across different periods.",
            "Month-level filters allow comparing dynamics before and after funnel changes or campaign launches.",
        ],
        "05_timeseries.png",
    ),
    _slide(
        "Campaign and Source Performance",
        [
            "The `/viz/campaigns` section merges Deals and Spend and calculates funnel metrics and key marketing KPIs: CPL, CPA, ROAS, and lead-to-payment conversion.",
            "Filters by source, campaign and adgroup allow comparing segments and observing how metrics shift when focus changes.",
            "These metrics show which channels and campaigns should be scaled and which ones need optimization or shutdown.",
        ],
        "06_campaigns.png",
    ),
    _slide(
        "Sales Team Performance",
        [
            "The `/viz/sales` section links deals and calls and shows how managers work with leads: how many calls are made per processed deal, how quickly the first contact happens, and what payment results each manager achieves.",
            "Metrics are calculated per employee, making it possible to identify strong performers and bottlenecks in lead processing.",
            "This section supports management decisions related to SLA, workload and quality of the sales team’s work.",
        ],
        "07_sales.png",
    ),
    _slide(
        "Payments and Product Portfolio",
        [
            "The `/viz/payments` section analyzes deals by products, payment formats and learning types.",
            "A treemap visualizes how deals and revenue are distributed across combinations of payment type, product and learning format.",
            "This page helps assess the structure of the product portfolio, the share of key programs and the impact of payment formats on final revenue.",
        ],
        "08_payments.png",
    ),
    _slide(
        "Geography of Demand",
        [
            "The `/viz/geo` section displays a map with the number of deals, payments and conversion by cities and language levels.",
            "Geo analytics helps understand where demand is concentrated, which regions grow faster and where there is potential for local initiatives.",
            "These insights can support regional campaigns and offline activities.",
        ],
        "09_geo.png",
    ),
    _slide(
        "Summary and Next Steps",
        [
            "A reproducible pipeline is built: when new CRM exports are added to `data/raw` and scripts are run, the dashboard updates automatically.",
            "The dashboard answers key questions: how the funnel behaves over time, which sources and campaigns are profitable, how the sales team performs, which products and payment formats drive revenue, and where geographic growth points are.",
            "Next steps: extend unit economics analytics, add SLA alerts, and automate data updates on schedule.",
        ],
        "10_summary.png",
    ),
]
        return slides_en

    if lang == "de":
        slides_de = [
    _slide(
        "Projektkontext und Zielsetzung",
        [
            "Der Auftraggeber ist eine Online-Programmierschule X, die Leads und Deals in einem CRM verwaltet.",
            "Das Ausgangsproblem: Die Daten sind über vier Exporte verteilt – Contacts, Calls, Deals und Spend; die Datenqualität ist instabil und es fehlt ein einheitliches Management-Reporting.",
            "Ziel: Einen reproduzierbaren Python-DA-Workflow und ein Dash-Dashboard aufzubauen, das die zentralen Fragen von Marketing und Vertrieb beantwortet.",
        ],
        "01_intro.png",
    ),
    _slide(
        "Daten und CRM-Struktur",
        [
            "Im Projekt werden vier Haupttabellen verwendet: Contacts, Calls, Deals und Spend.",
            "Contacts - enthält Informationen zu Kontakten (Id, zuständiger Manager, Erstellungs- und Aktualisierungszeitpunkt, Stadt, Sprachniveau, Einstiegsseite).",
            "Calls - enthält die Anrufhistorie und ist über CONTACTID mit Contacts verknüpft, wodurch sich Aktivitäten pro Lead und pro Deal auswerten lassen.",
            "Deals - beschreibt Verkaufsabschlüsse, verknüpft sie mit Kontakten und Produkten und speichert Funnel-Stufe, Beträge und Lernformat.",
            "Spend - enthält Werbeausgaben nach Quellen und Kampagnen, die anschließend mit Source/Campaign/AdGroup in Deals abgeglichen werden.",
            "Struktur und Beziehungen sind in DATA_SCHEMA.md dokumentiert; Rohdaten aus `data/raw` sind nicht im Repository und werden nur lokal verwendet.",
        ],
    ),
    _slide(
        "Gesamter Python-DA-Workflow",
        [
            "Schritt 1 - Import: `src.simple_import` über `src.io.load_table` liest die Exporte Contacts, Calls, Deals und Spend ein, prüft Schema und Datenqualität und erzeugt den Bericht `reports/import_checklist.*`.",
            "Schritt 2 - Bereinigung: `src.cleaning` vereinheitlicht Datentypen, normalisiert Kategorien, entfernt Rauschen und erstellt zentrale Merkmale (Zahlungs-Flag, Deal-Dauer, SLA bis zum Erstkontakt usw.); Ergebnisse werden als Parquet-Dateien in `data/clean` gespeichert.",
            "Schritt 3 - Analytik: Die Module `src.analytics_*` berechnen Metriken und Visualisierungen für verschiedene Aufgaben (deskriptive Statistik, Zeitreihen, Kampagnen, Vertrieb, Zahlungen, Geografie, Unit Economics).",
            "Schritt 4 - Visualisierung: Die Dash-Anwendung (`dash-app/`) integriert diese Visualisierungen und zeigt sie in den Bereichen /data, /viz, /product und /reports an.",
        ],
    ),
    _slide(
        "Kontrolle von Import und Bereinigung",
        [
            "Die Seite `/data/import` zeigt, welche Dateien geladen wurden, wie viele Zeilen und Spalten sie enthalten und welchen Anteil fehlende Werte pro Feld ausmachen.",
            "Die Seite `/data/cleaning` dokumentiert alle Bereinigungsschritte: welche Transformationen durchgeführt wurden, welche Merkmale hinzugefügt wurden und wie Anomalien und Duplikate behandelt wurden.",
            "Diese beiden Ansichten schaffen Transparenz über die Datenqualität, bevor Analytik und Visualisierung beginnen.",
        ],
        "04_import_cleaning.png",
    ),
    _slide(
        "Zeitreihen und Funnel-Entwicklung über die Zeit",
        [
            "Der Bereich `/viz/timeseries` zeigt, wie sich die wichtigsten Kennzahlen im Zeitverlauf entwickeln: wie viele Deals entstehen, wie viele Anrufe getätigt werden und wie sich die Konversion verändert.",
            "Separate Diagramme zeigen, wann Deals bezahlt werden und wie sich die Time-to-Close in verschiedenen Zeiträumen verteilt.",
            "Monatsfilter ermöglichen Vergleiche vor und nach Funnel-Anpassungen oder Kampagnenstarts.",
        ],
        "05_timeseries.png",
    ),
    _slide(
        "Leistung von Kampagnen und Quellen",
        [
            "Der Bereich `/viz/campaigns` kombiniert Deals und Spend und berechnet Funnel-Kennzahlen und zentrale Marketing-KPIs: CPL, CPA, ROAS und Lead-to-Payment-Konversion.",
            "Filter nach Quelle, Kampagne und Adgroup ermöglichen Segmentvergleiche und zeigen, wie sich Kennzahlen bei Fokuswechsel ändern.",
            "Diese Metriken zeigen, welche Kanäle und Kampagnen skaliert werden sollten und welche optimiert oder abgeschaltet werden müssen.",
        ],
        "06_campaigns.png",
    ),
    _slide(
        "Leistung des Vertriebsteams",
        [
            "Der Bereich `/viz/sales` verbindet Deals und Anrufe und zeigt, wie Manager mit Leads arbeiten: wie viele Anrufe pro bearbeitetem Deal erfolgen, wie schnell der Erstkontakt stattfindet und welche Zahlungsergebnisse jeder Manager erzielt.",
            "Die Kennzahlen werden pro Mitarbeiter berechnet, wodurch starke Performer und Engpässe im Lead-Prozess identifiziert werden können.",
            "Dieser Bereich unterstützt Managemententscheidungen zu SLA, Arbeitslast und Qualität der Vertriebsarbeit.",
        ],
        "07_sales.png",
    ),
    _slide(
        "Zahlungen und Produktportfolio",
        [
            "Der Bereich `/viz/payments` analysiert Deals nach Produkten, Zahlungsformaten und Lerntypen.",
            "Eine Treemap zeigt, wie Deals und Umsatz über Kombinationen aus Zahlungsart, Produkt und Lernformat verteilt sind.",
            "Diese Seite ermöglicht die Bewertung der Portfolio-Struktur, der Bedeutung zentraler Programme und des Einflusses von Zahlungsformaten auf den Umsatz.",
        ],
        "08_payments.png",
    ),
    _slide(
        "Geografische Nachfrage",
        [
            "Der Bereich `/viz/geo` zeigt eine Karte mit der Anzahl der Deals, Zahlungen und Konversionen nach Städten und Sprachniveaus.",
            "Die Geo-Analytik zeigt, wo die Nachfrage konzentriert ist, welche Regionen schneller wachsen und wo Potenzial für lokale Aktivitäten besteht.",
            "Diese Erkenntnisse unterstützen regionale Kampagnen und Offline-Initiativen.",
        ],
        "09_geo.png",
    ),
    _slide(
        "Fazit und nächste Schritte",
        [
            "Ein reproduzierbarer Pipeline wurde aufgebaut: Bei neuen CRM-Exporten müssen die Dateien nur in `data/raw` aktualisiert und die Skripte ausgeführt werden – das Dashboard aktualisiert sich automatisch.",
            "Das Dashboard beantwortet zentrale Fragen: Wie sich der Funnel im Zeitverlauf entwickelt, welche Quellen und Kampagnen profitabel sind, wie das Vertriebsteam arbeitet, welche Produkte und Zahlungsformate den Umsatz treiben und wo geografische Wachstumspunkte liegen.",
            "Nächste Schritte: Ausbau der Unit-Economics-Analytik, Hinzufügen von SLA-Benachrichtigungen und Automatisierung der Datenaktualisierung per Zeitplan.",
        ],
        "10_summary.png",
    ),
]
        return slides_de

    # Russian or unknown: rebuild original Russian slides from the page layout
    ru_layout = layout()
    try:
        return ru_layout.children[1].children
    except Exception:
        return []
