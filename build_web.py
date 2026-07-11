# -*- coding: utf-8 -*-
"""
build_web.py
生成自包含（离线可用）的双均线策略可视化网页：dual_ma_dashboard.html
- 内嵌股价数据，无需联网
- 纯 JS 实现双均线回测（逻辑与 dual_ma_backtest.py 一致）
- Canvas 自绘图表（价格+均线+买卖信号 / 策略净值 vs 买入持有）
- 指标面板 + 多股票×多周期对比表 + 策略分析报告
"""
import os, json
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chip_stocks_daily.csv")
GRID_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_output", "results.json")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dual_ma_dashboard.html")

STOCK_NAMES = {
    "688981.SH": "中芯国际", "603501.SH": "韦尔股份", "002371.SZ": "北方华创",
    "688012.SH": "中微公司", "002049.SZ": "紫光国微", "600584.SH": "长电科技",
    "688256.SH": "寒武纪",
}


def build_data():
    df = pd.read_csv(CSV_PATH)
    df["trade_date"] = df["trade_date"].astype(str)
    stocks = {}
    for code, g in df.groupby("ts_code"):
        g = g.sort_values("trade_date")
        stocks[code] = {
            "name": STOCK_NAMES.get(code, code),
            "dates": [d[:4] + "-" + d[4:6] + "-" + d[6:] for d in g["trade_date"].tolist()],
            "open": [float(x) for x in g["open"].tolist()],
            "high": [float(x) for x in g["high"].tolist()],
            "low": [float(x) for x in g["low"].tolist()],
            "close": [float(x) for x in g["close"].tolist()],
        }
    grid = []
    if os.path.exists(GRID_PATH):
        grid = json.load(open(GRID_PATH, encoding="utf-8"))
    # 仅保留主要展示字段
    grid_clean = []
    for r in grid:
        grid_clean.append({
            "ts_code": r["ts_code"], "name": r.get("name", STOCK_NAMES.get(r["ts_code"], r["ts_code"])),
            "short": r["short"], "long": r["long"],
            "cumulative_return": r["cumulative_return"], "annual_return": r["annual_return"],
            "max_drawdown": r["max_drawdown"], "sharpe": r["sharpe"],
            "annual_vol": r["annual_vol"], "buyhold_return": r["buyhold_return"],
            "n_trades": r["n_trades"], "final_equity": r["final_equity"],
        })
    return {
        "meta": {"trading_days": 252, "cost": 0.001, "init_capital": 100000.0, "risk_free": 0.0},
        "stocks": stocks,
        "grid": grid_clean,
        "order": list(STOCK_NAMES.keys()),
    }


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>双均线策略回测 · 芯片股可视化分析</title>
<style>
:root{
  --bg:#0d1117; --bg2:#161b22; --bg3:#21262d; --bg4:#30363d;
  --text:#c9d1d9; --text2:#8b949e; --accent:#58a6ff;
  --green:#3fb950; --red:#f85149; --yellow:#d2991d; --purple:#bc8cff;
  --buy:#e63946; --sell:#2a9d8f; --up:#f85149; --down:#3fb950;
  --radius:10px; --gap:14px;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;font-size:14px;}
