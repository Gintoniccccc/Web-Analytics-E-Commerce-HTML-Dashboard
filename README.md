# Web Analytics – E-Commerce Dashboard (Python + MySQL)

## Project Overview

This project analyzes e-commerce user behavior using a fully automated Python pipeline. Raw data is stored and aggregated in MySQL, processed with Pandas, and rendered as an interactive HTML dashboard using Chart.js — no BI tool required.

This project demonstrates an alternative to Power BI for teams that prefer code-based, lightweight, and freely deployable reporting solutions.

## Tech Stack

| Layer | Tool |
|---|---|
| Data Storage | MySQL |
| Data Aggregation | SQL Views |
| Data Processing | Python, Pandas |
| Visualization | Chart.js (HTML/JS) |
| Dashboard Output | Standalone HTML file |

## Dataset

Simulated e-commerce dataset covering the full year of 2023:

| Table | Rows | Description |
|---|---|---|
| users | 2,000 | User profiles, acquisition channel, device, country |
| sessions | 8,800 | Web sessions with page views, duration, bounce status |
| events | 25,177 | User behavior events (view / cart / purchase) |
| transactions | 1,429 | Completed purchases with revenue data |

## Architecture

```
MySQL Database
    ├── Raw Tables: users, sessions, events, transactions
    └── Aggregated Views:
        ├── funnel_overall        → Overall funnel KPIs
        ├── funnel_chaannel       → Funnel metrics by channel
        ├── monthly_revenue       → Revenue trend by month
        ├── bounce_by_channel     → Bounce rate per channel
        └── revenue_by_channel    → Total revenue per channel
            ↓
Python (dashboard_generator.py)
    ├── Connects to MySQL via SQLAlchemy
    ├── Reads Views directly (no Pandas aggregation)
    └── Renders HTML dashboard
            ↓
ecommerce_dashboard.html
    └── Standalone interactive dashboard (Chart.js)
```

## Dashboard Features

- **3 Static KPI Cards** — Total view / cart / purchase users (not affected by channel filter)
- **Funnel Table** — Per-channel breakdown of view, cart, purchase users and conversion rates
- **Monthly Revenue Trend** — Line chart across all 12 months
- **Channel Slicer** — Filters all bottom charts dynamically
- **Conversion Funnel** — Visual funnel that updates on channel selection
- **Cart Abandonment Rate** — By channel, color-coded by severity
- **Bounce Rate** — By channel
- **Total Revenue** — By channel

## Dashboard Preview

![Dashboard](Dashboard.png)

## Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ecommerce-analytics-python.git
cd ecommerce-analytics-python
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install pandas sqlalchemy mysql-connector-python
```

### 3. Set up MySQL

- Create a database called `ecommerce`
- Import the CSV files from the `data/` folder
- Run `sql/views.sql` to create all required Views

### 4. Configure your MySQL credentials

In `dashboard_generator.py`, update this line:

```python
engine = sqlalchemy.create_engine(
    'mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/ecommerce'
)
```

### 5. Run the dashboard generator

```bash
python dashboard_generator.py
```

Open `ecommerce_dashboard.html` in your browser.

## Key Findings

1. **Direct channel has the highest purchase conversion rate (67%)** — Users who navigate directly show the strongest purchase intent
2. **Social Media has the highest cart abandonment rate (64%)** — High add-to-cart rate but low purchase follow-through suggests impulse browsing
3. **December drives peak revenue** — Seasonal demand spike, likely holiday shopping
4. **Cart abandonment is the biggest drop-off point** — ~47% overall abandonment rate suggests cart recovery strategies (e.g. reminder emails) could significantly increase revenue

## Project Structure

```
├── data/
│   ├── users.csv
│   ├── sessions.csv
│   ├── events.csv
│   └── transactions.csv
├── sql/
│   └── views.sql
├── dashboard_generator.py
├── ecommerce_dashboard.html
└── README.md
```

## Related Project

For a Power BI version of this analysis, see:
[Web Analytics – Power BI Dashboard](https://github.com/yourusername/ecommerce-web-analytics)
