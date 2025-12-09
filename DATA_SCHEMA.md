# DATA_SCHEMA - Паспорт данных CRM проекта

Документ фиксирует **исходную схему 4 таблиц CRM** (Contacts, Calls, Spend, Deals) и правила работы с ними в нашем пайплайне (шаг 1–2). Файлы поступают в `data/raw`, промежуточные артефакты храним в `data/temp`, очищенные витрины - в `data/clean` (`*.parquet`). Все функции чтения/записи централизованы в `src/io.py`, поэтому любые изменения схемы нужно отражать здесь.

## Каталоги и форматы
- `data/raw` - выгрузки CRM в `.xlsx`/`.csv`. Кодировка `utf-8` либо `cp1251`, разделители `,`, `;` или `\t`.
- `data/temp` - вспомогательные таблицы (например, `city_coords.parquet` после геокодирования).
- `data/clean` - единый источник правды для Dash (`*.parquet`, `pyarrow`).
- Даты приводим к `datetime64[ns]` (время) или `date` (без времени). Целочисленные значения - `Int64` (nullable), суммы - `float64`, категориальные поля - `string`. Булевы поля (`Scheduled in CRM`, производные флаги) - pandas `boolean`.

---

## Contacts (`data/raw/Contacts.xlsx --> data/clean/Contacts.parquet`)
**Ключ:** `Id`

| Колонка             | Тип       | Обяз. | Описание                                                      |
|---------------------|-----------|-------|---------------------------------------------------------------|
| `Id`                | string    | да    | Глобальный идентификатор контакта                             |
| `Contact Owner Name`| string    | да    | Ответственный менеджер                                        |
| `Created Time`      | datetime  | да    | Время создания записи в CRM                                   |
| `Modified Time`     | datetime  | да    | Последнее обновление контакта                                 |
| `City`              | string    | нет   | Указанный город                                               |
| `Level of Deutsch`  | string    | нет   | Уровень владения немецким                                     |
| `Page`              | string    | нет   | Лендинг/форма, с которых пришёл лид                           |

> Все остальные поля (почта, телефон) при наличии обрабатываются в `src/cleaning.py`, но в витринах Dash не используются и могут отсутствовать.

---

## Calls (`data/raw/Calls.xlsx --> data/clean/Calls.parquet`)
**Ключ:** `Id`, внешний ключ `CONTACTID --> Contacts.Id`

| Колонка                     | Тип      | Обяз. | Описание                                                                |
|-----------------------------|----------|-------|-------------------------------------------------------------------------|
| `Id`                        | string   | да    | Идентификатор звонка                                                    |
| `CONTACTID`                 | string   | да    | Ссылка на контакт (`Contacts.Id`)                                       |
| `Call Start Time`           | datetime | да    | Дата и время начала звонка                                              |
| `Call Owner Name`           | string   | да    | Оператор/менеджер                                                       |
| `Call Type`                 | string   | нет   | inbound / outbound / missed                                             |
| `Call Status`               | string   | нет   | статус завершения (answered, voicemail, …)                              |
| `Outgoing Call Status`      | string   | нет   | деталь исходящего звонка (Dialled, Overdue и т.д.)                      |
| `Scheduled in CRM`          | boolean  | нет   | Флаг запланированного звонка (0/1 --> bool)                             |
| `Call Duration (in seconds)`| Int64    | да    | Длительность разговора                                                  |
| `Dialled Number`            | string   | нет   | Набранный номер                                                         |
| `Tag`                       | string   | нет   | Тег звонка                                                              |

---

## Spend (`data/raw/Spend.csv --> data/clean/Spend.parquet`)
**Ключ:** комбинация (`Date`, `Campaign`, `AdGroup`, `Source`), связка `Campaign` ↔ `Deals.Campaign`

