import pandas as pd
import sqlalchemy
import json

# ============================================================
# 1. MySQL Connection, get data
# ============================================================

engine = sqlalchemy.create_engine(
    'mysql+mysqlconnector://root:PW@localhost/ecommerce'
)

# KPI Table
funnel_overall = pd.read_sql('SELECT * FROM funnel_overall', engine)
funnel_channel = pd.read_sql('SELECT * FROM funnel_chaannel', engine)

# Monthly Revenue
transactions = pd.read_sql('SELECT * FROM transactions', engine)
monthly = pd.read_sql('SELECT * FROM monthly_revenue', engine)

# Bounce Rate
bounce = pd.read_sql('SELECT * FROM bounce_by_channel', engine)

# Revenue by channel
revenue = pd.read_sql('SELECT * FROM revenue_by_channel', engine)

# ============================================================
# 2. Prepare data as JSON（into HTML）
# ============================================================

kpi_data = {
    'view_users': int(funnel_overall['view_users'].iloc[0]),
    'cart_users': int(funnel_overall['cart_users'].iloc[0]),
    'purchase_users': int(funnel_overall['purchase_users'].iloc[0]),
}

funnel_table = funnel_channel.copy()
funnel_table['cart_conversion_rate'] = (funnel_table['cart_conversion_rate'] * 100).round(2)
funnel_table['purchase_conversion_rate'] = (funnel_table['purchase_conversion_rate'] * 100).round(2)
funnel_table['cart_abandonment_rate'] = (100 - funnel_table['purchase_conversion_rate']).round(2)
funnel_table_json = funnel_table.to_dict(orient='records')

monthly_json = {
    'months': monthly['month'].tolist(),
    'revenue': monthly['total_revenue'].tolist()
}

channels = funnel_channel['channel'].tolist()
cart_abandon = (funnel_channel['purchase_conversion_rate'].apply(lambda x: round((1 - x) * 100, 1))).tolist()
bounce_rates = []
bounce_channels = []
for ch in channels:
    row = bounce[bounce['channel'] == ch]
    if not row.empty:
        bounce_rates.append(float(row['bounce_rate'].values[0]))
        bounce_channels.append(ch)

rev_data = revenue.set_index('channel')['total_revenue'].to_dict()
rev_by_channel = [float(rev_data.get(ch, 0)) for ch in channels]

funnel_events = pd.read_sql('SELECT * FROM events', engine)
funnel_data = {
    'view': int(funnel_events[funnel_events['event_type'] == 'view']['user_id'].nunique()),
    'cart': int(funnel_events[funnel_events['event_type'] == 'cart']['user_id'].nunique()),
    'purchase': int(funnel_events[funnel_events['event_type'] == 'purchase']['user_id'].nunique()),
}

# ============================================================
# 3. GEnerate HTML
# ============================================================

# Generate Slicer
slicer_buttons = '\n  '.join([
    f'<button class="slicer-btn" onclick="filterChannel(\'{ch}\', this)">{ch}</button>'
    for ch in channels
])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --accent: #f0a500;
    --accent2: #e06c2b;
    --text: #e8eaf0;
    --text-muted: #7b8194;
    --border: #2e3348;
    --green: #4ade80;
    --red: #f87171;
    --radius: 12px;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px;
  }}

  /* TITLE */
  .title-bar {{
    text-align: center;
    padding: 20px 0 28px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
  }}
  .title-bar h1 {{
    font-size: 22px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--text);
  }}
  .title-bar h1 span {{ color: var(--accent); }}

  /* KPI ROW */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px 28px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
  }}
  .kpi-label {{
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }}
  .kpi-value {{
    font-size: 40px;
    font-weight: 700;
    color: var(--accent);
    font-family: 'DM Mono', monospace;
  }}

  /* MIDDLE ROW */
  .middle-row {{
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    gap: 16px;
    margin-bottom: 24px;
  }}

  /* CARD */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
  }}
  .card-title {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 16px;
  }}

  /* TABLE */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  thead th {{
    text-align: left;
    padding: 8px 10px;
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border);
  }}
  tbody tr {{
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }}
  tbody tr:hover {{ background: var(--surface2); }}
  tbody td {{
    padding: 10px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
  }}
  tbody td:first-child {{
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    color: var(--text);
  }}
  .cvr-good {{ color: var(--green); }}
  .cvr-bad {{ color: var(--red); }}

  /* SLICER */
  .slicer-row {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .slicer-label {{
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-right: 4px;
  }}
  .slicer-btn {{
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .slicer-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
  .slicer-btn.active {{
    background: var(--accent);
    border-color: var(--accent);
    color: #000;
    font-weight: 600;
  }}

  /* BOTTOM ROW */
  .bottom-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }}
  .chart-container {{
    position: relative;
    height: 220px;
  }}

  /* FUNNEL VISUAL */
  .funnel-visual {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 8px 0;
  }}
  .funnel-step {{
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    transition: all 0.3s;
  }}
  .funnel-bar {{
    height: 44px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    color: #000;
    transition: width 0.5s ease;
    font-family: 'DM Mono', monospace;
  }}
  .funnel-meta {{
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 3px;
    margin-bottom: 4px;
  }}
  .funnel-arrow {{
    color: var(--text-muted);
    font-size: 14px;
    margin: 2px 0;
  }}
