#!/usr/bin/env python3
"""
KAI Quant - 生成交互式HTML量化分析仪表盘
读取 stocks_data.json → 嵌入到自包含HTML中
"""
import json, os

OUT = r"E:\BA_learn\task\task1"

# 读取数据
with open(os.path.join(OUT, "data", "stocks_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

# 将数据嵌入HTML
data_json = json.dumps(data, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KAI Quant - 芯片股量化分析仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
:root {{
  --bg-primary: #f0f2f5; --bg-card: #ffffff; --bg-header: #1a1a2e;
  --text-primary: #1a1a2e; --text-secondary: #6c757d; --text-on-dark: #ffffff;
  --color-1: #e63946; --color-2: #457b9d; --color-3: #2a9d8f; --color-4: #e9c46a;
  --color-5: #f4a261; --color-6: #264653; --color-7: #6a4c93;
  --positive: #e63946; --negative: #2a9d8f; --neutral: #6c757d;
  --gap: 16px; --radius: 10px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',sans-serif; background:var(--bg-primary); color:var(--text-primary); line-height:1.6; }}
.container {{ max-width:1400px; margin:0 auto; padding:var(--gap); }}
.header {{ background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); color:var(--text-on-dark); padding:24px 28px; border-radius:var(--radius); margin-bottom:var(--gap); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; box-shadow:0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size:22px; font-weight:700; letter-spacing:0.5px; }}
.header .subtitle {{ font-size:13px; opacity:0.7; margin-top:4px; }}
.header .live-badge {{ background:var(--positive); color:#fff; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:6px; }}
.header .live-badge::before {{ content:''; width:8px; height:8px; background:#fff; border-radius:50%; animation:pulse 2s infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.3;}} }}
.filters {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-top:12px; }}
.filter-group {{ display:flex; align-items:center; gap:6px; }}
.filter-group label {{ font-size:12px; color:rgba(255,255,255,0.6); }}
.filter-group select, .filter-group input {{ padding:6px 12px; border:1px solid rgba(255,255,255,0.2); border-radius:6px; background:rgba(255,255,255,0.1); color:#fff; font-size:13px; cursor:pointer; }}
.filter-group select option {{ background:var(--bg-header); }}
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:var(--gap); margin-bottom:var(--gap); }}
.kpi-card {{ background:var(--bg-card); border-radius:var(--radius); padding:18px 20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border-left:4px solid var(--color-1); transition:transform 0.2s; }}
.kpi-card:hover {{ transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,0.1); }}
.kpi-card:nth-child(2) {{ border-left-color:var(--color-2); }}
.kpi-card:nth-child(3) {{ border-left-color:var(--color-3); }}
.kpi-card:nth-child(4) {{ border-left-color:var(--color-4); }}
.kpi-card:nth-child(5) {{ border-left-color:var(--color-5); }}
.kpi-card:nth-child(6) {{ border-left-color:var(--color-6); }}
.kpi-card:nth-child(7) {{ border-left-color:var(--color-7); }}
.kpi-label {{ font-size:12px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }}
.kpi-value {{ font-size:24px; font-weight:700; margin-bottom:2px; }}
.kpi-change {{ font-size:12px; font-weight:600; }}
.kpi-change.positive {{ color:var(--positive); }}
.kpi-change.negative {{ color:var(--negative); }}
.chart-row {{ display:grid; grid-template-columns:1fr 1fr; gap:var(--gap); margin-bottom:var(--gap); }}
.chart-row.full {{ grid-template-columns:1fr; }}
.chart-container {{ background:var(--bg-card); border-radius:var(--radius); padding:20px 24px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
.chart-container h3 {{ font-size:14px; font-weight:600; margin-bottom:14px; color:var(--text-primary); display:flex; justify-content:space-between; align-items:center; }}
.chart-container h3 .chart-sub {{ font-size:11px; color:var(--text-secondary); font-weight:400; }}
.chart-container canvas {{ max-height:320px; }}
.chart-container.tall canvas {{ max-height:400px; }}
.table-section {{ background:var(--bg-card); border-radius:var(--radius); padding:20px 24px; box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:var(--gap); overflow-x:auto; }}
.table-section h3 {{ font-size:14px; font-weight:600; margin-bottom:14px; }}
.data-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.data-table thead th {{ text-align:left; padding:10px 12px; border-bottom:2px solid #e0e0e0; color:var(--text-secondary); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; cursor:pointer; white-space:nowrap; }}
.data-table thead th:hover {{ color:var(--text-primary); }}
.data-table tbody td {{ padding:8px 12px; border-bottom:1px solid #f5f5f5; }}
.data-table tbody tr:hover {{ background:#f8f9fa; }}
.pos {{ color:var(--positive); font-weight:600; }}
.neg {{ color:var(--negative); font-weight:600; }}
.footer {{ text-align:center; padding:20px; color:var(--text-secondary); font-size:12px; }}
.footer a {{ color:var(--color-2); text-decoration:none; }}
.stock-toggle {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }}
.stock-chip {{ padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600; cursor:pointer; border:2px solid transparent; transition:all 0.2s; }}
.stock-chip.active {{ opacity:1; }}
.stock-chip.inactive {{ opacity:0.3; }}
.tabs {{ display:flex; gap:4px; margin-bottom:12px; }}
.tab {{ padding:8px 18px; border:none; background:#f0f0f0; color:var(--text-secondary); border-radius:6px; cursor:pointer; font-size:13px; font-weight:500; transition:all 0.2s; }}
.tab.active {{ background:var(--bg-header); color:#fff; }}
@media(max-width:900px) {{ .chart-row{{grid-template-columns:1fr;}} .kpi-row{{grid-template-columns:repeat(2,1fr);}} }}
@media(max-width:600px) {{ .kpi-row{{grid-template-columns:1fr;}} .header{{flex-direction:column;align-items:flex-start;}} }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>KAI Quant · 芯片股量化分析仪表盘</h1>
      <div class="subtitle">沪深A股半导体板块 · 过去一年交易日数据 · Tushare数据源</div>
    </div>
    <div class="live-badge">LIVE DATA</div>
  </div>

  <div class="header" style="background:linear-gradient(135deg,#16213e 0%,#0f3460 100%);">
    <div class="filters">
      <div class="filter-group">
        <label>图表类型</label>
        <select id="chart-type" onchange="switchChart()">
          <option value="normalized">归一化对比 (基准=100)</option>
          <option value="close">收盘价走势</option>
          <option value="change">日涨跌幅</option>
        </select>
      </div>
      <div class="filter-group">
        <label>时间范围</label>
        <select id="time-range" onchange="updateTimeRange()">
          <option value="all">全部</option>
          <option value="3m">近3个月</option>
          <option value="1m">近1个月</option>
        </select>
      </div>
      <div class="filter-group">
        <label>基准股票</label>
        <select id="base-stock" onchange="updateBase()"></select>
      </div>
    </div>
  </div>

  <div class="kpi-row" id="kpi-row"></div>

  <div class="chart-row full">
    <div class="chart-container tall">
      <h3><span id="main-chart-title">归一化收盘价对比 (起始日=100)</span><span class="chart-sub" id="main-chart-sub"></span></h3>
      <div class="stock-toggle" id="stock-toggle"></div>
      <canvas id="main-chart"></canvas>
    </div>
  </div>

  <div class="chart-row">
    <div class="chart-container">
      <h3>日涨跌幅分布 <span class="chart-sub">最近交易日</span></h3>
      <canvas id="change-chart"></canvas>
    </div>
    <div class="chart-container">
      <h3>年化收益率 vs 波动率 <span class="chart-sub">风险收益比</span></h3>
      <canvas id="risk-chart"></canvas>
    </div>
  </div>

  <div class="chart-row">
    <div class="chart-container">
      <h3>成交量对比 <span class="chart-sub">万手</span></h3>
      <canvas id="vol-chart"></canvas>
    </div>
    <div class="chart-container">
      <h3>累计收益率排名 <span class="chart-sub">过去一年</span></h3>
      <canvas id="rank-chart"></canvas>
    </div>
  </div>

  <div class="table-section">
    <h3>最新交易日行情数据</h3>
    <table class="data-table" id="data-table">
      <thead><tr>
        <th onclick="sortTable('name')">股票名称</th>
        <th onclick="sortTable('code')">代码</th>
        <th onclick="sortTable('close')">最新收盘价</th>
        <th onclick="sortTable('pct_chg')">日涨跌幅</th>
        <th onclick="sortTable('vol')">成交量(手)</th>
        <th onclick="sortTable('amount')">成交额(千元)</th>
        <th onclick="sortTable('return')">年涨跌幅</th>
        <th onclick="sortTable('volatility')">年波动率</th>
        <th onclick="sortTable('sharpe')">夏普比率</th>
      </tr></thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <div class="footer">
    <p>KAI Quant Dashboard · 数据来源: <a href="https://tushare.pro" target="_blank">Tushare</a> · 
       GitHub: <a href="https://github.com/Kairos2425/KAI_quant" target="_blank">Kairos2425/KAI_quant</a></p>
    <p style="margin-top:4px;">本仪表盘仅供学习研究，不构成投资建议。股市有风险，投资需谨慎。</p>
  </div>
</div>

<script>
const RAW_DATA = {data_json};
const COLORS = ['#e63946','#457b9d','#2a9d8f','#e9c46a','#f4a261','#264653','#6a4c93'];
const NAMES = RAW_DATA.stocks;

let activeStocks = new Set(NAMES);
let currentChartType = 'normalized';
let mainChart, changeChart, riskChart, volChart, rankChart;
let sortCol = 'return', sortDir = 'desc';

// === 工具函数 ===
function fmtDate(d) {{
  return d.substring(0,4)+'-'+d.substring(4,6)+'-'+d.substring(6,8);
}}
function fmtNum(v, dec=2) {{
  if (v == null || isNaN(v)) return '-';
  if (Math.abs(v) >= 1e8) return (v/1e8).toFixed(dec)+'亿';
  if (Math.abs(v) >= 1e4) return (v/1e4).toFixed(dec)+'万';
  return Number(v).toFixed(dec);
}}
function fmtPct(v) {{
  if (v == null || isNaN(v)) return '-';
  return (v>=0?'+':'')+Number(v).toFixed(2)+'%';
}}

// === 计算统计指标 ===
function calcStats(name) {{
  const d = RAW_DATA.raw[name];
  if (!d || !d.closes.length) return null;
  const closes = d.closes;
  const changes = d.changes;
  const first = closes[0], last = closes[closes.length-1];
  const totalReturn = (last - first) / first * 100;
  
  // 年化收益率
  const days = closes.length;
  const annReturn = (Math.pow(last/first, 252/days) - 1) * 100;
  
  // 日收益率波动率
  const validChanges = changes.filter(c => c != null);
  const meanChg = validChanges.reduce((a,b)=>a+b,0) / validChanges.length;
  const variance = validChanges.reduce((a,b)=>a+(b-meanChg)**2,0) / validChanges.length;
  const dailyVol = Math.sqrt(variance);
  const annVol = dailyVol * Math.sqrt(252);
  
  // 夏普比率 (假设无风险利率2%)
  const sharpe = (annReturn - 2) / annVol;
  
  // 最大回撤
  let maxDD = 0, peak = closes[0];
  for (const c of closes) {{
    if (c > peak) peak = c;
    const dd = (peak - c) / peak * 100;
    if (dd > maxDD) maxDD = dd;
  }}
  
  return {{
    name, code: d.code, close: last, pct_chg: changes[changes.length-1],
    vol: d.vols[d.vols.length-1], amount: d.amounts[d.amounts.length-1],
    totalReturn, annReturn, annVol, sharpe, maxDD, days
  }};
}}

// === KPI 卡片 ===
function renderKPIs() {{
  const container = document.getElementById('kpi-row');
  let html = '';
  NAMES.forEach((name, i) => {{
    const s = calcStats(name);
    if (!s) return;
    const color = COLORS[i % COLORS.length];
    const chgClass = s.totalReturn >= 0 ? 'positive' : 'negative';
    html += `<div class="kpi-card" style="border-left-color:${{color}}">
      <div class="kpi-label">${{name}}</div>
      <div class="kpi-value">¥${{s.close.toFixed(2)}}</div>
      <div class="kpi-change ${{chgClass}}">${{fmtPct(s.totalReturn)}} (1年) · 夏普${{s.sharpe.toFixed(2)}}</div>
    </div>`;
  }});
  container.innerHTML = html;
}}

// === 股票切换 ===
function renderStockToggle() {{
  const container = document.getElementById('stock-toggle');
  let html = '';
  NAMES.forEach((name, i) => {{
    const color = COLORS[i % COLORS.length];
    const active = activeStocks.has(name);
    html += `<span class="stock-chip ${{active?'active':'inactive'}}" 
      style="background:${{color}}20;color:${{color}};border-color:${{color}}" 
      onclick="toggleStock('${{name}}')">${{name}}</span>`;
  }});
  container.innerHTML = html;
}}
function toggleStock(name) {{
  if (activeStocks.has(name)) {{
    if (activeStocks.size > 1) activeStocks.delete(name);
  }} else {{
    activeStocks.add(name);
  }}
  renderStockToggle();
  updateMainChart();
}}

// === 主图表 ===
function updateMainChart() {{
  const ctx = document.getElementById('main-chart').getContext('2d');
  if (mainChart) mainChart.destroy();
  
  let datasets = [], labels = [];
  let title = '';
  
  if (currentChartType === 'normalized') {{
    title = '归一化收盘价对比 (起始日=100)';
    const refName = NAMES[0];
    labels = RAW_DATA.normalized[refName]?.dates.map(fmtDate) || [];
    NAMES.forEach((name, i) => {{
      if (!activeStocks.has(name)) return;
      const d = RAW_DATA.normalized[name];
      if (!d) return;
      datasets.push({{
        label: name, data: d.values, borderColor: COLORS[i],
        backgroundColor: COLORS[i]+'15', borderWidth: 2, tension: 0.3,
        pointRadius: 0, pointHoverRadius: 5, fill: false
      }});
    }});
  }} else if (currentChartType === 'close') {{
    title = '收盘价走势 (元)';
    const refName = NAMES[0];
    labels = RAW_DATA.raw[refName]?.dates.map(fmtDate) || [];
    NAMES.forEach((name, i) => {{
      if (!activeStocks.has(name)) return;
      const d = RAW_DATA.raw[name];
      if (!d) return;
      datasets.push({{
        label: name, data: d.closes, borderColor: COLORS[i],
        backgroundColor: COLORS[i]+'15', borderWidth: 2, tension: 0.3,
        pointRadius: 0, pointHoverRadius: 5, fill: false
      }});
    }});
  }} else if (currentChartType === 'change') {{
    title = '日涨跌幅 (%)';
    const refName = NAMES[0];
    labels = RAW_DATA.raw[refName]?.dates.map(fmtDate) || [];
    NAMES.forEach((name, i) => {{
      if (!activeStocks.has(name)) return;
      const d = RAW_DATA.raw[name];
      if (!d) return;
      datasets.push({{
        label: name, data: d.changes, borderColor: COLORS[i],
        backgroundColor: COLORS[i]+'15', borderWidth: 1.5, tension: 0.1,
        pointRadius: 0, pointHoverRadius: 4, fill: false
      }});
    }});
  }}
  
  document.getElementById('main-chart-title').textContent = title;
  
  mainChart = new Chart(ctx, {{
    type: 'line', data: {{ labels, datasets }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 16 }} }},
        tooltip: {{
          callbacks: {{
            label: ctx => `${{ctx.dataset.label}}: ${{ctx.parsed.y.toFixed(2)}}${{currentChartType==='change'?'%':currentChartType==='close'?'元':''}}`
          }}
        }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }}, ticks: {{ maxTicksLimit: 12 }} }},
        y: {{ grid: {{ color: '#f0f0f0' }} }}
      }}
    }}
  }});
}}

// === 日涨跌幅柱状图 ===
function renderChangeChart() {{
  const ctx = document.getElementById('change-chart').getContext('2d');
  const labels = NAMES;
  const data = NAMES.map(n => {{
    const d = RAW_DATA.raw[n];
    return d ? d.changes[d.changes.length-1] : 0;
  }});
  changeChart = new Chart(ctx, {{
    type: 'bar', data: {{ labels, datasets: [{{
      label: '最新日涨跌幅(%)', data,
      backgroundColor: data.map(v => v >= 0 ? '#e63946cc' : '#2a9d8fcc'),
      borderColor: data.map(v => v >= 0 ? '#e63946' : '#2a9d8f'),
      borderWidth: 1, borderRadius: 4
    }}] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ grid: {{ color: '#f0f0f0' }} }} }}
    }}
  }});
}}

// === 风险收益散点图 ===
function renderRiskChart() {{
  const ctx = document.getElementById('risk-chart').getContext('2d');
  const stats = NAMES.map(n => calcStats(n)).filter(s => s);
  riskChart = new Chart(ctx, {{
    type: 'scatter', data: {{
      datasets: stats.map((s, i) => ({{
        label: s.name, data: [{{ x: s.annVol, y: s.annReturn }}],
        backgroundColor: COLORS[i % COLORS.length],
        pointRadius: 10, pointHoverRadius: 14
      }}))
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{
          label: ctx => `${{ctx.dataset.label}}: 收益率${{ctx.parsed.y.toFixed(1)}}% / 波动率${{ctx.parsed.x.toFixed(1)}}%`
        }}}}
      }},
      scales: {{
        x: {{ title: {{ display: true, text: '年化波动率 (%)' }}, grid: {{ color: '#f0f0f0' }} }},
        y: {{ title: {{ display: true, text: '年化收益率 (%)' }}, grid: {{ color: '#f0f0f0' }} }}
      }}
    }}
  }});
}}