a{color:var(--accent);text-decoration:none;}
.container{max-width:1320px;margin:0 auto;padding:14px 18px;}
.header{background:linear-gradient(135deg,#0d1117,#161b22);border:1px solid var(--bg4);border-radius:var(--radius);padding:18px 22px;margin-bottom:var(--gap);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;}
.header-left h1{font-size:21px;font-weight:700;background:linear-gradient(90deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.header-left .sub{font-size:12px;color:var(--text2);margin-top:3px;}
.controls{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;background:var(--bg2);border:1px solid var(--bg4);border-radius:var(--radius);padding:14px 18px;margin-bottom:var(--gap);}
.field{display:flex;flex-direction:column;gap:4px;}
.field label{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;}
.field select,.field input{background:var(--bg3);border:1px solid var(--bg4);border-radius:6px;color:var(--text);font-size:14px;padding:7px 10px;min-width:110px;}
.btn{padding:9px 20px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;border:none;background:var(--accent);color:#fff;transition:filter .15s;}
.btn:hover{filter:brightness(1.15);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);margin-bottom:var(--gap);}
@media(max-width:980px){.grid2{grid-template-columns:1fr;}}
.card{background:var(--bg2);border:1px solid var(--bg4);border-radius:var(--radius);padding:16px 18px;}
.card h2{font-size:15px;margin-bottom:10px;display:flex;align-items:center;gap:8px;}
.card h2 .tag{font-size:11px;background:var(--bg3);color:var(--text2);padding:2px 8px;border-radius:10px;font-weight:500;}
canvas{width:100%;display:block;}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--gap);margin-bottom:var(--gap);}
.kpi{background:var(--bg2);border:1px solid var(--bg4);border-radius:var(--radius);padding:14px 16px;}
.kpi .k-label{font-size:12px;color:var(--text2);}
.kpi .k-val{font-size:24px;font-weight:700;margin-top:4px;}
.kpi .k-sub{font-size:11px;color:var(--text2);margin-top:2px;}
.pos{color:var(--up);}
.neg{color:var(--down);}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--bg4);white-space:nowrap;}
th{color:var(--text2);font-weight:600;position:sticky;top:0;background:var(--bg2);cursor:pointer;user-select:none;}
td.name,th.name{text-align:left;}
tr.sel{background:rgba(88,166,255,.12);}
tr:hover{background:rgba(255,255,255,.04);}
.table-wrap{max-height:420px;overflow:auto;border:1px solid var(--bg4);border-radius:8px;}
.section{background:var(--bg2);border:1px solid var(--bg4);border-radius:var(--radius);padding:20px 24px;margin-bottom:var(--gap);}
.section h2{font-size:18px;margin-bottom:14px;color:var(--accent);}
.section h3{font-size:15px;margin:18px 0 8px;color:var(--purple);}
.section p,.section li{color:var(--text);margin-bottom:8px;}
.section ul,.section ol{padding-left:22px;margin-bottom:10px;}
.section code{background:var(--bg3);padding:2px 6px;border-radius:4px;font-size:12px;color:var(--yellow);}
.note{font-size:12px;color:var(--text2);}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--text2);margin-top:8px;}
.legend span{display:inline-flex;align-items:center;gap:5px;}
.dot{width:10px;height:10px;border-radius:2px;display:inline-block;}
.footer{text-align:center;color:var(--text2);font-size:12px;padding:20px;}
.hl{color:var(--yellow);font-weight:600;}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="header-left">
      <h1>双均线策略回测 · 芯片股可视化分析</h1>
      <div class="sub">金叉买入 / 死叉卖出 · 纯前端离线回测 · 初始资金 ¥100,000 · 单边成本 0.1%</div>
    </div>
    <div class="header-right">
      <span class="live-dot" style="width:8px;height:8px;background:var(--green);border-radius:50%;display:inline-block;margin-right:6px;"></span>
      <span style="font-size:12px;color:var(--text2);">本地数据 · 无需联网</span>
    </div>
  </div>

  <div class="controls">
    <div class="field">
      <label>股票</label>
      <select id="stock"></select>
    </div>
    <div class="field">
      <label>短均线周期</label>
      <input id="short" type="number" value="5" min="2" max="60" step="1">
    </div>
    <div class="field">
      <label>长均线周期</label>
      <input id="long" type="number" value="15" min="3" max="120" step="1">
    </div>
    <div class="field">
      <label>单边成本(%)</label>
      <input id="cost" type="number" value="0.1" min="0" max="2" step="0.05">
    </div>
    <button class="btn" id="run">运行策略</button>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="grid2">
    <div class="card">
      <h2>价格 · 均线 · 交易信号 <span class="tag" id="tag1"></span></h2>
      <canvas id="priceChart" height="380"></canvas>
      <div class="legend">
        <span><i class="dot" style="background:#58a6ff;"></i>收盘价</span>
        <span><i class="dot" style="background:#ff7f0e;"></i>短均线</span>
        <span><i class="dot" style="background:#3fb950;"></i>长均线</span>
        <span><i class="dot" style="background:#e63946;"></i>买入(金叉)</span>
        <span><i class="dot" style="background:#2a9d8f;"></i>卖出(死叉)</span>
      </div>
    </div>
    <div class="card">
      <h2>策略净值 vs 买入持有 <span class="tag" id="tag2"></span></h2>
      <canvas id="equityChart" height="380"></canvas>
      <div class="legend">
        <span><i class="dot" style="background:#bc8cff;"></i>策略净值</span>
        <span><i class="dot" style="background:#8b949e;"></i>买入持有(基准)</span>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>多股票 × 多周期 收益对比</h2>
    <p class="note">下表为 7 只芯片股在 5 组均线参数下的回测结果（成本 0.1%）。点击任意行可载入该股票与参数到上方主视图。当前所选股票以高亮显示。</p>
    <div class="table-wrap">
      <table id="gridTable">
        <thead>
          <tr>
            <th class="name" data-k="name">股票</th>
            <th data-k="short">短</th>
            <th data-k="long">长</th>
            <th data-k="cumulative_return">累计回报</th>
            <th data-k="annual_return">年化收益</th>
            <th data-k="max_drawdown">最大回撤</th>
            <th data-k="sharpe">夏普</th>
            <th data-k="annual_vol">年化波动</th>
            <th data-k="buyhold_return">买入持有</th>
            <th data-k="n_trades">交易次数</th>
          </tr>
        </thead>
        <tbody id="gridBody"></tbody>
      </table>
    </div>
  </div>

  <div class="section" id="report">
    <h2>策略分析报告</h2>

    <h3>一、双均线策略原理：金叉与死叉</h3>
    <p>双均线策略使用两条<strong>简单移动平均线（SMA）</strong>：短周期均线（如 MA5）反映近期价格趋势，长周期均线（如 MA15）反映中期趋势。核心假设是<strong>趋势具有惯性</strong>：当短均线从下方穿越长均线，说明短期动能转强，是<strong>买入信号（金叉，Golden Cross）</strong>；当短均线从上方跌破长均线，说明短期动能走弱，是<strong>卖出信号（死叉，Death Cross）</strong>。</p>
    <ul>
      <li><span class="hl">金叉</span>：短均线由下向上穿越长均线 → 做多/加仓。</li>
      <li><span class="hl">死叉</span>：短均线由上向下穿越长均线 → 平仓/离场。</li>
      <li>本实现的细节：信号由<strong>当日收盘价</strong>计算，实际成交在<strong>次日开盘价</strong>执行，避免前视偏差（look-ahead bias）；金叉满仓买入、死叉清仓，为多头-only 回测。</li>
    </ul>

    <h3>二、量化效果基础指标</h3>
    <ul>
      <li><span class="hl">累计回报 Cumulative Return</span>：期末净值/初始资金 − 1，反映整个回测期的绝对收益。</li>
      <li><span class="hl">最大回撤 MDD</span>：净值从历史高点回落的最大幅度（min(净值/历史最高点 − 1)）。衡量<strong>最坏情况下的潜在亏损</strong>，是风控核心指标，越小（越接近0）越好。</li>
      <li><span class="hl">夏普比率 Sharpe Ratio</span>：(日均超额收益 / 日均收益标准差) × √252。衡量<strong>每承担一单位风险获得的超额回报</strong>，&gt;1 通常视为良好，&gt;2 优秀。</li>
      <li><span class="hl">年化收益 / 年化波动率</span>：将区间收益与波动按 252 交易日年化，便于跨周期比较。</li>
      <li><span class="hl">买入持有对比 Buy &amp; Hold</span>：同期"买了不动"的回报，用于判断策略是否真的创造了价值（很多趋势策略在强牛市反而跑输买入持有）。</li>
      <li><span class="hl">交易次数</span>：反映换手频率与摩擦成本的影响。</li>
    </ul>

    <h3>三、中芯国际（688981.SH）实证</h3>
    <p id="smicText"></p>

    <h3>四、多股票 / 多周期观察</h3>
    <ul>
      <li><strong>周期越短越灵敏</strong>：MA5/MA15 捕捉机会多、交易次数高，但在震荡市易被"假突破"反复打脸（whipsaw）。</li>
      <li><strong>周期越长越平滑</strong>：MA20/MA60 信号少、回撤通常更小，但会错过早期行情、滞后期更长。</li>
      <li><strong>个股分化明显</strong>：强趋势股（如区间内单边上行者）双均线收益接近甚至跑赢买入持有；箱体震荡股则因频繁进出而明显跑输。</li>
    </ul>

    <h3>五、适用场景与应用心得</h3>
    <ul>
      <li><span class="hl">适用</span>：明显的单边趋势市、成长股主升浪；作为趋势跟踪的入门框架与信号过滤器。</li>
      <li><span class="hl">不适用</span>：横盘震荡市（信号反复、摩擦成本吞噬收益）；高波动无趋势品种。</li>
      <li><span class="hl">心得 1 · 参数过拟合</span>：在历史上调出"漂亮"的参数，往往只是过度拟合，样本外容易失效。建议用多组参数取稳健区间，而非追求单组最优。</li>
      <li><span class="hl">心得 2 · 成本是隐形杀手</span>：单边 0.1% 看似小，高频交易下累积显著。本回测已计入，实盘需把佣金+滑点算足。</li>
      <li><span class="hl">心得 3 · 风控优先</span>：比起追求高收益，控制 MDD 更关键——一次大回撤会摧毁复利。可叠加止损、仓位管理。</li>
      <li><span class="hl">心得 4 · 组合使用</span>：双均线单独用胜率有限，宜与成交量、波动率、基本面或宏观信号结合，作为"确认"而非"唯一"依据。</li>
    </ul>
  </div>

  <div class="footer">数据区间 2025-07-01 ~ 2026-06-30 · 回测为教学演示，非投资建议</div>