</style>
</head>
<body>

<!-- TITLE -->
<div class="title-bar">
  <h1>Web Analytics – <span>Checkout Process Dashboard</span></h1>
</div>

<!-- KPI ROW (static, no filter) -->
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">User Product View in Total</div>
    <div class="kpi-value">{kpi_data['view_users']:,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">User Product Add in Total</div>
    <div class="kpi-value">{kpi_data['cart_users']:,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">User Product Buy in Total</div>
    <div class="kpi-value">{kpi_data['purchase_users']:,}</div>
  </div>
</div>

<!-- MIDDLE ROW -->
<div class="middle-row">
  <!-- Funnel Table -->
  <div class="card">
    <div class="card-title">Funnel by Channel</div>
    <table>
      <thead>
        <tr>
          <th>Channel</th>
          <th>Views</th>
          <th>Cart</th>
          <th>Purchase</th>
          <th>Cart CVR</th>
          <th>Purchase CVR</th>
        </tr>
      </thead>
      <tbody>
        {''.join([f"""
        <tr>
          <td>{r['channel']}</td>
          <td>{int(r['view_users'])}</td>
          <td>{int(r['cart_users'])}</td>
          <td>{int(r['purchase_users'])}</td>
          <td class="cvr-good">{r['cart_conversion_rate']}%</td>
          <td class="{'cvr-good' if r['purchase_conversion_rate'] > 50 else 'cvr-bad'}">{r['purchase_conversion_rate']}%</td>
        </tr>""" for r in funnel_table_json])}
      </tbody>
    </table>
  </div>

  <!-- Monthly Revenue -->
  <div class="card">
    <div class="card-title">Monthly Revenue Trend</div>
    <div class="chart-container">
      <canvas id="monthlyChart"></canvas>
    </div>
  </div>
</div>

<!-- SLICER -->
<div class="slicer-row">
  <span class="slicer-label">Channel</span>
  <button class="slicer-btn active" onclick="filterChannel('all', this)">All</button>
  {slicer_buttons}
</div>

<!-- BOTTOM ROW -->
<div class="bottom-row">
  <!-- Funnel -->
  <div class="card">
    <div class="card-title">Funnel</div>
    <div class="funnel-visual" id="funnelViz"></div>
  </div>

  <!-- Cart Abandonment -->
  <div class="card">
    <div class="card-title">Cart Abandonment Rate</div>
    <div class="chart-container">
      <canvas id="abandonChart"></canvas>
    </div>
  </div>

  <!-- Bounce Rate -->
  <div class="card">
    <div class="card-title">Bounce Rate by Channel</div>
    <div class="chart-container">
      <canvas id="bounceChart"></canvas>
    </div>
  </div>

  <!-- Revenue by Channel -->
  <div class="card">
    <div class="card-title">Total Revenue by Channel</div>
    <div class="chart-container">
      <canvas id="revenueChart"></canvas>
    </div>
  </div>
</div>

<script>
// ── Data ──────────────────────────────────────────────
Chart.register(ChartDataLabels);
const allChannels = {json.dumps(channels)};
const allCartAbandon = {json.dumps(cart_abandon)};
const allBounceRates = {json.dumps(bounce_rates)};
const allRevenue = {json.dumps(rev_by_channel)};
const funnelData = {json.dumps(funnel_data)};
const funnelTableData = {json.dumps(funnel_table_json)};
const monthlyData = {json.dumps(monthly_json)};

const ACCENT = '#f0a500';
const ACCENT2 = '#e06c2b';
const SURFACE2 = '#22263a';
const MUTED = '#7b8194';
const GREEN = '#4ade80';
const RED = '#f87171';

const chartDefaults = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{ legend: {{ display: false }} }},
  scales: {{
    x: {{ ticks: {{ color: MUTED, font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }},
    y: {{ ticks: {{ color: MUTED, font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
  }}
}};

// ── Monthly Chart (static) ────────────────────────────
const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
new Chart(monthlyCtx, {{
  type: 'line',
  data: {{
    labels: monthlyData.months,
    datasets: [{{ data: monthlyData.revenue, borderColor: ACCENT, backgroundColor: 'rgba(240,165,0,0.08)',
      tension: 0.4, pointBackgroundColor: ACCENT, pointRadius: 4, fill: true }}]
  }},
  options: {{ ...chartDefaults }}
}});

// ── Funnel Visualization ──────────────────────────────
function renderFunnel(viewN, cartN, purchaseN) {{
  const max = viewN;
  const steps = [
    {{ label: 'View', value: viewN, pct: 100, color: ACCENT }},
    {{ label: 'Cart', value: cartN, pct: Math.round(cartN/max*100), color: ACCENT2 }},
    {{ label: 'Purchase', value: purchaseN, pct: Math.round(purchaseN/max*100), color: GREEN }},
  ];
  const container = document.getElementById('funnelViz');
  container.innerHTML = steps.map((s, i) => `
    <div class="funnel-step">
      <div class="funnel-bar" style="width:${{s.pct}}%;background:${{s.color}}">
        ${{s.value.toLocaleString()}}
      </div>
      <div class="funnel-meta">${{s.label}} · ${{s.pct}}%</div>
      ${{i < steps.length - 1 ? '<div class="funnel-arrow">▼</div>' : ''}}
    </div>
  `).join('');
}}
renderFunnel(funnelData.view, funnelData.cart, funnelData.purchase);

// ── Bottom Charts ─────────────────────────────────────
let abandonChart, bounceChart, revenueChart;

function makeBar(id, labels, data, colors) {{
  const ctx = document.getElementById(id).getContext('2d');
  const isPct = id !== 'revenueChart';
  return new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data, backgroundColor: colors || ACCENT,
      borderRadius: 4,
      datalabels: {{
        display: true,
        color: '#e8eaf0',
        font: {{ size: 10, weight: '600' }},
        formatter: val => isPct ? val.toFixed(1) + '%' : val.toLocaleString()
      }}
    }}] }},
    options: {{ 
      ...chartDefaults, 
      plugins: {{ 
        ...chartDefaults.plugins,
        tooltip: {{ callbacks: {{ label: ctx => ctx.parsed.y.toFixed(1) + (isPct ? '%' : '') }} }},
        datalabels: {{ anchor: 'end', align: 'top' }}
      }} 
    }}
  }});
}}

