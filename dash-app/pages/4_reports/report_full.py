from dash import dcc, html, register_page, callback, Input, Output
from .sidebar import get_sidebar


register_page(
    __name__,
    path="/reports/full",
    name="Текстовый отчет Python DA",
    title="Отчеты - Текстовый отчет Python DA",
    order=140,
)


REPORT_MD = """
# Всесторонний отчет по Python DA

## 1. Охват проекта
Этот финальный проект про полный цикл аналитики CRM для онлайн-школы программирования. Мы получем четыре таблицы (Contacts, Calls, Deals, Spend), очищаем их в Python и показываем результаты только в Dash (`dash-app/`)

---

## 2. Страницы подготовки данных

### 2.1 Проверка импорта (`/data/import`)
`src.simple_import` читает все файлы через `src.io.load_table`, проверяет кодировки, наличие столбцов, количество строк и столбцов, а также количество пропусков по каждому столбцу. Итоги записываются в `reports/import_checklist.{json,md}` и выводятся на странице `import_validation.py`

### 2.2 Примечания по очистке (`/data/cleaning`)
`src.cleaning.run_cleaning` приводит типы (даты, bool, категории), убирает лишние пробелы, нормализует справочники и пересчитывает признаки (`is_paid`, длительность сделки - `deal_lifetime_days`, время до первого звонка - `lead_to_first_call_sla_hours`). Все логируется в `reports/step2_eda_summary.{json,md}` и показывается на странице `cleaning_preparation.py`

### 2.3 Описательная статистика (`/data/descriptive`)
`src.analytics_descriptive` берет очищенные parquet-файлы и считает сводные статистики по числовым полям (среднее, медиана, минимум/максимум), а также распределения по категориям `Quality`, `Stage`, `Source`, `Product`. Это помогает убедиться, что очищенная схема данных соответствует ожиданиям перед тем, как переходить к аналитике

---

## 3. Страницы анализа Python DA

### 3.1 Анализ временных рядов (`/viz/timeseries`)

Процесс:(src.analytics_timeseries)

1. `load_deals_calls` загружает очищенные Deals и Calls

2. `make_daily_series` агрегирует дневные создания сделок, количество звонков и конверсию

3. `make_closed_daily` считает, сколько сделок дошли до `Stage="payment done"` по дням

4. `make_ttc_series` и `ttc_hist_counts` рассчитывают распределения time-to-close (для всех сделок и отдельно для оплаченных)

5. Страница Dash, с учетом выбранного месяца, запускает ETL и показывает:
- двухлинейный график: созданные сделки и звонки, плюс субплот с конверсией;
- тренд закрытых сделок;
- сводную таблицу (итоги, средние значения в день);
- box plot для вариативности дневных значений;
- гистограмму time-to-close (общие и оплаченные);
- блок примечаний с датами, конверсией, медианой/p90 TTC, статистиками по длительности звонков.

Трактовка: 
мы видим динамику обработки лидов, изменения в активности отдела продаж, моменты роста или падения звонков и скорость закрытия сделок. Фильтр по месяцам дает возможность изучать конкретные периоды

### 3.2 Анализ эффективности кампаний и источников (`/viz/campaigns`)

Процесс:(src.analytics_campaigns)

1. `load_campaign_data` объединяет Deals и Spend по `campaign/source`

2. `compute_all_metrics` и `funnel_table` формируют этапы воронки (показы -> клики -> лиды -> оплаченные) и метрики по источнику/кампании/группе объявлений:
- leads, paid, конверсия, CPL/CPA, ROAS, выручка

3. На странице Dash исходные таблицы хранятся в dcc.Store, чтобы не перезагружать данные при каждом изменении фильтра

4. Пользователь может отфильтровать данные по источнику, кампании или adgroup. Страница обновляет:
- референсную воронку и воронку после фильтра
- таблицу ROAS и scatter-графики (Spend vs. Paid, CPC vs. CR)
- глоссарий метрик CTR/CPL/CPA и др.
- таблицу метрик (по источникам, кампаниям или adgroup)

Трактовка:
можно понять, какие каналы окупаются, где бюджет работает лучше, какие кампании дают высокий CPL или низкую конверсию и куда стоит перераспределять средства

### 3.3 Анализ работы отдела продаж (`/viz/sales`)

Процесс:(src.analytics_sales)

1. `_prepare_with_calls` соединяет Deals и Calls через контакт (`CONTACTID <--> Deals:contact_id`). Каждая сделка получает количество звонков, время первого звонка и метрики

2. `owner_metrics` группирует показатели по менеджерам (Deal Owner Name):
- `calls_cnt_total` - общее число звонков
- `n_processed` - количество обработанных сделок (есть звонок или закрытая стадия)
- `calls_cnt_per_processed` - среднее число звонков на обработанную сделку
- конверсия, сумма оплат и др.

3. Визуализации Dash подчеркивают менеджеров с лучшими показателями обработки, быстротой первого контакта и эффективностью

Трактовка:
можно увидеть реальные паттерны работы менеджеров, выделяет лидеров и узкие места, сколько усилий нужно на сделку, как быстро она берется в работу и какие результаты приносит каждый сотрудник

### 3.4 Анализ платежей и продуктов (`/viz/payments`)

Процесс: (src.analytics_payments)

1. `load_deals_for_payments` читает очищенные сделки из `data/clean/Deals.parquet`/`Deals.csv`, приводит даты к одному формату и добавляет вспомогательный столбец `month` по дате создания сделки.

2. `payment_product_metrics` группирует сделки по комбинации **типа оплаты (`Payment Type`)**, **продукта (`Product`)** и **формата обучения (`Education Type`)**. 

3. Страница Dash использует три основных показателя: выручка (`revenue_total`), количество сделок (`n_deals`) и количество оплаченных сделок (`n_paid`). 
   - работает с ограниченным набором ключевых продуктов (`Web Developer`, `Digital Marketing`, `UX/UI Design`).
На основе отфильтрованных данных строится одна интерактивная treemap-диаграмма, где размер и цвет прямоугольников отражают выбранный показатель.

Трактовка:
страница показывает, как распределяются сделки и выручка между разными продуктами и форматами оплаты. По ней можно увидеть:
- какие сочетания «тип оплаты + продукт» дают наибольший вклад в выручку;
- где много сделок, но относительно мало оплаченных (если сравнивать `n_deals` и `n_paid`);
- как меняется структура выручки и объема сделок при переключении периода и выбранной метрики.

### 3.5 Географический анализ (`/viz/geo`)

Процесс: (src.analytics_geo)

1. `load_deals` читает Deals, а `load_city_coords` подгружает координаты городов (`data/temp/city_coords.parquet`)

2. города без координат получают данные из `MANUAL_COORDS`

3. `city_options`, `make_city_summary` и `make_level_city_summary` считают количество сделок, выручку и конверсию по городам и уровню языка

4. на странице отображаются карты (+ scatter) с итогами по городам

Трактовка:
карта помогает понять географию спроса, где концентрируются лиды и оплаты, какие города показывают лучшую конверсию, где есть точки роста

---

## 4. Раздел отчетов (`/reports/*`)
- `report_full.py` - всесторонний отчет по Python DA
- `report_full_ue.py` - всесторонний отчет по юнит-экономике
- `presentation_final.py` - финальная презентация по Python DA

Все страницы используют уже посчитанные данные; новых расчетов там нет

---

## 5. Основные выводы
1. **Рабочий процес воспроизводим.** Импорт, очистка, описательная статистика фиксируются в отчетах и доступны в Dash
2. **Dash покрывает весь операционный контур.** Лиды, звонки, кампании, продажи, платежи, география - все в одном интерфейсе
3. **Логика связей прозрачна.** Звонки привязываются к сделкам по контакту, кампании - по названию и источнику; это задокументировано в `DATA_SCHEMA.md`
4. **Фильтры и кнопки обновления держат данные актуальными.** Импорт и Time Series можно пересчитать прямо из UI, чтобы подтянуть свежие выгрузки
5. **Вся аналитика сосредоточена в `src/analytics_*`.** Dash лишь визуализирует готовые результат, поэтому понимать отчет можно, опираясь на описание модулей
"""