// === 成交量图 ===
function renderVolChart() {{
  const ctx = document.getElementById('vol-chart').getContext('2d');
  const labels = NAMES;
  const data = NAMES.map(n => {{
    const d = RAW_DATA.raw[n];
    return d ? d.vols[d.vols.length-1] / 10000 : 0;
  }});
  volChart = new Chart(ctx, {{
    type: 'bar', data: {{ labels, datasets: [{{
      label: '最新日成交量(万手)', data,
      backgroundColor: COLORS.map(c => c + 'cc'),
      borderColor: COLORS, borderWidth: 1, borderRadius: 4
    }}] }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ grid: {{ color: '#f0f0f0' }} }} }}
    }}
  }});
}}

// === 累计收益排名 ===
function renderRankChart() {{
  const ctx = document.getElementById('rank-chart').getContext('2d');
  const stats = NAMES.map(n => calcStats(n)).filter(s => s).sort((a,b) => b.totalReturn - a.totalReturn);
  const labels = stats.map(s => s.name);
  const data = stats.map(s => s.totalReturn);
  rankChart = new Chart(ctx, {{
    type: 'bar', data: {{ labels, datasets: [{{
      label: '年累计收益率(%)', data,
      backgroundColor: data.map(v => v >= 0 ? '#e63946cc' : '#2a9d8fcc'),
      borderColor: data.map(v => v >= 0 ? '#e63946' : '#2a9d8f'),
      borderWidth: 1, borderRadius: 4
    }}] }},
    options: {{
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ color: '#f0f0f0' }} }} }}
    }}
  }});
}}

