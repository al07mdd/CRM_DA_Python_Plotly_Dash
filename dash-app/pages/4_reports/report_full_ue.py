from dash import dcc, html, register_page, callback, Input, Output


register_page(
    __name__,
    path="/reports/full-ue",
    name="Текстовый отчет по юнит-экономике",
    title="Отчеты - Текстовый отчет по юнит-экономике",
    order=150,
)


REPORT_MD_UE = """
# Всесторонний отчет по юнит-экономике

## 1. Охват раздела
Этот раздел проекта посвящен юнит-экономике онлайн-школы программирования X. На этом этапе мы исходим из уже очищенных данных (Deals, Contacts, Calls, Spend в `data/clean`) и отвечаем на вопросы:
- насколько текущая бизнес-модель окупается в среднем по бизнесу и по ключевым продуктам;
- какие метрики юнит-экономики являются точками роста;
- какие изменения в показателях (UA, C1, CPA, AOV, APC) больше всего влияют на маржинальную прибыль;
- какую гипотезу по росту (через улучшение C1) имеет смысл проверять и хватит ли нам трафика для A/B-теста.

Все расчеты юнит-экономики реализованы в модуле `src.analytics_ue`, а визуальная часть вынесена в блок страниц `/product/*`.

---

## 2. Базовые метрики и юнит-экономика (`/product/unit-economics`)

### 2.1 Что считаем
В модуле `src.analytics_ue` мы переходим от сырых полей CRM к набору бизнес-метрик юнит-экономики:
- UA - количество уникальных лидов (контактов), которые вошли в воронку;
- B - количество клиентов (сделки со стадией `payment done`);
- AC - маркетинговый бюджет (общий Spend из таблицы Spend);
- T - количество транзакций (например, месяцев обучения по сделкам);
- Revenue - суммарная выручка, рассчитанная через промежуточную метрику `R_I` для каждой сделки;
- C1 = B / UA - конверсия из лида в клиента;
- CPA = AC / UA - стоимость привлечения потенциального клиента (на одного лида);
- CAC = AC / B - стоимость привлечения клиента;
- AOV - средний чек (выручка на одну транзакцию);
- APC - среднее количество транзакций на клиента;
- CLTV - средняя валовая прибыль на одного клиента;
- LTV - средняя валовая прибыль на «юнит масштабирования» (например, на одного лида);
- CM = UA * (LTV - CPA) - маржинальная прибыль.

Для оценки Revenue используется формула на уровне отдельной сделки:
- сначала считаем «индивидуальный» средний чек AOV_I с учетом первоначальной оплаты и растянутой части (`Offer Total Amount`, `Initial Amount Paid`, `Course duration`, `Months of study`);
- затем выручка по сделке R_I = AOV_I * Months of study;
- общая выручка Revenue - сумма R_I по всем сделкам.

Все эти метрики агрегируются:
- по бизнесу в целом;
- по каждому ключевому продукту (например, `Web Developer`, `Digital Marketing`, `UX/UI Design`).

### 2.2 Как это видно в дашборде
На странице `/product/unit-economics` (файл `unit_economics.py`):
- верхний блок - таблица «Юнит-экономика по бизнесу в целом», где для каждой метрики отображается код (UA, B, AC, …) и человекочитаемое название;
- нижний блок - таблица «Юнит-экономика по продуктам», где те же показатели представлены в разрезе ключевых программ.

Таким образом, этот экран отвечает на вопрос: «В среднем, при текущем трафике и ценах, бизнес окупается или нет, и какие продукты вносят основной вклад в юнит-экономику?».

---

## 3. Точки роста юнит-экономики (`/product/growth-points`)

### 3.1 Логика сценариев роста
В модуле `src.analytics_ue` реализована функция `growth_scenarios_table`, которая строит таблицу сценариев изменения маржинальной прибыли CM при малых изменениях ключевых рычагов:
- UA - количество лидов;
- C1 - конверсия из лида в клиента;
- CPA - стоимость привлечения лида (для нее рассматривается снижение);
- AOV - средний чек;
- APC - среднее число транзакций на клиента.

Для каждого сегмента (бизнес целиком и каждый продукт) моделируются сценарии вида:
- «увеличить UA на +10 %»;
- «повысить C1 до целевого уровня (+10 %)»;
- «снизить CPA на 10 %»;
- «увеличить AOV на 10 %»;
- «увеличить APC на 10 %».

По каждому сценарию пересчитывается новая CM и сравнивается с базовым значением:
- CM_base - исходная маржинальная прибыль;
- CM_new - маржинальная прибыль после изменения одной метрики;
- CM_delta и CM_delta_% - абсолютный и относительный прирост.

### 3.2 Как это показано на странице
На странице `/product/growth-points`:
- первый блок показывает сценарии роста CM для бизнеса в целом (Segment = Business);
- второй блок - сценарии для отдельных продуктов.

Таблицы подсвечивают строки с максимальным приростом CM, чтобы сразу было видно:
- какой рычаг (UA, C1, CPA, AOV, APC) дает наибольший эффект в деньгах;
- по каким продуктам влияние этого рычага особенно сильное.

Таким образом, раздел «Growth Points» переводит язык юнит-экономики в конкретные «точки роста», с которыми можно идти к маркетингу и продукту.

---

## 4. Дерево метрик (`/product/metric-tree`)

### 4.1 Смысл дерева метрик
Отдельный модуль и страница `/product/metric-tree` визуализируют, как высокоуровневые показатели (например, CM или LTV) раскладываются на более простые составляющие:
- CM зависит от LTV и CPA;
- LTV зависит от CLTV и конверсии C1;
- CLTV складывается из AOV и APC;
- AOV и APC «поддерживаются» продуктовой и маркетинговой аналитикой (цены, продуктовый микс, длительность обучения и т.д.).

Идея: вместо того чтобы говорить «нам нужно увеличить CM», мы показываем, через какие конкретные метрики это может быть достигнуто и какие блоки воронки за них отвечают.

### 4.2 Как это выглядит в интерфейсе
На странице дашборда дерево отображается в виде структурированного блока: узлы (CM, LTV, CLTV, AOV, APC, C1, UA, AC, T, Revenue) и связи между ними. В таблицах под деревом можно видеть:
- описание каждой метрики;
- ее роль в общей формуле;
- краткий комментарий, за какой командой/процессом стоит улучшение этой метрики (маркетинг, продажи, продукт).

Этот раздел помогает объяснить юнит-экономику не только аналитикам, но и менеджерам: видно, какие показатели - результат, а какие - инструменты для роста.

---

## 5. Гипотезы и HADI-цикл (`/product/hypotheses`)

### 5.1 HADI-таблица по C1
Модуль `src.analytics_ue` содержит HADI-таблицу `hadi_table`, где разобрана примерная гипотеза по росту конверсии C1 (B / UA):
- H (гипотеза): если сократить SLA (время первого контакта с лидом) до 24 часов, то конверсия C1 вырастет до целевого уровня (10 %);
- A (действия): описаны шаги, как именно менять процесс (автоматические задачи, напоминания, скрипты);
- D (данные): какие именно метрики считаем по группам (C1, SLA, промежуточные конверсии);
- I (интерпретация): когда гипотеза считается подтвержденной и что делать дальше.

На странице `/product/hypotheses` HADI-таблица выводится отдельной таблицей, чтобы можно было обсуждать гипотезу в одном экране с числовой проверкой.

### 5.2 Проверка гипотезы: достаточно ли трафика
Функция `hypothesis_check_info` в `src.analytics_ue` рассчитывает параметры для проверки гипотезы по C1:
- текущая конверсия C1 (p_base) и целевая конверсия (target);
- абсолютный эффект x = target - p_base, который мы хотим заметить;
- требуемый размер выборки n_per_group для A/B-теста (по стандартной формуле для пропорций);
- текущий трафик UA/день и сколько лидов можно набрать за 14 дней (`n_available`);
- сколько дней нужно, чтобы набрать достаточный объем (`days_required`) и укладываемся ли в лимит 14 дней.

На странице `/product/hypotheses` это отображается в виде таблицы:
- по бизнесу в целом;
- по отдельным продуктам.

Дополнительно внизу есть блок с примером расчета: из каких чисел получается требуемый объем выборки, как считается минимально обнаружимый эффект и как это связано с текущим трафиком.

---

## 6. Основные выводы по юнит-экономике

1. **Все расчеты юнит-экономики опираются на очищенные данные.** Весь модуль `src.analytics_ue` использует только таблицы из `data/clean`, которые прошли импорт и очистку. Это позволяет доверять итоговым UE-метрикам.
2. **Юнит-экономика считается как по бизнесу в целом, так и по продуктам.** Мы видим не только «среднюю температуру», но и вклад отдельных программ, что важно для продуктовой стратегии.
3. **Точки роста привязаны к конкретным метрикам.** Сценарии роста CM показывают, за счет каких рычагов (UA, C1, CPA, AOV, APC) можно получить наибольший эффект - и для бизнеса в целом, и для конкретных программ.
4. **Дерево метрик делает модель понятной неаналитикам.** Вместо формул «на бумаге» дерево и подписи объясняют, из чего складывается CM и какие команды могут повлиять на каждую из метрик.
5. **HADI-цикл помогает перейти от аналитики к действиям.** Гипотеза по C1 и расчеты для A/B-теста показывают, как использовать юнит-экономику на практике: что именно тестировать, какой трафик нужен и какие результаты считать успехом.

Этот отчет можно рассматривать как текстовую «легенду» к разделу `/product/*`: он объясняет, какие таблицы и модули стоят за юнит-экономикой, какие метрики считаются и как по ним принимаются решения.
"""


