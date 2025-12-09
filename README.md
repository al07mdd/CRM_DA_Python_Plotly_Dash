# CRM Analytics Dashboard

## Overview
This repository contains the full Python DA pipeline and Dash application that we built for an online programming school.  The goal is to clean CRM exports (Contacts, Calls, Deals, Spend), build analytical tables, and publish interactive dashboards for marketing, sales, product teams, and final presentations.

## Data & Privacy
- Raw data (`data/raw/`), intermediate artifacts (`data/temp/`), and cleaned parquet tables (`data/clean/`) are ignored by git. Place the four CRM exports in `data/raw/` before running any scripts.
- Generated notebooks, notes, and reports may include client details; they remain local and are also ignored by git.

## Tech Stack
- Python 3.10+
- Dash 3, Plotly 6, pandas 2, numpy 2
- pyarrow/openpyxl for parquet and Excel I/O
- Custom ETL in `src/`, dashboards in `dash-app/`

## Project Structure
```
├── dash-app/                # Dash UI (app.py, assets, pages/*)
├── src/                     # ETL + analytics modules
├── data/                    # raw/temp/clean (gitignored)
├── reports/                 # import & cleaning reports (gitignored)
├── notes/, notebooks/       # internal documentation (gitignored)
├── requirements.txt
├── DATA_SCHEMA.md           # data passport
├── notes/data_flow.txt      # pipeline cheat sheet
└── notes/Dash_App_Schema.txt# Dash architecture
```

## Running the pipeline
1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Place CRM exports** in `data/raw/Contacts (Done).xlsx`, `Calls_(Done).xlsx`, `Deals (Done).xlsx`, `Spend (Done).xlsx`.
3. **Generate import report**
   ```bash
   python -m src.simple_import
   ```
4. **Run cleaning**
   ```bash
   python -m src.cleaning
   ```
   This fills `data/clean/*.parquet` and updates `reports/step2_eda_summary.*`.

## Running the Dash app
```bash
python dash-app/app.py
```
Visit `http://127.0.0.1:8050/`. The home page provides quick navigation to:
- `/data/*` - import validation, cleaning notes, descriptive stats
- `/viz/*`  - time series, campaigns, sales, payments, geo
- `/product/*` - unit economics, growth points, metric tree, hypotheses
- `/reports/*` - final decks and project summary

Pages call helper functions from `src/analytics_*.py`, so the ETL steps must be executed beforehand.

## Development Notes
- `src/io.py` is the single entry point for reading/writing raw and clean data. Do not bypass it.
- We rely on parabquet files; CSV support remains for ad-hoc exports but is not used by Dash.
- All notebooks in `notebooks/` mirror the Python modules for reproducibility.

---

# Дашборд аналитики CRM

## Краткое описание
Это полный пайплайн Python DA и приложение Dash для онлайн-школы программирования. Мы очищаем CRM-выгрузки (Contacts, Calls, Deals, Spend), строим аналитические витрины и публикуем интерактивные дашборды для маркетинга, продаж, продуктовой команды и финального отчета.

## Данные и приватность
- Папки `data/raw`, `data/temp`, `data/clean` не коммитятся. Перед запуском положите четыре исходных файла в `data/raw/`.
- Ноутбуки, заметки и отчеты могут содержать клиентскую информацию и также исключены из git.

## Технологии
- Python 3.10+
- Dash 3, Plotly 6, pandas 2, numpy 2
- pyarrow и openpyxl для чтения Parquet/XLSX
- Собственные ETL-скрипты в `src/`, интерфейс в `dash-app/`

## Структура проекта
```
├── dash-app/                # приложение Dash (app.py, assets, pages/*)
├── src/                     # ETL и аналитические модули
├── data/                    # данные (игнорируются)
├── reports/                 # отчеты импорта/очистки (игнорируются)
├── notes/, notebooks/       # внутренняя документация (игнорируется)
├── requirements.txt
├── DATA_SCHEMA.md           # паспорт данных
├── notes/data_flow.txt      # схема пайплайна
└── notes/Dash_App_Schema.txt# архитектура Dash
```

## Запуск пайплайна
1. **Установите зависимости**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Положите CRM-файлы** в `data/raw/Contacts (Done).xlsx`, `Calls_(Done).xlsx`, `Deals (Done).xlsx`, `Spend (Done).xlsx`.
3. **Сформируйте отчет импорта**
   ```bash
   python -m src.simple_import
   ```
4. **Запустите очистку**
   ```bash
   python -m src.cleaning
   ```
   В результате появятся `data/clean/*.parquet` и свежий `reports/step2_eda_summary.*`.

## Запуск дашборда
```bash
python dash-app/app.py
```
Откройте `http://127.0.0.1:8050/`. Домашняя страница ведет к разделам:
- `/data/*` - проверка импорта, лог очистки, описательная статистика;
- `/viz/*`  - временные ряды, кампании, продажи, платежи, гео;
- `/product/*` - unit economics, growth points, metric tree, hypotheses;
- `/reports/*` - финальные презентации.

Все страницы используют функции `src/analytics_*.py`, поэтому перед запуском UI нужно прогнать ETL.

## Примечания разработчика
- `src/io.py` - единственная точка доступа к данным. Не обходите ее.
- Основной формат хранения - Parquet; CSV пригоден только для экспорта.
- Ноутбуки в каталоге `notebooks/` повторяют логику Python-скриптов для воспроизводимости.