// === 数据表格 ===
function renderTable() {{
  const tbody = document.getElementById('table-body');
  let stats = NAMES.map(n => calcStats(n)).filter(s => s);
  stats.sort((a,b) => {{
    let va = a[sortCol], vb = b[sortCol];
    if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortDir === 'asc' ? va - vb : vb - va;
  }});
  let html = '';
  stats.forEach(s => {{
    html += `<tr>
      <td><strong>${{s.name}}</strong></td>
      <td>${{s.code}}</td>
      <td>¥${{s.close.toFixed(2)}}</td>
      <td class="${{s.pct_chg>=0?'pos':'neg'}}">${{fmtPct(s.pct_chg)}}</td>
      <td>${{fmtNum(s.vol)}}</td>
      <td>${{fmtNum(s.amount)}}</td>
      <td class="${{s.totalReturn>=0?'pos':'neg'}}">${{fmtPct(s.totalReturn)}}</td>
      <td>${{s.annVol.toFixed(2)}}%</td>
      <td>${{s.sharpe.toFixed(2)}}</td>
    </tr>`;
  }});
  tbody.innerHTML = html;
}}

function sortTable(col) {{
  if (sortCol === col) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  else {{ sortCol = col; sortDir = 'desc'; }}
  renderTable();
}}