</div>

<script>
const DATA = /*__DATA__*/;
const $ = id => document.getElementById(id);

// ---------- 回测核心（与 dual_ma_backtest.py 逻辑一致）----------
function sma(arr, w){
  const out = new Array(arr.length).fill(null);
  let sum = 0;
  for(let i=0;i<arr.length;i++){
    sum += arr[i];
    if(i>=w) sum -= arr[i-w];
    if(i>=w-1) out[i] = sum/w;
  }
  return out;
}
function stdSample(a){
  if(a.length<2) return 0;
  const m = a.reduce((s,x)=>s+x,0)/a.length;
  const v = a.reduce((s,x)=>s+(x-m)*(x-m),0)/(a.length-1);
  return Math.sqrt(v);
}
function backtest(code, short, long, costPct){
  const st = DATA.stocks[code];
  const close = st.close, open = st.open, dates = st.dates;
  const n = close.length;
  const s = sma(close, short), l = sma(close, long);
  const signal = new Array(n).fill(0);
  const action = new Array(n).fill(null);
  for(let i=1;i<n;i++){
    if(s[i]==null||l[i]==null||s[i-1]==null||l[i-1]==null) continue;
    const diff = s[i]-l[i], pdiff = s[i-1]-l[i-1];
    if(pdiff<=0 && diff>0) signal[i]=1;
    else if(pdiff>=0 && diff<0) signal[i]=-1;
  }
  for(let i=0;i<n;i++) action[i] = (i>0)? signal[i-1] : null;
  const cost = costPct/100;
  let cash = DATA.meta.init_capital, shares=0, pos=0;
  const equity = new Array(n); const trades=[];
  const buyPts=[], sellPts=[];
  for(let i=0;i<n;i++){
    const act = action[i], o=open[i], c=close[i];
    if(act!==null && act!==0){
      if(act===1 && pos===0){ shares = cash/(o*(1+cost)); cash=0; pos=1; trades.push({date:dates[i],side:'BUY',price:o}); buyPts.push({i, y:c}); }
      else if(act===-1 && pos===1){ cash = shares*o*(1-cost); trades.push({date:dates[i],side:'SELL',price:o}); shares=0; pos=0; sellPts.push({i, y:c}); }
    }
    equity[i] = cash + shares*c;
  }
  // 指标
  const eq = equity;
  const dailyRet=[];
  for(let i=1;i<n;i++) dailyRet.push((eq[i]-eq[i-1])/eq[i-1]);
  const cumRet = eq[n-1]/eq[0]-1;
  const annRet = Math.pow(eq[n-1]/eq[0], DATA.meta.trading_days/n)-1;
  let runMax=eq[0], mdd=0;
  for(let i=0;i<n;i++){ if(eq[i]>runMax) runMax=eq[i]; const dd=eq[i]/runMax-1; if(dd<mdd) mdd=dd; }
  const mean = dailyRet.reduce((a,b)=>a+b,0)/(dailyRet.length||1);
  const sd = stdSample(dailyRet);
  const sharpe = sd>0 ? mean/sd*Math.sqrt(DATA.meta.trading_days) : 0;
  const volAnn = sd*Math.sqrt(DATA.meta.trading_days);
  const buyhold = close[n-1]/close[0]-1;
  return {dates,close,s,l,buyPts,sellPts,equity,buyholdEq:bhEq(close),metrics:{
    cumulative_return:cumRet, annual_return:annRet, max_drawdown:mdd, sharpe,
    annual_vol:volAnn, buyhold_return:buyhold, n_trades:trades.length,
    n_round_trips:Math.floor(trades.length/2), final_equity:eq[n-1]
  }, trades};
}
function bhEq(close){
  const base = close[0];
  return close.map(c=>DATA.meta.init_capital * (c/base));
}