def layout():
    from .sidebar import get_sidebar

    return html.Div(
        style={"display": "flex", "gap": "16px"},
        children=[
            get_sidebar(),
            html.Article(
                [
                    dcc.Markdown(REPORT_MD_UE, id="report-full-ue-md"),
                ],
                className="viz-card",
            ),
        ],
    )


# Placeholders for future English / German versions.
# You can replace these strings later with full Markdown translations.
REPORT_MD_UE_EN = """# Comprehensive unit-economics report

## 1. Section scope
This section of the project is devoted to the unit economics of the online programming school X. At this stage we work with already cleaned data (Deals, Contacts, Calls, Spend in `data/clean`) and answer the following questions:
- to what extent the current business model pays off on average for the whole business and for key products;
- which unit-economics metrics represent growth points;
- which changes in indicators (UA, C1, CPA, AOV, APC) have the strongest impact on contribution margin;
- which growth hypothesis (through improving C1) is worth testing and whether we have enough traffic for an A/B test.

All unit-economics calculations are implemented in the module `src.analytics_ue`, and the visual part is presented in the `/product/*` group of pages.

---

## 2. Base metrics and unit economics (`/product/unit-economics`)

### 2.1 What we calculate
In the `src.analytics_ue` module we move from raw CRM fields to a set of business unit-economics metrics:
- **UA** - number of unique leads (contacts) that entered the funnel;
- **B** - number of customers (deals with stage `payment done`);
- **AC** - marketing budget (total Spend from the Spend table);
- **T** - number of transactions (for example, months of study per deal);
- **Revenue** - total revenue, calculated via an intermediate metric `R_I` for each deal;
- **C1 = B / UA** - conversion from lead to customer;
- **CPA = AC / UA** - cost of acquiring a potential customer (per lead);
- **CAC = AC / B** - cost of acquiring a paying customer;
- **AOV** - average order value (revenue per transaction);
- **APC** - average number of transactions per customer;
- **CLTV** - average gross profit per customer;
- **LTV** - average gross profit per “scaling unit” (for example, per lead);
- **CM = UA * (LTV - CPA)** - contribution margin.

To compute **Revenue**, we use a formula at the individual-deal level:
- first we calculate an “individual” average check `AOV_I` taking into account the initial payment and the stretched part (`Offer Total Amount`, `Initial Amount Paid`, `Course duration`, `Months of study`);
- then for each deal revenue is `R_I = AOV_I × Months of study`;
- total **Revenue** is the sum of `R_I` over all deals.

All these metrics are aggregated:
- for the business as a whole;
- for each key product (for example, `Web Developer`, `Digital Marketing`, `UX/UI Design`).

### 2.2 How this appears on the dashboard
On the `/product/unit-economics` page (file `unit_economics.py`):
- the upper block is the table “Unit economics for the whole business”, where for each metric we show the code (UA, B, AC, …) and a human-readable name;
- the lower block is the table “Unit economics by product”, where the same indicators are broken down by key programmes.

Thus this screen answers the question: “On average, with the current traffic and prices, does the business pay off or not, and which products contribute most to unit economics?”.

---

## 3. Unit-economics growth points (`/product/growth-points`)

### 3.1 Logic of growth scenarios
In the `src.analytics_ue` module the function `growth_scenarios_table` builds a table of scenarios for changes in contribution margin **CM** under small changes of key levers:
- **UA** - number of leads;
- **C1** - conversion from lead to customer;
- **CPA** - cost of acquiring a lead (we consider a decrease here);
- **AOV** - average check;
- **APC** - average number of transactions per customer.

For each segment (whole business and each product) we model scenarios such as:
- “increase UA by +10%”;
- “raise C1 to the target level (+10%)”;
- “decrease CPA by 10%”;
- “increase AOV by 10%”;
- “increase APC by 10%”.

For each scenario a new **CM** is recalculated and compared with the baseline:
- **CM_base** - baseline contribution margin;
- **CM_new** - contribution margin after changing a single metric;
- **CM_delta** and **CM_delta_%** - absolute and relative increase.

### 3.2 How this is shown on the page
On the `/product/growth-points` page:
- the first block shows CM growth scenarios for the business as a whole (Segment = Business);
- the second block shows scenarios for individual products.

The tables highlight the rows with the largest CM increase so that it is immediately visible:
- which lever (UA, C1, CPA, AOV, APC) gives the strongest monetary effect;
- for which products the impact of this lever is especially strong.

Thus the “Growth Points” section translates the language of unit economics into concrete “growth points” that can be taken to marketing and product teams.

---

## 4. Metric tree (`/product/metric-tree`)

### 4.1 Idea of the metric tree
A separate module and the `/product/metric-tree` page visualise how high-level indicators (for example CM or LTV) decompose into simpler components:
- **CM** depends on **LTV** and **CPA**;
- **LTV** depends on **CLTV** and conversion **C1**;
- **CLTV** is built from **AOV** and **APC**;
- **AOV** and **APC** are “supported” by product and marketing analytics (prices, product mix, course duration, etc.).

The idea: instead of saying “we need to increase CM”, we show through which specific metrics this can be achieved and which parts of the funnel are responsible for them.

### 4.2 How it looks in the interface
On the dashboard page the tree is shown as a structured block: nodes (CM, LTV, CLTV, AOV, APC, C1, UA, AC, T, Revenue) and the links between them. In the tables below the tree you can see:
- a description of each metric;
- its role in the overall formula;
- a short comment which team/process is responsible for improving this metric (marketing, sales, product).

This section helps to explain unit economics not only to analysts but also to managers: it becomes clear which indicators are *results* and which are *levers for growth*.

---

## 5. Hypotheses and the HADI cycle (`/product/hypotheses`)

### 5.1 HADI table for C1
The `src.analytics_ue` module contains a HADI table `hadi_table` with a sample hypothesis about increasing conversion **C1** (B / UA):
- **H (Hypothesis)**: if we reduce SLA (time to first contact with a lead) to 24 hours, the conversion C1 will grow to the target level (10%);
- **A (Actions)**: the concrete steps to change the process (automatic tasks, reminders, scripts) are described;
- **D (Data)**: which metrics we calculate by groups (C1, SLA, intermediate conversions);
- **I (Insights)**: when the hypothesis is considered confirmed and what to do next.

On the `/product/hypotheses` page the HADI table is shown as a separate table so that the hypothesis can be discussed on the same screen as its numeric verification.

### 5.2 Hypothesis check: is traffic sufficient?
The function `hypothesis_check_info` in `src.analytics_ue` computes parameters for testing the C1 hypothesis:
- current conversion C1 (`p_base`) and target conversion (`target`);
- absolute effect `x = target - p_base` that we want to detect;
- required sample size `n_per_group` for an A/B test (by the standard formula for proportions);
- current traffic UA per day and how many leads can be gathered in 14 days (`n_available`);
- how many days are needed to gather enough volume (`days_required`) and whether we fit into the 14-day limit.

On the `/product/hypotheses` page this is displayed as a table:
- for the business as a whole;
- for individual products.

At the bottom there is an additional block with an example calculation: which numbers give the required sample size, how the minimum detectable effect is computed and how this relates to the current traffic.

---

## 6. Key conclusions about unit economics

1. **All unit-economics calculations are based on cleaned data.** The entire `src.analytics_ue` module uses only tables from `data/clean` that have passed import and cleaning, which makes the final UE metrics trustworthy.  
2. **Unit economics is calculated both for the whole business and by product.** We see not only the “average temperature” but also the contribution of individual programmes, which is important for product strategy.  
3. **Growth points are tied to specific metrics.** CM growth scenarios show which levers (UA, C1, CPA, AOV, APC) can yield the strongest effect - for the whole business and for specific programmes.  
4. **The metric tree makes the model understandable for non-analysts.** Instead of formulas “on paper”, the tree and captions explain what CM consists of and which teams can influence each metric.  
5. **The HADI cycle helps move from analytics to action.** The C1 hypothesis and A/B-test calculations show how to use unit economics in practice: what exactly to test, how much traffic is needed and which results count as success.

This report can be viewed as a textual “legend” for the `/product/*` section: it explains which tables and modules stand behind unit economics, which metrics are calculated and how they are used for decision-making."""