// === 交互控制 ===
function switchChart() {{
  currentChartType = document.getElementById('chart-type').value;
  updateMainChart();
}}
function updateTimeRange() {{
  // 简化: 全部数据已加载
  updateMainChart();
}}
function updateBase() {{
  updateMainChart();
}}

// === 实时刷新模拟 ===
function simulateLiveUpdate() {{
  // 每60秒可在此处接入实时API刷新
}}

// === 初始化 ===
function init() {{
  // 填充基准股票下拉
  const sel = document.getElementById('base-stock');
  NAMES.forEach(n => {{
    const opt = document.createElement('option');
    opt.value = n; opt.textContent = n;
    sel.appendChild(opt);
  }});
  renderKPIs();
  renderStockToggle();
  updateMainChart();
  renderChangeChart();
  renderRiskChart();
  renderVolChart();
  renderRankChart();
  renderTable();
  document.getElementById('main-chart-sub').textContent = `${{NAMES.length}}只股票 · ${{RAW_DATA.raw[NAMES[0]].dates.length}}个交易日`;
}}

init();
</script>
</body>
</html>'''

html_path = os.path.join(OUT, "index.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML仪表盘已生成: {html_path}")
print(f"文件大小: {os.path.getsize(html_path) / 1024:.1f} KB")