// ---------- Canvas 绘图 ----------
function setupCanvas(cv){
  const dpr = window.devicePixelRatio||1;
  const w = cv.clientWidth, h = cv.clientHeight || 380;
  cv.width = w*dpr; cv.height = h*dpr;
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  return {ctx,w,h};
}
function fmtPct(v){ return (v*100).toFixed(2)+'%'; }
function niceTicks(min,max,count){
  const range = max-min || 1;
  const raw = range/count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw/mag;
  let step;
  if(norm<1.5) step=1; else if(norm<3) step=2; else if(norm<7) step=5; else step=10;
  step*=mag;
  const start = Math.floor(min/step)*step;
  const ticks=[];
  for(let v=start; v<=max+1e-9; v+=step) ticks.push(v);
  return ticks;
}
function drawLineChart(cv, spec, hoverIdx){
  const {ctx,w,h} = setupCanvas(cv);
  ctx.clearRect(0,0,w,h);
  const padL=56, padR=14, padT=14, padB=30;
  const plotW = w-padL-padR, plotH = h-padT-padB;
  // y 范围
  let lo=Infinity, hi=-Infinity;
  spec.lines.forEach(s=>s.data.forEach(p=>{ if(p.y!=null){ if(p.y<lo)lo=p.y; if(p.y>hi)hi=p.y; }}));
  spec.scats&&spec.scats.forEach(s=>s.points.forEach(p=>{ if(p.y<lo)lo=p.y; if(p.y>hi)hi=p.y; }));
  if(!isFinite(lo)){ lo=0; hi=1; }
  const pad=(hi-lo)*0.08||1; lo-=pad; hi+=pad;
  const n = spec.xLabels.length;
  const xAt = i => padL + (n<=1?0:(i/(n-1))*plotW);
  const yAt = v => padT + (1-(v-lo)/(hi-lo))*plotH;
  // 网格 + y 刻度
  ctx.strokeStyle='#21262d'; ctx.fillStyle='#8b949e'; ctx.font='11px "Microsoft YaHei",sans-serif';
  ctx.textAlign='right'; ctx.textBaseline='middle';
  const ticks = niceTicks(lo,hi,5);
  ticks.forEach(t=>{
    const y=yAt(t);
    ctx.beginPath(); ctx.moveTo(padL,y); ctx.lineTo(w-padR,y); ctx.stroke();
    ctx.fillText(t.toFixed(t<10?2:0), padL-6, y);
  });
  // x 刻度
  ctx.textAlign='center'; ctx.textBaseline='top';
  const xticks = 6;
  for(let k=0;k<=xticks;k++){
    const i = Math.round(k/(xticks)*(n-1));
    ctx.fillText(spec.xLabels[i] ? spec.xLabels[i].slice(2) : '', xAt(i), h-padB+6);
  }
  // 零线（如需要）
  // 折线
  spec.lines.forEach(s=>{
    ctx.strokeStyle=s.color; ctx.lineWidth=1.6; ctx.beginPath();
    let started=false;
    s.data.forEach((p,i)=>{
      if(p.y==null) return;
      const x=xAt(i), y=yAt(p.y);
      if(!started){ ctx.moveTo(x,y); started=true; } else ctx.lineTo(x,y);
    });
    ctx.stroke();
  });
  // 散点
  if(spec.scats) spec.scats.forEach(s=>{
    s.points.forEach(p=>{
      const x=xAt(p.i), y=yAt(p.y);
      ctx.fillStyle=s.color;
      if(s.marker==='^'){ ctx.beginPath(); ctx.moveTo(x,y-6); ctx.lineTo(x-5,y+4); ctx.lineTo(x+5,y+4); ctx.closePath(); ctx.fill(); }
      else { ctx.beginPath(); ctx.moveTo(x,y+6); ctx.lineTo(x-5,y-4); ctx.lineTo(x+5,y-4); ctx.closePath(); ctx.fill(); }
    });
  });
  // hover
  if(hoverIdx!=null && hoverIdx>=0 && hoverIdx<n){
    const x=xAt(hoverIdx);
    ctx.strokeStyle='rgba(255,255,255,.25)'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(x,padT); ctx.lineTo(x,h-padB); ctx.stroke();
    // tooltip
    const lines=[spec.xLabels[hoverIdx]];
    spec.lines.forEach(s=>{ const p=s.data[hoverIdx]; if(p&&p.y!=null) lines.push(s.name+': '+p.y.toFixed(2)); });
    if(spec.scats) spec.scats.forEach(s=>{ const hit=s.points.find(p=>p.i===hoverIdx); if(hit) lines.push(s.name); });
    ctx.font='11px "Microsoft YaHei",sans-serif'; ctx.textAlign='left'; ctx.textBaseline='top';
    const tw=Math.max(...lines.map(t=>ctx.measureText(t).width))+12;
    let tx=x+8; if(tx+tw>w-padR) tx=x-8-tw;
    const ty=padT+4;
    ctx.fillStyle='rgba(13,17,23,.92)'; ctx.strokeStyle='#30363d';
    ctx.fillRect(tx,ty,tw,lines.length*15+8); ctx.strokeRect(tx,ty,tw,lines.length*15+8);
    ctx.fillStyle='#c9d1d9';
    lines.forEach((t,k)=>ctx.fillText(t,tx+6,ty+5+k*15));
  }
}