REPORT_MD_UE_DE = """# Umfassender Bericht zur Unit Economics

## 1. Umfang des Abschnitts
Dieser Projektabschnitt ist der Unit Economics der Online-Programmierschule X gewidmet. In dieser Phase arbeiten wir mit bereits bereinigten Daten (Deals, Contacts, Calls, Spend in `data/clean`) und beantworten folgende Fragen:
- wie gut sich das aktuelle Geschäftsmodell im Durchschnitt für das gesamte Geschäft und für Schlüsselprodukte rechnet;
- welche Unit-Economics-Kennzahlen echte Wachstumspunkte darstellen;
- welche Änderungen in den Kennzahlen (UA, C1, CPA, AOV, APC) den größten Einfluss auf die Deckungsbeitragsmarge haben;
- welche Wachstumshypothese (über die Verbesserung von C1) getestet werden sollte und ob der Traffic für einen A/B-Test ausreicht.

Alle unit-ökonomischen Berechnungen sind im Modul `src.analytics_ue` implementiert, die Visualisierung erfolgt in den Seiten des Blocks `/product/*`.

---

## 2. Basiskennzahlen und Unit Economics (`/product/unit-economics`)

### 2.1 Was wir berechnen
Im Modul `src.analytics_ue` überführen wir rohe CRM-Felder in ein Set von Business-Kennzahlen der Unit Economics:
- **UA** - Anzahl eindeutiger Leads (Kontakte), die in den Funnel eingetreten sind;
- **B** - Anzahl der Kunden (Deals mit Stufe `payment done`);
- **AC** - Marketingbudget (gesamter Spend aus der Spend-Tabelle);
- **T** - Anzahl der Transaktionen (z.B. Unterrichtsmonate pro Deal);
- **Revenue** - Gesamtumsatz, berechnet über eine Zwischenkennzahl `R_I` für jeden Deal;
- **C1 = B / UA** - Konversion vom Lead zum Kunden;
- **CPA = AC / UA** - Kosten pro potentiellen Kunden (pro Lead);
- **CAC = AC / B** - Kosten pro zahlendem Kunden;
- **AOV** - durchschnittlicher Bestellwert (Umsatz pro Transaktion);
- **APC** - durchschnittliche Anzahl Transaktionen pro Kunde;
- **CLTV** - durchschnittlicher Bruttogewinn pro Kunde;
- **LTV** - durchschnittlicher Bruttogewinn pro „Skalierungs-Unit“ (z.B. pro Lead);
- **CM = UA * (LTV - CPA)** - Deckungsbeitrag (Contribution Margin).

Zur Ermittlung von **Revenue** verwenden wir eine Formel auf Ebene einzelner Deals:
- zunächst berechnen wir einen „individuellen“ durchschnittlichen Check `AOV_I` unter Berücksichtigung der Erstzahlung und des gestreckten Teils (`Offer Total Amount`, `Initial Amount Paid`, `Course duration`, `Months of study`);
- anschließend ist der Umsatz pro Deal `R_I = AOV_I × Months of study`;
- der Gesamtumsatz **Revenue** ist die Summe aller `R_I` über alle Deals.

Alle diese Kennzahlen werden aggregiert:
- für das gesamte Geschäft;
- für jedes Schlüsselprodukt (z.B. `Web Developer`, `Digital Marketing`, `UX/UI Design`).

### 2.2 Darstellung im Dashboard
Auf der Seite `/product/unit-economics` (Datei `unit_economics.py`):
- zeigt der obere Block die Tabelle „Unit Economics für das gesamte Geschäft“, in der für jede Kennzahl der Code (UA, B, AC, …) und eine verständliche Bezeichnung angezeigt werden;
- der untere Block ist die Tabelle „Unit Economics nach Produkten“, in der dieselben Kennzahlen nach Schlüsselprogrammen aufgeschlüsselt sind.

Damit beantwortet dieser Screen die Frage: „Rechnet sich das Geschäft im Durchschnitt bei aktuellem Traffic und aktuellen Preisen, und welche Produkte leisten den größten Beitrag zur Unit Economics?“.

---

## 3. Wachstumspunkte der Unit Economics (`/product/growth-points`)

### 3.1 Logik der Wachstumsszenarien
Im Modul `src.analytics_ue` implementiert die Funktion `growth_scenarios_table` eine Tabelle von Szenarien, wie sich die Deckungsbeitragsmarge **CM** bei kleinen Änderungen der wichtigsten Hebel verändert:
- **UA** - Anzahl der Leads;
- **C1** - Konversion Lead → Kunde;
- **CPA** - Kosten pro Lead (hier betrachten wir Senkung);
- **AOV** - durchschnittlicher Check;
- **APC** - durchschnittliche Anzahl Transaktionen pro Kunde.

Für jedes Segment (gesamtes Geschäft und jedes Produkt) werden Szenarien modelliert wie:
- „UA um +10 % erhöhen“;
- „C1 auf Zielniveau (+10 %) steigern“;
- „CPA um 10 % senken“;
- „AOV um 10 % erhöhen“;
- „APC um 10 % erhöhen“.

Für jedes Szenario wird eine neue **CM** berechnet und mit dem Ausgangswert verglichen:
- **CM_base** - ursprünglicher Deckungsbeitrag;
- **CM_new** - Deckungsbeitrag nach Änderung einer Kennzahl;
- **CM_delta** und **CM_delta_%** - absoluter bzw. relativer Zuwachs.

### 3.2 Darstellung auf der Seite
Auf der Seite `/product/growth-points`:
- zeigt der erste Block CM-Wachstumsszenarien für das gesamte Geschäft (Segment = Business);
- der zweite Block zeigt Szenarien für einzelne Produkte.

Die Tabellen heben die Zeilen mit dem höchsten CM-Zuwachs hervor, sodass sofort erkennbar ist:
- welcher Hebel (UA, C1, CPA, AOV, APC) den größten Effekt in Geld bringt;
- bei welchen Produkten dieser Hebel besonders stark wirkt.

Damit übersetzt der Abschnitt „Growth Points“ die Sprache der Unit Economics in konkrete „Wachstumspunkte“, mit denen man zu Marketing und Produkt gehen kann.

---

## 4. Metrikbaum (`/product/metric-tree`)

### 4.1 Bedeutung des Metrikbaums
Ein eigenes Modul und die Seite `/product/metric-tree` visualisieren, wie sich hochrangige Kennzahlen (z.B. CM oder LTV) in einfachere Komponenten zerlegen:
- **CM** hängt von **LTV** und **CPA** ab;
- **LTV** hängt von **CLTV** und der Konversion **C1** ab;
- **CLTV** setzt sich aus **AOV** und **APC** zusammen;
- **AOV** und **APC** werden durch Produkt- und Marketing-Analytik „unterstützt“ (Preise, Produktmix, Kursdauer usw.).

Die Idee: Anstatt nur zu sagen „wir müssen CM erhöhen“, zeigen wir, über welche konkreten Kennzahlen das erreicht werden kann und welche Teile des Funnels dafür verantwortlich sind.

### 4.2 Darstellung im Interface
Auf der Dashboard-Seite wird der Baum als strukturierter Block gezeigt: Knoten (CM, LTV, CLTV, AOV, APC, C1, UA, AC, T, Revenue) und die Verbindungen zwischen ihnen. In den Tabellen unter dem Baum sieht man:
- die Beschreibung jeder Kennzahl;
- ihre Rolle in der Gesamtformel;
- einen kurzen Kommentar, welches Team bzw. welcher Prozess für die Verbesserung dieser Kennzahl zuständig ist (Marketing, Vertrieb, Produkt).

Dieser Abschnitt hilft, Unit Economics nicht nur Analysten, sondern auch Managern zu erklären: es wird sichtbar, welche Kennzahlen *Ergebnis* sind und welche als *Hebel für Wachstum* dienen.

---

## 5. Hypothesen und HADI-Zyklus (`/product/hypotheses`)

### 5.1 HADI-Tabelle für C1
Das Modul `src.analytics_ue` enthält eine HADI-Tabelle `hadi_table` mit einer Beispielhypothese zur Steigerung der Konversion **C1** (B / UA):
- **H (Hypothese)**: Wenn wir die SLA (Zeit bis zum ersten Kontakt mit dem Lead) auf 24 Stunden reduzieren, steigt die Konversion C1 auf das Zielniveau (10 %).
- **A (Actions / Maßnahmen)**: Es werden Schritte beschrieben, wie genau der Prozess geändert wird (automatische Aufgaben, Erinnerungen, Skripte).
- **D (Data / Daten)**: Welche Kennzahlen wir für die Gruppen berechnen (C1, SLA, Zwischenkonversionen).
- **I (Insights / Interpretation)**: Wann die Hypothese als bestätigt gilt und was danach zu tun ist.

Auf der Seite `/product/hypotheses` wird die HADI-Tabelle separat angezeigt, sodass man die Hypothese auf demselben Screen wie ihre numerische Prüfung diskutieren kann.

### 5.2 Hypothesenprüfung: reicht der Traffic aus?
Die Funktion `hypothesis_check_info` in `src.analytics_ue` berechnet die Parameter zur Prüfung der C1-Hypothese:
- aktuelle Konversion C1 (`p_base`) und Zielkonversion (`target`);
- absoluter Effekt `x = target - p_base`, den wir nachweisen möchten;
- erforderliche Stichprobengröße `n_per_group` für den A/B-Test (nach Standardformel für Anteile);
- aktueller Traffic UA pro Tag und wie viele Leads in 14 Tagen gesammelt werden können (`n_available`);
- wie viele Tage benötigt werden, um genügend Volumen zu bekommen (`days_required`) und ob wir in das 14-Tage-Limit passen.

Auf der Seite `/product/hypotheses` wird dies in Tabellenform dargestellt:
- für das Geschäft insgesamt;
- für einzelne Produkte.

Zusätzlich gibt es unten einen Block mit einem Rechenbeispiel: aus welchen Zahlen sich die erforderliche Stichprobengröße ergibt, wie der minimal nachweisbare Effekt berechnet wird und wie dies mit dem aktuellen Traffic zusammenhängt.

---

## 6. Zentrale Schlussfolgerungen zur Unit Economics

1. **Alle Unit-Economics-Berechnungen basieren auf bereinigten Daten.** Das gesamte Modul `src.analytics_ue` nutzt nur Tabellen aus `data/clean`, die Import und Cleaning durchlaufen haben. Dadurch werden die finalen UE-Kennzahlen vertrauenswürdig.  
2. **Unit Economics wird sowohl für das Gesamtgeschäft als auch für Produkte berechnet.** Wir sehen nicht nur den „Durchschnittswert“, sondern auch den Beitrag einzelner Programme, was für die Produktstrategie wichtig ist.  
3. **Wachstumspunkte sind an konkrete Kennzahlen gebunden.** Die CM-Wachstumsszenarien zeigen, über welche Hebel (UA, C1, CPA, AOV, APC) der größte Effekt erzielt werden kann - sowohl für das Gesamtgeschäft als auch für einzelne Programme.  
4. **Der Metrikbaum macht das Modell für Nicht-Analysten verständlich.** Statt Formeln „auf Papier“ erklären Baum und Beschriftungen, woraus sich CM zusammensetzt und welche Teams jede Kennzahl beeinflussen können.  
5. **Der HADI-Zyklus hilft, von Analyse zu Handeln zu kommen.** Die C1-Hypothese und die A/B-Test-Berechnungen zeigen, wie man Unit Economics praktisch nutzt: was genau getestet werden soll, wie viel Traffic nötig ist und welche Ergebnisse als Erfolg gelten.

Dieser Bericht kann als textliche „Legende“ zum Bereich `/product/*` betrachtet werden: er erklärt, welche Tabellen und Module hinter der Unit Economics stehen, welche Kennzahlen berechnet werden und wie auf ihrer Basis Entscheidungen getroffen werden."""


@callback(Output("report-full-ue-md", "children"), Input("app-lang", "data"))
def _update_report_full_ue_md(lang_value: str | None):
    lang = (lang_value or "ru").lower()

    if lang == "en":
        return REPORT_MD_UE_EN
    if lang == "de":
        return REPORT_MD_UE_DE

    # Default: Russian original
    return REPORT_MD_UE