def layout():
    return html.Div(
        style={"display": "flex", "gap": "16px"},
        children=[
            get_sidebar(),
            html.Article(
                [
                    dcc.Markdown(REPORT_MD, id="report-full-md"),
                ],
                className="viz-card",
            ),
        ],
    )


# Placeholders for future English / German versions.
# You can replace these strings later with full Markdown translations.
REPORT_MD_EN = """# Comprehensive Report

## 1. Project scope
This final project covers the full CRM analytics cycle for an online programming school. We work with four tables (Contacts, Calls, Deals, Spend), clean them in Python and show the results only in Dash (`dash-app/`).

---

## 2. Data preparation pages

### 2.1 Import check (`/data/import`)
`src.simple_import` reads all files via `src.io.load_table`, checks encodings, required columns, row and column counts, and the number of missing values in each column. The results are stored in `reports/import_checklist.{json,md}` and displayed on the `import_validation.py` page.

### 2.2 Cleaning notes (`/data/cleaning`)
`src.cleaning.run_cleaning` standardises types (dates, booleans, categories), removes extra whitespace, normalises categorical values and recalculates features (`is_paid`, deal lifetime - `deal_lifetime_days`, time to first call - `lead_to_first_call_sla_hours`). All steps are logged to `reports/step2_eda_summary.{json,md}` and shown on the `cleaning_preparation.py` page.

### 2.3 Descriptive statistics (`/data/descriptive`)
`src.analytics_descriptive` takes cleaned parquet files and computes summary statistics for numeric fields (mean, median, min/max), as well as distributions for the categories `Quality`, `Stage`, `Source`, `Product`. This helps check that the cleaned data schema matches expectations before moving on to deeper analysis.

---

## 3. Python DA analysis pages

### 3.1 Time series analysis (`/viz/timeseries`)

Process (src.analytics_timeseries):
1. `load_deals_calls` loads cleaned Deals and Calls.
2. `make_daily_series` aggregates daily deal creations, call counts and conversion.
3. `make_closed_daily` counts how many deals per day reach `Stage="payment done"`.
4. `make_ttc_series` and `ttc_hist_counts` calculate time-to-close distributions (for all deals and separately for paid ones).
5. Taking the selected month into account, the Dash page runs the ETL and shows:
   - a dual-line chart (created deals and calls) plus a conversion subplot;
   - a trend of closed deals;
   - a summary table (totals and daily averages);
   - a box plot for day-to-day variation;
   - a time-to-close histogram (overall and paid);
   - a notes block with dates, conversion, TTC median/p90 and call duration statistics.

Interpretation:  
we see how leads are processed over time, how sales activity changes, where call volume grows or falls, and how quickly deals are closed. Monthly filtering makes it possible to study specific periods.

### 3.2 Campaign and source effectiveness (`/viz/campaigns`)

Process (src.analytics_campaigns):
1. `load_campaign_data` joins Deals and Spend by `campaign/source`.
2. `compute_all_metrics` and `funnel_table` construct funnel stages (impressions → clicks → leads → paid) and metrics by source/campaign/adgroup:
   - leads, paid deals, conversion, CPL/CPA, ROAS, revenue.
3. On the Dash page raw tables are stored in `dcc.Store` so data does not have to be reloaded on each filter change.
4. The user can filter by source, campaign or adgroup. The page updates:
   - the reference funnel and the funnel for the selected segment;
   - the ROAS table and scatter plots (Spend vs. Paid, CPC vs. CR);
   - the glossary of metrics (CTR/CPL/CPA, etc.);
   - the metrics table (by sources, campaigns or adgroups).

Interpretation:  
this makes it possible to see which channels pay off, where the budget performs better or worse, which campaigns have high CPL or low conversion, and where it is worth reallocating funds.

### 3.3 Sales team performance (`/viz/sales`)

Process (src.analytics_sales):
1. `_prepare_with_calls` joins Deals and Calls using the contact (`CONTACTID <--> Deals.contact_id`). Each deal receives a call count, time of first call and SLA metrics.
2. `owner_metrics` aggregates indicators by manager (Deal Owner Name):
   - `calls_cnt_total` – total number of calls;
   - `n_processed` – number of processed deals (there is a call or the stage is closed);
   - `calls_cnt_per_processed` – average number of calls per processed deal;
   - conversion, paid amount and other metrics.
3. Dash visualisations highlight managers with the best processing, fastest first contact and strongest performance.

Interpretation:  
we can see real patterns in how managers work, identify leaders and bottlenecks, understand how many calls are needed per deal, how quickly deals are picked up and what results each person delivers.

### 3.4 Payments and products analysis (`/viz/payments`)

Process (src.analytics_payments):
1. `load_deals_for_payments` reads cleaned deals from `data/clean/Deals.parquet`/`Deals.csv`, standardises date formats and adds the auxiliary `month` column based on the creation date.
2. `payment_product_metrics` groups deals by a combination of **payment type (`Payment Type`)**, **product (`Product`)** and **education format (`Education Type`)**.
3. The Dash page uses three main indicators: revenue (`revenue_total`), number of deals (`n_deals`) and number of paid deals (`n_paid`), and focuses on a limited set of key products (`Web Developer`, `Digital Marketing`, `UX/UI Design`). Based on the filters, it builds a single interactive treemap where the size and colour of rectangles reflect the chosen metric.

Interpretation:  
the page shows how deals and revenue are distributed between products and payment formats. You can see:
   - which “payment type + product” combinations contribute the most to revenue;
   - where there are many deals but relatively few paid ones (comparing `n_deals` and `n_paid`);
   - how the structure of revenue and deal volume changes when switching the period and selected metric.

### 3.5 Geographic analysis (`/viz/geo`)

Process (src.analytics_geo):
1. `load_deals` reads Deals, and `load_city_coords` loads city coordinates (`data/temp/city_coords.parquet`).
2. Cities without coordinates get values from `MANUAL_COORDS`.
3. `city_options`, `make_city_summary` and `make_level_city_summary` calculate deal counts, revenue and conversion by city and language level.
4. The page displays maps (plus scatter) with results by city.

Interpretation:  
the map helps understand the geography of demand: where leads and payments are concentrated, which cities have the best conversion and where there is growth potential.

---

## 4. Reports section (`/reports/*`)
- `report_full.py` – textual conclusions for Python DA;
- `presentation_python_da.py` – presentation for the team;
- `presentation_final.py` – final presentation for the client.

All pages use already computed data; no new calculations are performed there.

---

## 5. Key conclusions
1. **The workflow is reproducible.** Import, cleaning and descriptive statistics are recorded in reports and visible in Dash.
2. **Dash covers the entire operational contour.** Leads, calls, campaigns, sales, payments and geography are all in one interface.
3. **Join logic is transparent.** Calls are linked to deals by contact, campaigns by name and source; this is documented in `DATA_SCHEMA.md`.
4. **Filters and reload buttons keep data up to date.** Import and Time Series can be recalculated directly from the UI to pull in fresh dumps.
5. **All analytics is concentrated in `src/analytics_*`.** Dash only visualises ready-made results, so the report can be understood by referring to the module descriptions."""