// ---------- 状态 ----------
let lastMainSpec=null, lastEqSpec=null, hoverMain=null, hoverEq=null;

function render(){
  const code=$('stock').value;
  const short=parseInt($('short').value)||5;
  const long=parseInt($('long').value)||15;
  const cost=parseFloat($('cost').value)||0.1;
  if(short>=long){ alert('短均线周期必须小于长均线周期'); return; }
  const r = backtest(code, short, long, cost);
  const m=r.metrics;
  // KPI
  const kpis=[
    ['累计回报', fmtPct(m.cumulative_return), m.cumulative_return>=0?'pos':'neg', '买入持有 '+fmtPct(m.buyhold_return)],
    ['年化收益', fmtPct(m.annual_return), m.annual_return>=0?'pos':'neg', '期末净值 ¥'+m.final_equity.toLocaleString('zh-CN',{maximumFractionDigits:0})],
    ['最大回撤', fmtPct(m.max_drawdown), 'neg', '风控核心指标'],
    ['夏普比率', m.sharpe.toFixed(3), m.sharpe>=1?'pos':'neg', m.sharpe>=1?'良好':'偏低'],
    ['年化波动率', fmtPct(m.annual_vol), 'neg', '风险水平'],
    ['交易次数', m.n_trades+' ('+m.n_round_trips+'回合)', 'pos', '成本影响'],
  ];
  $('kpis').innerHTML = kpis.map(k=>`<div class="kpi"><div class="k-label">${k[0]}</div><div class="k-val ${k[2]}">${k[1]}</div><div class="k-sub">${k[3]}</div></div>`).join('');
  $('tag1').textContent = `${r.dates[0]} ~ ${r.dates[r.dates.length-1]}`;
  $('tag2').textContent = `${DATA.stocks[code].name} MA${short}/MA${long}`;
  // 主图 spec
  const lineData=(arr)=>arr.map((y,i)=>({y}));
  lastMainSpec={xLabels:r.dates, lines:[
    {name:'收盘价',color:'#58a6ff',data:lineData(r.close)},
    {name:'MA'+short,color:'#ff7f0e',data:lineData(r.s)},
    {name:'MA'+long,color:'#3fb950',data:lineData(r.l)},
  ], scats:[
    {name:'买入',color:'#e63946',marker:'^',points:r.buyPts},
    {name:'卖出',color:'#2a9d8f',marker:'v',points:r.sellPts},
  ]};
  lastEqSpec={xLabels:r.dates, lines:[
    {name:'策略净值',color:'#bc8cff',data:lineData(r.equity)},
    {name:'买入持有',color:'#8b949e',data:lineData(r.buyholdEq)},
  ]};
  paintMain(); paintEq();
  // 中芯国际文案
  if(code==='688981.SH'){
    const vs = m.cumulative_return - m.buyhold_return;
    $('smicText').innerHTML = `在默认参数 <code>MA${short}/MA${long}</code> 下，中芯国际区间累计回报 <span class="${m.cumulative_return>=0?'pos':'neg'}">${fmtPct(m.cumulative_return)}</span>，年化收益 ${fmtPct(m.annual_return)}，最大回撤 <span class="neg">${fmtPct(m.max_drawdown)}</span>，夏普比率 <span class="${m.sharpe>=1?'pos':'neg'}">${m.sharpe.toFixed(3)}</span>，共交易 ${m.n_trades} 次（${m.n_round_trips} 个完整回合）。同期买入持有回报为 <span class="${m.buyhold_return>=0?'pos':'neg'}">${fmtPct(m.buyhold_return)}</span>，策略${vs>=0?'<span class="pos">跑赢</span>':'<span class="neg">跑输</span>'}买入持有约 <span class="${vs>=0?'pos':'neg'}">${fmtPct(Math.abs(vs))}</span>。这符合强趋势市的典型特征：双均线在中长期上行通道中因频繁换手与滞后，往往略逊于"买入不动"，但其价值在于<strong>回撤可控、规则透明、可机械执行</strong>。`;
  } else {
    $('smicText').innerHTML = `已切换至 <span class="hl">${DATA.stocks[code].name} (${code})</span>，参数 <code>MA${short}/MA${long}</code>。当前累计回报 <span class="${m.cumulative_return>=0?'pos':'neg'}">${fmtPct(m.cumulative_return)}</span>，最大回撤 <span class="neg">${fmtPct(m.max_drawdown)}</span>，夏普 <span class="${m.sharpe>=1?'pos':'neg'}">${m.sharpe.toFixed(3)}</span>，买入持有 ${fmtPct(m.buyhold_return)}。可与下方对比表交叉验证不同个股的表现分化。`;
  }
}