function renderBottomCharts(channels, abandon, bounce, revenue) {{
  if (abandonChart) abandonChart.destroy();
  if (bounceChart) bounceChart.destroy();
  if (revenueChart) revenueChart.destroy();

  abandonChart = makeBar('abandonChart', channels, abandon,
    abandon.map(v => v > 55 ? RED : ACCENT));
  bounceChart = makeBar('bounceChart', channels, bounce,
    bounce.map(v => v > 30 ? RED : ACCENT));
  revenueChart = makeBar('revenueChart', channels, revenue, ACCENT);
}}

renderBottomCharts(allChannels, allCartAbandon, allBounceRates, allRevenue);

// ── Filter ────────────────────────────────────────────
function filterChannel(channel, btn) {{
  document.querySelectorAll('.slicer-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  let chans, abandon, bounce, revenue, view, cart, purchase;

  if (channel === 'all') {{
    chans = allChannels;
    abandon = allCartAbandon;
    bounce = allBounceRates;
    revenue = allRevenue;
    view = funnelData.view;
    cart = funnelData.cart;
    purchase = funnelData.purchase;
  }} else {{
    const idx = allChannels.indexOf(channel);
    chans = [channel];
    abandon = [allCartAbandon[idx]];
    bounce = [allBounceRates[idx]];
    revenue = [allRevenue[idx]];

    const row = funnelTableData.find(r => r.channel === channel);
    view = row ? row.view_users : 0;
    cart = row ? row.cart_users : 0;
    purchase = row ? row.purchase_users : 0;
  }}

  renderFunnel(view, cart, purchase);
  renderBottomCharts(chans, abandon, bounce, revenue);
}}
</script>
</body>
</html>"""

with open('ecommerce_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ Dashboard saved as ecommerce_dashboard.html')