REPORT_MD_DE = """# Umfassender Bericht

## 1. Projektumfang
Dieses Abschlussprojekt umfasst den gesamten CRM-Analyse-Zyklus für eine Online-Programmierschule. Wir arbeiten mit vier Tabellen (Contacts, Calls, Deals, Spend), bereinigen sie in Python und visualisieren die Ergebnisse ausschließlich in Dash (`dash-app/`).

---

## 2. Seiten zur Datenaufbereitung

### 2.1 Import-Kontrolle (`/data/import`)
`src.simple_import` liest alle Dateien über `src.io.load_table`, prüft Encodings, Pflichtspalten, Zeilen- und Spaltenanzahl sowie die Menge fehlender Werte in jeder Spalte. Die Ergebnisse werden in `reports/import_checklist.{json,md}` gespeichert und auf der Seite `import_validation.py` angezeigt.

### 2.2 Cleaning-Notizen (`/data/cleaning`)
`src.cleaning.run_cleaning` vereinheitlicht Datentypen (Datumswerte, Booleans, Kategorien), entfernt überflüssige Leerzeichen, normalisiert kategoriale Werte und berechnet Merkmale wie `is_paid`, Deal-Lebensdauer (`deal_lifetime_days`) und Time-to-First-Call (`lead_to_first_call_sla_hours`) neu. Alle Schritte werden in `reports/step2_eda_summary.{json,md}` protokolliert und auf der Seite `cleaning_preparation.py` visualisiert.

### 2.3 Deskriptive Statistik (`/data/descriptive`)
`src.analytics_descriptive` nimmt die bereinigten Parquet-Dateien und berechnet zusammenfassende Statistiken für numerische Felder (Mittelwert, Median, Min/Max) sowie Verteilungen für die Kategorien `Quality`, `Stage`, `Source`, `Product`. So lässt sich prüfen, ob das bereinigte Datenschema den Erwartungen entspricht, bevor man zu tiefergehenden Analysen übergeht.

---

## 3. Analyse-Seiten in Python DA

### 3.1 Zeitreihenanalyse (`/viz/timeseries`)

Ablauf (src.analytics_timeseries):
1. `load_deals_calls` lädt bereinigte Deals und Calls.
2. `make_daily_series` aggregiert täglich erstellte Deals, Call-Anzahl und Konversion.
3. `make_closed_daily` zählt, wie viele Deals pro Tag den Status `Stage="payment done"` erreichen.
4. `make_ttc_series` und `ttc_hist_counts` berechnen Time-to-Close-Verteilungen (für alle Deals und separat für bezahlte).
5. Unter Berücksichtigung des ausgewählten Monats führt die Dash-Seite das ETL aus und zeigt:
   - ein Dual-Liniendiagramm (erstellte Deals und Calls) plus Konversions-Subplot;
   - einen Trend der abgeschlossenen Deals;
   - eine Zusammenfassungstabelle (Summen und Tagesdurchschnitte);
   - einen Box-Plot für Tag-zu-Tag-Schwankungen;
   - ein Time-to-Close-Histogramm (insgesamt und nur für bezahlte Deals);
   - einen Notizblock mit Daten, Konversion, TTC-Median/p90 und Call-Dauer-Statistiken.

Interpretation:  
wir sehen, wie Leads über die Zeit verarbeitet werden, wie sich die Vertriebsaktivität verändert, wo die Call-Volumina wachsen oder fallen und wie schnell Deals geschlossen werden. Die Monats-Filterung erlaubt die Analyse spezifischer Zeiträume.

### 3.2 Kampagnen- und Quellen-Performance (`/viz/campaigns`)

Ablauf (src.analytics_campaigns):
1. `load_campaign_data` verbindet Deals und Spend über `campaign/source`.
2. `compute_all_metrics` und `funnel_table` bauen Funnel-Stufen (Impressions → Klicks → Leads → Paid) und Kennzahlen nach Quelle/Kampagne/Adgroup:
   - Leads, bezahlte Deals, Konversion, CPL/CPA, ROAS, Umsatz.
3. Auf der Dash-Seite werden die Roh-Tabellen in `dcc.Store` gehalten, damit die Daten beim Filtern nicht neu geladen werden müssen.
4. Der Nutzer kann nach Quelle, Kampagne oder Adgroup filtern. Die Seite aktualisiert:
   - den Referenz-Funnel und den Funnel für das gewählte Segment;
   - die ROAS-Tabelle und Scatter-Plots (Spend vs. Paid, CPC vs. CR);
   - das Kennzahlen-Glossar (CTR/CPL/CPA usw.);
   - die Kennzahlen-Tabelle (nach Quellen, Kampagnen oder Adgroups).

Interpretation:  
so lässt sich erkennen, welche Kanäle sich lohnen, wo das Budget besser oder schlechter arbeitet, welche Kampagnen hohe CPL oder niedrige Konversion haben und wo sich Budget-Umschichtung anbietet.

### 3.3 Performance des Sales-Teams (`/viz/sales`)

Ablauf (src.analytics_sales):
1. `_prepare_with_calls` verbindet Deals und Calls über den Kontakt (`CONTACTID <--> Deals.contact_id`). Jeder Deal erhält Call-Anzahl, Zeitpunkt des ersten Calls und SLA-Metriken.
2. `owner_metrics` aggregiert Kennzahlen nach Manager (Deal Owner Name):
   - `calls_cnt_total` – Gesamtanzahl Calls;
   - `n_processed` – Anzahl verarbeiteter Deals (es gibt einen Call oder die Stufe ist geschlossen);
   - `calls_cnt_per_processed` – durchschnittliche Call-Anzahl pro verarbeitetem Deal;
   - Konversion, bezahlte Summe und weitere Werte.
3. Die Dash-Visualisierungen heben Manager mit bester Bearbeitung, schnellstem Erstkontakt und stärkster Performance hervor.

Interpretation:  
wir sehen reale Arbeitsmuster der Manager, erkennen Leader und Engpässe, verstehen, wie viele Calls pro Deal nötig sind, wie schnell Deals aufgenommen werden und welche Ergebnisse jeder Einzelne liefert.

### 3.4 Analyse von Zahlungen und Produkten (`/viz/payments`)

Ablauf (src.analytics_payments):
1. `load_deals_for_payments` liest bereinigte Deals aus `data/clean/Deals.parquet`/`Deals.csv`, vereinheitlicht Datumsformate und fügt eine Hilfsspalte `month` basierend auf dem Erstellungsdatum hinzu.
2. `payment_product_metrics` gruppiert Deals nach Kombination aus **Zahlungsart (`Payment Type`)**, **Produkt (`Product`)** und **Ausbildungsformat (`Education Type`)**.
3. Die Dash-Seite nutzt drei Kernkennzahlen: Umsatz (`revenue_total`), Anzahl Deals (`n_deals`) und Anzahl bezahlter Deals (`n_paid`) und fokussiert sich auf eine begrenzte Menge Schlüsselprodukte (`Web Developer`, `Digital Marketing`, `UX/UI Design`). Auf Basis der Filter wird eine interaktive Treemap aufgebaut, in der Größe und Farbe der Rechtecke die gewählte Kennzahl widerspiegeln.

Interpretation:  
die Seite zeigt, wie sich Deals und Umsatz über Produkte und Zahlungsarten verteilen. Man sieht:
   - welche Kombinationen aus Zahlungsart + Produkt den größten Umsatzbeitrag leisten;
   - wo viele Deals, aber relativ wenige bezahlte Deals vorliegen (Vergleich von `n_deals` und `n_paid`);
   - wie sich Struktur von Umsatz und Deal-Volumen beim Wechsel von Zeitraum und Kennzahl verändert.

### 3.5 Geografische Analyse (`/viz/geo`)

Ablauf (src.analytics_geo):
1. `load_deals` liest Deals, `load_city_coords` lädt Stadtkoodinaten (`data/temp/city_coords.parquet`).
2. Städte ohne Koordinaten erhalten Werte aus `MANUAL_COORDS`.
3. `city_options`, `make_city_summary` und `make_level_city_summary` berechnen Deal-Anzahl, Umsatz und Konversion nach Stadt und Sprachlevel.
4. Die Seite zeigt Karten (plus Scatter-Plots) mit Ergebnissen nach Stadt.

Interpretation:  
die Karte hilft, die Geografie der Nachfrage zu verstehen: wo Leads und Zahlungen konzentriert sind, welche Städte die beste Konversion haben und wo Wachstumspotenzial besteht.

---

## 4. Report-Bereich (`/reports/*`)
- `report_full.py` – Text-Schlussfolgerungen für Python DA;
- `presentation_python_da.py` – Präsentation für das interne Team;
- `presentation_final.py` – Abschlusspräsentation für den Kunden.

Alle Seiten nutzen bereits berechnete Daten; es werden dort keine neuen Berechnungen durchgeführt.

---

## 5. Zentrale Schlussfolgerungen
1. **Der Workflow ist reproduzierbar.** Import, Cleaning und deskriptive Statistik sind in Reports festgehalten und in Dash sichtbar.  
2. **Dash deckt den gesamten operativen Bereich ab.** Leads, Calls, Kampagnen, Sales, Payments und Geografie liegen in einer gemeinsamen Oberfläche.  
3. **Die Join-Logik ist transparent.** Calls werden über den Kontakt an Deals angebunden, Kampagnen über Namen/Quelle; Details sind in `DATA_SCHEMA.md` dokumentiert.  
4. **Filter und Reload-Buttons halten Daten aktuell.** Import und Time Series können direkt aus dem UI neu berechnet werden, um frische Dumps einzulesen.  
5. **Alle Analytics-Logik steckt in `src/analytics_*`.** Dash visualisiert nur fertige Ergebnisse, sodass der Bericht über Modulbeschreibungen nachvollziehbar bleibt."""


@callback(Output("report-full-md", "children"), Input("app-lang", "data"))
def _update_report_full_md(lang_value: str | None):
    lang = (lang_value or "ru").lower()

    if lang == "en":
        return REPORT_MD_EN
    if lang == "de":
        return REPORT_MD_DE

    # Default: Russian original
    return REPORT_MD