function paintMain(){ if(lastMainSpec) drawLineChart($('priceChart'), lastMainSpec, hoverMain); }
function paintEq(){ if(lastEqSpec) drawLineChart($('equityChart'), lastEqSpec, hoverEq); }

function bindHover(cv, setHover, paint){
  cv.addEventListener('mousemove', e=>{
    const rect=cv.getBoundingClientRect();
    const x=e.clientX-rect.left;
    const padL=56, padR=14, plotW=cv.clientWidth-padL-padR;
    let idx=Math.round((x-padL)/plotW*(lastMainSpec.xLabels.length-1));
    idx=Math.max(0,Math.min(lastMainSpec.xLabels.length-1,idx));
    setHover(idx); paint();
  });
  cv.addEventListener('mouseleave', ()=>{ setHover(null); paint(); });
}

// ---------- 对比表 ----------
let gridSort={k:'cumulative_return',dir:-1};
function renderGrid(){
  const sel=$('stock').value;
  const rows=DATA.grid.slice().sort((a,b)=>{
    let va=a[gridSort.k], vb=b[gridSort.k];
    if(typeof va==='string') return gridSort.dir*va.localeCompare(vb);
    return gridSort.dir*(va-vb);
  });
  $('gridBody').innerHTML = rows.map(r=>{
    const cls = r.ts_code===sel ? ' class="sel"' : '';
    return `<tr${cls} data-code="${r.ts_code}" data-short="${r.short}" data-long="${r.long}">
      <td class="name">${r.name}</td>
      <td>${r.short}</td><td>${r.long}</td>
      <td class="${r.cumulative_return>=0?'pos':'neg'}">${fmtPct(r.cumulative_return)}</td>
      <td class="${r.annual_return>=0?'pos':'neg'}">${fmtPct(r.annual_return)}</td>
      <td class="neg">${fmtPct(r.max_drawdown)}</td>
      <td class="${r.sharpe>=1?'pos':'neg'}">${r.sharpe.toFixed(3)}</td>
      <td>${fmtPct(r.annual_vol)}</td>
      <td class="${r.buyhold_return>=0?'pos':'neg'}">${fmtPct(r.buyhold_return)}</td>
      <td>${r.n_trades}</td>
    </tr>`;
  }).join('');
  document.querySelectorAll('#gridBody tr').forEach(tr=>{
    tr.addEventListener('click', ()=>{
      $('stock').value=tr.dataset.code;
      $('short').value=tr.dataset.short;
      $('long').value=tr.dataset.long;
      render(); renderGrid();
    });
  });
}
document.querySelectorAll('#gridTable th').forEach(th=>{
  th.addEventListener('click', ()=>{
    const k=th.dataset.k;
    if(gridSort.k===k) gridSort.dir*=-1; else { gridSort.k=k; gridSort.dir=-1; }
    renderGrid();
  });
});

// ---------- 初始化 ----------
function init(){
  const sel=$('stock');
  DATA.order.forEach(code=>{
    const o=document.createElement('option');
    o.value=code; o.textContent=DATA.stocks[code].name+' ('+code+')';
    sel.appendChild(o);
  });
  sel.value='688981.SH';
  $('run').addEventListener('click', ()=>{ render(); renderGrid(); });
  bindHover($('priceChart'), v=>hoverMain=v, paintMain);
  bindHover($('equityChart'), v=>hoverEq=v, paintEq);
  window.addEventListener('resize', ()=>{ paintMain(); paintEq(); });
  render(); renderGrid();
}
init();
</script>
</body>
</html>
"""


def main():
    data = build_data()
    html = HTML.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT_PATH)
    print(f"已生成: {OUT_PATH}  ({size/1024:.0f} KB)")
    print(f"  股票数: {len(data['stocks'])}, 网格结果: {len(data['grid'])}")


if __name__ == "__main__":
    main()
