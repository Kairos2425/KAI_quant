#!/usr/bin/env python3
"""
KAI Quant v2 - 增强版交互式量化分析仪表盘生成器
包含K线图、技术指标、投资建议引擎、报告导出功能
"""
import json, os

OUT = r"E:\BA_learn\task\task1"

with open(os.path.join(OUT, "data", "stocks_data_v2.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False)

html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KAI Quant v2 · 芯片股量化分析系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg: #0d1117; --bg2: #161b22; --bg3: #21262d; --bg4: #30363d;
  --text: #c9d1d9; --text2: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --red: #f85149; --yellow: #d2991d; --purple: #bc8cff;
  --buy: #e63946; --hold: #f4a261; --sell: #2a9d8f;
  --radius: 8px; --gap: 14px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif; background:var(--bg); color:var(--text); line-height:1.5; font-size:14px; }
a { color:var(--accent); text-decoration:none; }
::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:var(--bg2); } ::-webkit-scrollbar-thumb { background:var(--bg4); border-radius:3px; }

.container { max-width:1440px; margin:0 auto; padding:12px 16px; }

/* Header */
.header { background:linear-gradient(135deg,#0d1117,#161b22); border:1px solid var(--bg4); border-radius:var(--radius); padding:16px 20px; margin-bottom:var(--gap); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
.header-left h1 { font-size:20px; font-weight:700; background:linear-gradient(90deg,#58a6ff,#bc8cff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.header-left .sub { font-size:12px; color:var(--text2); margin-top:2px; }
.header-right { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.header select { padding:6px 12px; background:var(--bg3); border:1px solid var(--bg4); border-radius:6px; color:var(--text); font-size:13px; }
.live-dot { width:8px; height:8px; background:var(--green); border-radius:50%; display:inline-block; animation:pulse 2s infinite; margin-right:6px; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
.btn { padding:8px 16px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; border:none; transition:all 0.2s; white-space:nowrap; }
.btn-primary { background:var(--accent); color:#fff; } .btn-primary:hover { filter:brightness(1.2); }
.btn-export { background:var(--bg3); color:var(--text); border:1px solid var(--bg4); } .btn-export:hover { border-color:var(--accent); }

/* Score KPI Row */
.score-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:var(--gap); margin-bottom:var(--gap); }
.score-card { background:var(--bg2); border:1px solid var(--bg4); border-radius:var(--radius); padding:14px 16px; }
.score-card .sc-stock { font-size:13px; font-weight:600; margin-bottom:4px; }
.score-card .sc-score { font-size:28px; font-weight:700; }
.score-card .sc-rec { font-size:12px; font-weight:600; margin-top:2px; }
.score-card .sc-risk { font-size:11px; color:var(--text2); margin-top:2px; }

/* Detail Panel */
.detail-panel { background:var(--bg2); border:1px solid var(--bg4); border-radius:var(--radius); padding:16px 20px; margin-bottom:var(--gap); }
.detail-panel h2 { font-size:15px; font-weight:600; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; }
.detail-panel h2 .badge { padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; }
.detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:var(--gap); }

/* Chart Container */
.chart-box { background:var(--bg2); border:1px solid var(--bg4); border-radius:var(--radius); padding:14px 18px; margin-bottom:var(--gap); }
.chart-box h3 { font-size:13px; font-weight:600; margin-bottom:10px; color:var(--text2); }
.chart-box canvas { max-height:350px; }
.chart-box.tall canvas { max-height:480px; }

.chart-row { display:grid; grid-template-columns:1fr 1fr; gap:var(--gap); margin-bottom:var(--gap); }
.chart-row.full { grid-template-columns:1fr; }

/* Table */
.table-box { background:var(--bg2); border:1px solid var(--bg4); border-radius:var(--radius); padding:16px 20px; margin-bottom:var(--gap); overflow-x:auto; }
.table-box h3 { font-size:13px; font-weight:600; margin-bottom:10px; color:var(--text2); }
table { width:100%; border-collapse:collapse; font-size:12px; }
th { text-align:left; padding:8px 10px; border-bottom:2px solid var(--bg4); color:var(--text2); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; cursor:pointer; white-space:nowrap; }
td { padding:7px 10px; border-bottom:1px solid var(--bg3); }
tr:hover td { background:var(--bg3); }
.pos { color:var(--red); } .neg { color:var(--green); }

/* Recommendation Box */
.rec-box { padding:14px 18px; border-radius:8px; margin:10px 0; }
.rec-buy { background:#e6394620; border:1px solid #e6394640; } .rec-buy h4 { color:#e63946; }
.rec-sell { background:#2a9d8f20; border:1px solid #2a9d8f40; } .rec-sell h4 { color:#2a9d8f; }
.rec-hold { background:#f4a26120; border:1px solid #f4a26140; } .rec-hold h4 { color:#f4a261; }
.rec-box ul { margin:8px 0 0 18px; color:var(--text2); font-size:12px; }
.rec-box ul li { margin-bottom:4px; }

/* Tabs */
.tabs { display:flex; gap:4px; margin-bottom:8px; flex-wrap:wrap; }
.tab { padding:6px 14px; border-radius:6px; font-size:12px; cursor:pointer; background:var(--bg3); color:var(--text2); border:none; transition:all 0.2s; }
.tab.active { background:var(--accent); color:#fff; }

/* Footer */
.footer { text-align:center; padding:20px; color:var(--text2); font-size:11px; border-top:1px solid var(--bg4); margin-top:20px; }

/* Print */
@media print {
  body { background:#fff; color:#000; } .header,.btn,.tabs { display:none; }
  .score-card,.detail-panel,.chart-box,.table-box { background:#fff; border:1px solid #ddd; break-inside:avoid; }
  .chart-box canvas { max-height:300px; }
}
@media(max-width:900px) { .chart-row,.detail-grid { grid-template-columns:1fr; } .score-row { grid-template-columns:repeat(2,1fr); } }
@media(max-width:600px) { .score-row { grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div class="header-left">
    <h1>KAI Quant v2 · 芯片股量化分析系统</h1>
    <div class="sub">沪深A股半导体板块 · {{STOCK_COUNT}}只标的 · 过去一年交易日数据</div>
  </div>
  <div class="header-right">
    <span class="live-dot"></span><span style="font-size:12px;color:var(--green);">LIVE</span>
    <select id="stock-select" onchange="switchStock()"></select>
    <button class="btn btn-primary" onclick="window.print()">📄 导出报告</button>
    <button class="btn btn-export" onclick="exportCSV()">📥 导出CSV</button>
  </div>
</div>

<!-- Investment Score Cards -->
<div class="score-row" id="score-row"></div>

<!-- K-Line + MA Chart -->
<div class="chart-box tall">
  <h3><span id="kl-title">K线图 + 均线系统</span></h3>
  <canvas id="kl-chart"></canvas>
</div>

<!-- Technical Indicators 2x2 -->
<div class="chart-row">
  <div class="chart-box"><h3>MACD 指标</h3><canvas id="macd-chart"></canvas></div>
  <div class="chart-box"><h3>RSI 相对强弱 (14)</h3><canvas id="rsi-chart"></canvas></div>
</div>
<div class="chart-row">
  <div class="chart-box"><h3>KDJ 随机指标</h3><canvas id="kdj-chart"></canvas></div>
  <div class="chart-box"><h3>布林带 BOLL (20,2)</h3><canvas id="boll-chart"></canvas></div>
</div>

<!-- Multi-stock Comparison -->
<div class="chart-row full">
  <div class="chart-box tall">
    <h3>多股归一化对比</h3>
    <div class="tabs" id="comp-tabs"></div>
    <canvas id="comp-chart"></canvas>
  </div>
</div>

<!-- Technical Indicator Summary Table -->
<div class="table-box">
  <h3>技术指标统计摘要</h3>
  <table id="indicator-table">
    <thead><tr>
      <th>指标</th><th>当前值</th><th>状态</th><th>趋势</th><th>操作信号</th><th>解读</th>
    </tr></thead>
    <tbody id="indicator-body"></tbody>
  </table>
</div>

<!-- Investment Recommendation Details -->
<div class="detail-panel" id="detail-panel">
  <h2><span>投资建议详情</span><span class="badge" id="detail-badge"></span></h2>
  <div class="detail-grid">
    <div id="detail-left"></div>
    <div id="detail-right"></div>
  </div>
  <div id="detail-operation"></div>
</div>

<!-- Support & Resistance -->
<div class="chart-row">
  <div class="chart-box"><h3>支撑位 / 阻力位</h3><canvas id="sr-chart"></canvas></div>
  <div class="chart-box"><h3>成交量分析</h3><canvas id="volana-chart"></canvas></div>
</div>

<div class="footer">
  <p><strong>KAI Quant v2</strong> · 数据来源: Tushare Pro · GitHub: Kairos2425/KAI_quant · 生成时间: <span id="gentime"></span></p>
  <p style="margin-top:4px;color:var(--yellow)">⚠️ 本系统仅供学习研究，不构成投资建议。量化评分基于技术指标，不保证盈利。股市有风险，投资需谨慎。</p>
</div>

</div>

<script>
const DATA = ''' + data_json + r''';
const COLORS = ['#e63946','#457b9d','#3fb950','#d2991d','#bc8cff','#58a6ff','#f85149'];
const STOCKS = DATA.stocks;
let currentStock = STOCKS[0];
let charts = {};

// === Helpers ===
function fmtDate(d){return d.substring(0,4)+'-'+d.substring(4,6)+'-'+d.substring(6,8);}
function fmtPct(v){if(v==null||isNaN(v))return'-';return(v>=0?'+':'')+Number(v).toFixed(2)+'%';}
function fmtNum(v){if(v==null||isNaN(v))return'-';if(Math.abs(v)>=1e8)return(v/1e8).toFixed(1)+'亿';if(Math.abs(v)>=1e4)return(v/1e4).toFixed(1)+'万';return v.toFixed(0);}
function fmtPrice(v){if(v==null||isNaN(v))return'-';return Number(v).toFixed(2);}

// === Score Cards ===
function renderScoreCards(){
  const container = document.getElementById('score-row');
  let html = '';
  STOCKS.forEach((name,i)=>{
    const d = DATA.raw[name]; if(!d) return;
    const sc = d.investment_score;
    const isSelected = name===currentStock;
    html += `<div class="score-card" style="${isSelected?'border-color:var(--accent);box-shadow:0 0 12px rgba(88,166,255,0.15)':''}" onclick="selectStock('${name}')">
      <div class="sc-stock">${name}</div>
      <div class="sc-score" style="color:${sc.color}">${sc.score}</div>
      <div class="sc-rec" style="color:${sc.color}">${sc.recommendation}</div>
      <div class="sc-risk">${sc.risk_level} | ${d.desc.substring(0,12)}...</div>
    </div>`;
  });
  container.innerHTML = html;
}

// === K-Line Candlestick Chart ===
function renderKLine(){
  const ctx = document.getElementById('kl-chart').getContext('2d');
  if(charts.kl) charts.kl.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  document.getElementById('kl-title').textContent = `K线图 + 均线系统 — ${currentStock} (${d.code})`;
  
  const dates = d.dates.map(fmtDate);
  const n = dates.length;
  
  // Candlestick data as individual bars
  const ohlc = [];
  for(let i=Math.max(0,n-90); i<n; i++){
    ohlc.push({
      x: i, o: d.opens[i], h: d.highs[i], l: d.lows[i], c: d.closes[i],
      date: dates[i]
    });
  }
  
  const startIdx = Math.max(0,n-90);
  
  charts.kl = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dates.slice(startIdx),
      datasets: [
        { label: 'K线', data: ohlc.map(b=>({x:b.x-startIdx,y:[b.l,b.h]})), type:'bar',
          backgroundColor: ctx=>{const v=ohlc[ctx.dataIndex];return v?.(v.c>=v.o?'#e63946':'#2a9d8f')||'#888';},
          borderColor: ctx=>{const v=ohlc[ctx.dataIndex];return v?.(v.c>=v.o?'#e63946':'#2a9d8f')||'#888';},
          borderWidth:1, order:1 },
        { label: 'MA5', data: d.ma5.slice(startIdx), borderColor:'#d2991d', borderWidth:1.5, pointRadius:0, type:'line', order:2 },
        { label: 'MA20', data: d.ma20.slice(startIdx), borderColor:'#bc8cff', borderWidth:1.5, pointRadius:0, type:'line', order:2 },
        { label: 'MA60', data: d.ma60.slice(startIdx), borderColor:'#58a6ff', borderWidth:1.5, pointRadius:0, type:'line', order:2 },
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{ legend:{position:'top',labels:{color:'#8b949e',usePointStyle:true,padding:12,font:{size:11}}},
        tooltip:{callbacks:{label:ctx=>{
          if(ctx.datasetIndex===0){const v=ohlc[ctx.dataIndex];return v?`O:${v.o} H:${v.h} L:${v.l} C:${v.c}`:'';}
          return `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)}`;
        }}}}},
      scales:{
        x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},
        y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}
      }
    }
  });
}

// === MACD ===
function renderMACD(){
  const ctx = document.getElementById('macd-chart').getContext('2d');
  if(charts.macd) charts.macd.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-120);
  const dif = d.macd_dif, dea = d.macd_dea, bar = d.macd_bar;
  charts.macd = new Chart(ctx, {
    type:'line', data:{labels:dates.slice(start),datasets:[
      {label:'DIF',data:dif.slice(start),borderColor:'#58a6ff',borderWidth:1.5,pointRadius:0},
      {label:'DEA',data:dea.slice(start),borderColor:'#d2991d',borderWidth:1.5,pointRadius:0},
      {label:'MACD',data:bar.slice(start),backgroundColor:ctx=>bar[start+ctx.dataIndex]>=0?'#e6394640':'#2a9d8f40',borderColor:ctx=>bar[start+ctx.dataIndex]>=0?'#e63946':'#2a9d8f',borderWidth:1,type:'bar'}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b949e',usePointStyle:true,font:{size:10}}}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}}}
  });
}

// === RSI ===
function renderRSI(){
  const ctx = document.getElementById('rsi-chart').getContext('2d');
  if(charts.rsi) charts.rsi.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-120);
  charts.rsi = new Chart(ctx, {
    type:'line', data:{labels:dates.slice(start),datasets:[
      {label:'RSI(14)',data:d.rsi.slice(start),borderColor:'#bc8cff',borderWidth:2,pointRadius:0,fill:false}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b949e',font:{size:10}}},annotation:{}},
      scales:{
        x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},
        y:{min:0,max:100,grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}
      }
    },
    plugins:[{id:'rsiThresholds',beforeDraw:(chart)=>{
      const{ctx,yScale}=chart.scales;
      [30,70].forEach(v=>{
        const y=yScale.getPixelForValue(v);
        ctx.save();ctx.setLineDash([5,5]);ctx.strokeStyle='#30363d';ctx.lineWidth=1;
        ctx.beginPath();ctx.moveTo(chart.chartArea.left,y);ctx.lineTo(chart.chartArea.right,y);ctx.stroke();ctx.restore();
        ctx.fillStyle='#8b949e';ctx.font='10px sans-serif';ctx.fillText(v,chart.chartArea.right+2,y+3);
      });
    }}]
  });
}

// === KDJ ===
function renderKDJ(){
  const ctx = document.getElementById('kdj-chart').getContext('2d');
  if(charts.kdj) charts.kdj.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-120);
  charts.kdj = new Chart(ctx, {
    type:'line', data:{labels:dates.slice(start),datasets:[
      {label:'K',data:d.kdj_k.slice(start),borderColor:'#58a6ff',borderWidth:1.5,pointRadius:0},
      {label:'D',data:d.kdj_d.slice(start),borderColor:'#d2991d',borderWidth:1.5,pointRadius:0},
      {label:'J',data:d.kdj_j.slice(start),borderColor:'#f85149',borderWidth:1.5,pointRadius:0,borderDash:[3,3]}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b949e',usePointStyle:true,font:{size:10}}}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},y:{min:0,max:100,grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}}}
  });
}

// === BOLL ===
function renderBOLL(){
  const ctx = document.getElementById('boll-chart').getContext('2d');
  if(charts.boll) charts.boll.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-120);
  charts.boll = new Chart(ctx, {
    type:'line', data:{labels:dates.slice(start),datasets:[
      {label:'收盘价',data:d.closes.slice(start),borderColor:'#fff',borderWidth:2,pointRadius:0},
      {label:'上轨',data:d.boll_upper.slice(start),borderColor:'#e63946',borderWidth:1,borderDash:[4,4],pointRadius:0,fill:false},
      {label:'中轨',data:d.boll_middle.slice(start),borderColor:'#d2991d',borderWidth:1,pointRadius:0},
      {label:'下轨',data:d.boll_lower.slice(start),borderColor:'#2a9d8f',borderWidth:1,borderDash:[4,4],pointRadius:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b949e',usePointStyle:true,font:{size:10}}}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}}}
  });
}

// === Multi-stock Comparison ===
function renderComparison(){
  const ctx = document.getElementById('comp-chart').getContext('2d');
  if(charts.comp) charts.comp.destroy();
  const datasets = STOCKS.map((name,i)=>{
    const nd = DATA.normalized[name];
    return nd ? {label:name,data:nd.values,borderColor:COLORS[i],borderWidth:2,pointRadius:0,tension:0.3} : null;
  }).filter(d=>d);
  const refName = STOCKS[0];
  const labels = (DATA.normalized[refName]?.dates||[]).map(fmtDate);
  charts.comp = new Chart(ctx, {
    type:'line', data:{labels,datasets},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{color:'#8b949e',usePointStyle:true,font:{size:10}}}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:14,font:{size:10}}},y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10},callback:v=>v.toFixed(0)}}}}
  });
  // Tabs
  let tabHtml = '';
  STOCKS.forEach((name,i)=>{
    tabHtml += `<span class="tab" style="border:1px solid ${COLORS[i]};color:${COLORS[i]};margin:2px" onclick="toggleComp('${name}',this)">${name}</span>`;
  });
  document.getElementById('comp-tabs').innerHTML = tabHtml;
}

// === Indicator Summary Table ===
function renderIndicatorTable(){
  const tbody = document.getElementById('indicator-body');
  const d = DATA.raw[currentStock]; if(!d) return;
  const n = d.dates.length - 1;
  const getLast = (arr) => arr?.filter(v=>v!=null).pop();
  
  const rsi_val = getLast(d.rsi) || 0;
  const k_val = getLast(d.kdj_k) || 0;
  const d_val = getLast(d.kdj_d) || 0;
  const j_val = getLast(d.kdj_j) || 0;
  const dif_val = getLast(d.macd_dif) || 0;
  const dea_val = getLast(d.macd_dea) || 0;
  const macd_bar = getLast(d.macd_bar) || 0;
  const boll_upper = getLast(d.boll_upper) || 0;
  const boll_lower = getLast(d.boll_lower) || 0;
  const price = d.closes[n];
  const ma5 = getLast(d.ma5) || 0;
  const ma20 = getLast(d.ma20) || 0;
  const ma60 = getLast(d.ma60) || 0;
  const boll_width = boll_upper - boll_lower;
  
  const rows = [
    {ind:'最新收盘价',val:fmtPrice(price),status:price>ma5?'偏强':'偏弱',trend:'',sig:'',desc:''},
    {ind:'MA5',val:fmtPrice(ma5),status:price>ma5?'价格>MA5':'价格<MA5',trend:ma5>ma20?'多头':'空头',sig:price>ma5?'偏多':'偏空',desc:'短期趋势'},
    {ind:'MA20',val:fmtPrice(ma20),status:price>ma20?'价格>MA20':'价格<MA20',trend:ma20>ma60?'多头':'空头',sig:ma5>ma20?'金叉区域':'死叉区域',desc:'中期趋势'},
    {ind:'MA60',val:fmtPrice(ma60),status:price>ma60?'价格>MA60':'价格<MA60',trend:'参考',sig:price>ma60?'偏多':'偏空',desc:'长期趋势'},
    {ind:'RSI(14)',val:rsi_val.toFixed(2),status:rsi_val>70?'超买':rsi_val<30?'超卖':'中性',trend:rsi_val>50?'偏强':'偏弱',sig:rsi_val>50?'多头':'空头',desc:rsi_val>70?'注意回调':'正常区间'},
    {ind:'KDJ-K/D/J',val:`${k_val.toFixed(1)}/${d_val.toFixed(1)}/${j_val.toFixed(1)}`,status:j_val>80?'超买':j_val<20?'超卖':'中性',trend:k_val>d_val?'金叉':'死叉',sig:k_val>d_val?'买入':'卖出',desc:j_val>100?'极端超买':'正常'},
    {ind:'MACD DIF/DEA',val:`${dif_val.toFixed(2)}/${dea_val.toFixed(2)}`,status:dif_val>dea_val?'多头':'空头',trend:dif_val>0?'偏多':'偏空',sig:dif_val>dea_val?'持股':'减仓',desc:macd_bar>0?'红柱放大':macd_bar<0?'绿柱放大':'趋零'},
    {ind:'布林带',val:`${fmtPrice(boll_lower)}-${fmtPrice(boll_upper)}`,status:price>boll_upper?'超上轨':price<boll_lower?'破下轨':'通道内',trend:boll_width<price*0.05?'收窄':'正常',sig:price>d.boll_middle[n]?'偏多':'偏空',desc:'波动率指标'},
    {ind:'支撑位',val:fmtPrice(d.support),status:'',trend:'',sig:'',desc:'近20日最低价'},
    {ind:'阻力位',val:fmtPrice(d.resistance),status:'',trend:'',sig:'',desc:'近20日最高价'},
  ];
  
  let html = '';
  rows.forEach(r=>{
    html += `<tr><td><strong>${r.ind}</strong></td><td>${r.val}</td><td>${r.status}</td><td>${r.trend}</td><td style="color:${r.sig.includes('买')||r.sig.includes('多头')||r.sig.includes('金')?'var(--red)':r.sig.includes('卖')||r.sig.includes('空头')||r.sig.includes('死')?'var(--green)':'var(--text2)'}">${r.sig}</td><td style="color:var(--text2);font-size:11px">${r.desc}</td></tr>`;
  });
  tbody.innerHTML = html;
}

// === Investment Detail Panel ===
function renderDetailPanel(){
  const d = DATA.raw[currentStock]; if(!d) return;
  const sc = d.investment_score;
  const p = d.closes[d.closes.length-1];
  const n = d.closes.length;
  
  // Statistics
  const totalReturn = ((p - d.closes[0]) / d.closes[0] * 100).toFixed(1);
  const changes = d.changes.filter(c=>c!=null);
  const meanChg = changes.reduce((a,b)=>a+b,0)/changes.length;
  const variance = changes.reduce((a,b)=>a+Math.pow(b-meanChg,2),0)/changes.length;
  const annVol = (Math.sqrt(variance)*Math.sqrt(252)).toFixed(2);
  const annRet = (Math.pow(p/d.closes[0], 252/n)-1)*100;
  const sharpe = ((annRet-2)/annVol).toFixed(2);
  
  // Max drawdown
  let maxDD = 0, peak = d.closes[0];
  for(const c of d.closes){ if(c>peak) peak=c; const dd=(peak-c)/peak*100; if(dd>maxDD) maxDD=dd; }
  
  // recBox class
  let recClass = 'rec-hold', recTitle = '观望/持有', recColor = 'var(--yellow)';
  if(sc.score>=70){recClass='rec-buy';recTitle='买入信号';recColor='var(--red)';}
  else if(sc.score>=60){recClass='rec-buy';recTitle='偏多';recColor='var(--red)';}
  else if(sc.score<35){recClass='rec-sell';recTitle='卖出信号';recColor='var(--green)';}
  
  document.getElementById('detail-badge').textContent = sc.recommendation;
  document.getElementById('detail-badge').style.background = sc.color;
  
  document.getElementById('detail-left').innerHTML = `
    <div class="rec-box ${recClass}">
      <h4 style="color:${sc.color}">${recTitle} — 综合评分 ${sc.score}/100</h4>
      <ul>${sc.details.map(d=>`<li>${d}</li>`).join('')}</ul>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--text2)">
      <strong>操作建议：</strong>
      ${sc.score>=70?'建议积极关注，可在回调时逢低建仓，设置止损位':sc.score>=60?'建议逢低轻仓介入，控制仓位不超过30%':sc.score>=45?'建议暂时观望，等待趋势明朗后再操作':sc.score>=35?'建议逢高减仓，降低持仓风险':'建议暂时离场观望，规避下行风险'}
    </div>`;
  
  document.getElementById('detail-right').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
      <div><span style="color:var(--text2)">最新收盘价</span><br><strong>¥${fmtPrice(p)}</strong></div>
      <div><span style="color:var(--text2)">年涨跌幅</span><br><strong class="${totalReturn>=0?'pos':'neg'}">${fmtPct(totalReturn)}</strong></div>
      <div><span style="color:var(--text2)">年化收益率</span><br><strong>${annRet.toFixed(2)}%</strong></div>
      <div><span style="color:var(--text2)">年化波动率</span><br><strong>${annVol}%</strong></div>
      <div><span style="color:var(--text2)">夏普比率</span><br><strong>${sharpe}</strong></div>
      <div><span style="color:var(--text2)">最大回撤</span><br><strong class="neg">${maxDD.toFixed(2)}%</strong></div>
      <div><span style="color:var(--text2)">支撑/阻力</span><br><strong>¥${fmtPrice(d.support)} / ¥${fmtPrice(d.resistance)}</strong></div>
      <div><span style="color:var(--text2)">风险等级</span><br><strong>${sc.risk_level}</strong></div>
    </div>`;
  
  // Operation steps
  let steps = '';
  if(sc.score>=70){ steps = `<div style="margin-top:14px;padding:12px;background:var(--bg3);border-radius:8px;font-size:12px">
    <strong style="color:var(--accent)">📋 建议操作步骤：</strong>
    <ol style="margin:8px 0 0 16px;color:var(--text2);line-height:1.8">
      <li><strong>建仓区间：</strong>¥${fmtPrice(p*0.92)} - ¥${fmtPrice(p*0.97)} 附近逢低建仓20-30%</li>
      <li><strong>加仓条件：</strong>MACD金叉确认 + RSI>50 + 放量突破MA20</li>
      <li><strong>止损位：</strong>¥${fmtPrice(p*0.90)} (亏损10%止损)</li>
      <li><strong>第一目标位：</strong>¥${fmtPrice(p*1.15)} (收益15%)</li>
      <li><strong>第二目标位：</strong>¥${fmtPrice(p*1.30)} (收益30%)</li>
    </ol></div>`; }
  else if(sc.score>=45){ steps = `<div style="margin-top:14px;padding:12px;background:var(--bg3);border-radius:8px;font-size:12px">
    <strong style="color:var(--yellow)">📋 观望策略：</strong>
    <ol style="margin:8px 0 0 16px;color:var(--text2);line-height:1.8">
      <li>等待MACD金叉或RSI突破50确认信号</li>
      <li>关注成交量是否放大（放量突破是关键）</li>
      <li>可在支撑位 ¥${fmtPrice(d.support)} 附近轻仓试探(5-10%)</li>
      <li>严格设置止损 ¥${fmtPrice(p*0.93)}</li>
    </ol></div>`; }
  else { steps = `<div style="margin-top:14px;padding:12px;background:var(--bg3);border-radius:8px;font-size:12px">
    <strong style="color:var(--green)">⚠️ 风控建议：</strong>
    <ol style="margin:8px 0 0 16px;color:var(--text2);line-height:1.8">
      <li>建议暂时离场或大幅减仓</li>
      <li>若持有仓位，建议设止损 ¥${fmtPrice(p*0.95)}</li>
      <li>等待趋势反转信号（MA5金叉MA20 + RSI突破50）再考虑介入</li>
      <li>关注基本面变化，警惕利空消息</li>
    </ol></div>`; }
  document.getElementById('detail-operation').innerHTML = steps;
}

// === Support/Resistance Chart ===
function renderSRChart(){
  const ctx = document.getElementById('sr-chart').getContext('2d');
  if(charts.sr) charts.sr.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-60);
  charts.sr = new Chart(ctx, {
    type:'line', data:{labels:dates.slice(start),datasets:[
      {label:'收盘价',data:d.closes.slice(start),borderColor:'#fff',borderWidth:2,pointRadius:0,fill:false},
      {label:'阻力位',data:Array(dates.length-start).fill(d.resistance),borderColor:'#e63946',borderDash:[5,5],borderWidth:1.5,pointRadius:0},
      {label:'支撑位',data:Array(dates.length-start).fill(d.support),borderColor:'#3fb950',borderDash:[5,5],borderWidth:1.5,pointRadius:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8b949e',usePointStyle:true,font:{size:10}}}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10}}}}}
  });
}

// === Volume Analysis Chart ===
function renderVolChart(){
  const ctx = document.getElementById('volana-chart').getContext('2d');
  if(charts.volana) charts.volana.destroy();
  const d = DATA.raw[currentStock]; if(!d) return;
  const dates = d.dates.map(fmtDate);
  const n = dates.length, start = Math.max(0,n-60);
  const vols = d.vols.slice(start);
  const closes = d.closes.slice(start);
  charts.volana = new Chart(ctx, {
    type:'bar', data:{labels:dates.slice(start),datasets:[
      {label:'成交量(手)',data:vols,backgroundColor:ctx=>{return closes[ctx.dataIndex]>=closes[Math.max(0,ctx.dataIndex-1)]?'#e6394650':'#2a9d8f50';},borderColor:ctx=>{return closes[ctx.dataIndex]>=closes[Math.max(0,ctx.dataIndex-1)]?'#e63946':'#2a9d8f';},borderWidth:1}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{grid:{color:'#21262d'},ticks:{color:'#8b949e',maxTicksLimit:12,font:{size:10}}},y:{grid:{color:'#21262d'},ticks:{color:'#8b949e',font:{size:10},callback:v=>fmtNum(v)}}}}
  });
}

// === Navigation ===
function selectStock(name){ currentStock=name; renderScoreCards(); renderAllCharts(); renderIndicatorTable(); renderDetailPanel(); }
function switchStock(){ const sel=document.getElementById('stock-select'); if(sel.value) selectStock(sel.value); }
function toggleComp(name,el){
  const vis = charts.comp?.getDatasetMeta(STOCKS.indexOf(name))?.hidden;
  if(vis!==undefined){
    if(vis===false){charts.comp.hide(STOCKS.indexOf(name));el.style.opacity='0.3';}
    else{charts.comp.show(STOCKS.indexOf(name));el.style.opacity='1';}
  }
}

function renderAllCharts(){ renderKLine(); renderMACD(); renderRSI(); renderKDJ(); renderBOLL(); renderSRChart(); renderVolChart(); }

function init(){
  // Stock selector
  const sel = document.getElementById('stock-select');
  STOCKS.forEach((n,i)=>sel.appendChild(new Option(n,n)));
  sel.value = currentStock;
  
  renderScoreCards();
  renderAllCharts();
  renderComparison();
  renderIndicatorTable();
  renderDetailPanel();
  document.getElementById('gentime').textContent = new Date().toLocaleString('zh-CN');
}

function exportCSV(){
  const d = DATA.raw[currentStock]; if(!d) return;
  let csv = 'date,open,high,low,close,change,volume,amount\n';
  d.dates.forEach((dt,i)=>{
    csv += `${dt},${d.opens[i]},${d.highs[i]},${d.lows[i]},${d.closes[i]},${d.changes[i]},${d.vols[i]},${d.amounts[i]}\n`;
  });
  const blob = new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=`${currentStock}_daily.csv`; a.click();
}

document.getElementById('stock-select').value = currentStock;
document.getElementById('gentime').textContent = new Date().toLocaleString('zh-CN');
document.querySelector('.sub').textContent = document.querySelector('.sub').textContent.replace('{{STOCK_COUNT}}', STOCKS.length);
init();
</script>
</body>
</html>'''

html_path = os.path.join(OUT, "index.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML生成完成: {html_path} ({os.path.getsize(html_path)/1024:.1f} KB)")