| Колонка      | Тип    | Обяз. | Описание                                                |
|--------------|--------|-------|---------------------------------------------------------|
| `Date`       | date   | да    | Дата показа                                             |
| `Source`     | string | да    | Канал (Facebook, Google, VK и т.д.)                     |
| `Campaign`   | string | да    | Название кампании (может содержать `NA`/пустые значения)|
| `AdGroup`    | string | да    | Группа объявлений                                       |
| `Ad`         | string | нет   | Название креатива                                       |
| `Impressions`| Int64  | да    | Показов                                                 |
| `Clicks`     | Int64  | да    | Клика                                                   |
| `Spend`      | float64| да    | Бюджет за день (валюта CRM)                             |

---

## Deals (`data/raw/Deals.xlsx --> data/clean/Deals.parquet`)
**Ключ:** `Id`, внешние ссылки `Contact Name ↔ Contacts.Id` (по необходимости) и `Campaign ↔ Spend.Campaign`

| Колонка               | Тип      | Обяз. | Описание                                                                 |
|-----------------------|----------|-------|--------------------------------------------------------------------------|
| `Id`                  | string   | да    | Идентификатор сделки                                                     |
| `Deal Owner Name`     | string   | да    | Менеджер                                                                 |
| `Created Time`        | datetime | да    | Создание сделки                                                          |
| `Closing Date`        | date     | да    | Запланированное/фактическое закрытие                                     |
| `Stage`               | string   | да    | Статус воронки (ключевое значение `payment done`)                        |
| `Quality`             | string   | нет   | Качество лида по CRM                                                     |
| `SLA`                 | float64  | да    | Время реакции (часы)                                                     |
| `Payment Type`        | string   | да    | Единовременный/рассрочка/другое                                          |
| `Initial Amount Paid` | float64  | да    | Факт первой оплаты (0/1/пусто --> числовое значение)                     |
| `Offer Total Amount`  | float64  | да    | Договорная стоимость                                                     |
| `Product`             | string   | да    | Программа / тариф                                                        |
| `Education Type`      | string   | да    | Формат обучения                                                          |
| `Source`              | string   | да    | Маркетинговый источник                                                   |
| `Campaign`            | string   | да    | Название кампании                                                        |
| `Content (Ad)`        | string   | нет   | Креатив                                                                  |
| `Term (AdGroup)`      | string   | да    | Группа объявлений                                                        |
| `Contact Name`        | string   | нет   | Связанный контакт (текстовое имя)                                        |
| `City`                | string   | да    | Город из CRM                                                             |
| `Level of Deutsch`    | string   | да    | Уровень языка                                                            |
| `Course duration`     | Int64    | да    | Плановая длительность курса (дни/недели)                                 |
| `Months of study`     | Int64    | да    | Прошедшие месяцы обучения                                                |
| `Page`                | string   | нет   | Входная страница                                                         |
| `Lost Reason`         | string   | да    | Причина потери                                                           |

---

## Связи и производные поля
- `CONTACTID --> Contacts.Id` (в `src/analytics_sales.py` и `src/analytics_timeseries.py` используется для джойна звонков и сделок).
- `Campaign`/`Source` в Deals ↔ Spend (см. `src/analytics_campaigns.py`).
- Флаги `is_paid`, `revenue_value`, `deal_lifetime_days`, `lead_to_first_call_sla_hours` рассчитываются в `src/cleaning.py` и доступны всем аналитикам.
- Таблица координат городов (`data/temp/city_coords.parquet`) создаётся из Deals.City + `geopy` (для страниц `/viz/geo`).

---

## Контроль качества
1. **Импорт** (`src/simple_import.py`) проверяет наличие файлов, количество строк/столбцов, типы данных и долю пропусков. Результат фиксируется в `reports/import_checklist.{json,md}` и отображается на странице `/data/import`.
2. **Очистка** (`src/cleaning.py`) нормализует типы, обрезает пробелы, приводит категориальные значения к справочникам, логирует заметки в `reports/step2_eda_summary.{json,md}` (страница `/data/cleaning`).
3. **EDA / Dash** используют только таблицы `data/clean/*.parquet`, поэтому любое изменение схемы должно сопровождаться обновлением этого паспорта и перенастройкой виджетов (`dash-app/pages/...`).

> Любые отклонения от схемы (новые/удалённые столбцы, нестандартные типы) документируем здесь, чтобы не ломать Dash.
