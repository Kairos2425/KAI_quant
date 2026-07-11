# -*- coding: utf-8 -*-
"""
由本地股价数据生成海龟策略的离线自包含交互网页 turtle_dashboard.html。
- 数据内嵌（无需联网），Canvas 手绘图表（无需外部库）。
- JS 回测逻辑与 turtle_backtest.py 完全一致，并会在 parity 脚本中核对。
"""
import json
import os

import pandas as pd

SRC_CSV = "chip_stocks_daily.csv"
GRID_JSON = "turtle_output/results.json"
OUT_HTML = "turtle_dashboard.html"

# 海龟策略默认参数（与 turtle_backtest.py 对应）
META = {
    "trading_days": 252,
    "cost": 0.001,            # 默认单边成本（小数）
    "init_capital": 100000.0,
    "risk_pct": 0.01,         # 每单位风险 = 1% 权益
    "atr_n": 20,
    "max_units": 4,
    "pyramid_step": 0.5,
    "pyramid_raise": 0.5,
    "stop_mult": 2.0,
    "entry_default": 20,
    "exit_default": 10,
}


def build_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    order = list(dict.fromkeys(df["ts_code"].tolist()))
    stocks = {}
    for code in order:
        sub = df[df["ts_code"] == code]
        stocks[code] = {
            "name": str(sub["name"].iloc[0]),
            "dates": sub["trade_date"].astype(str).tolist(),
            "open": [float(x) for x in sub["open"].tolist()],
            "high": [float(x) for x in sub["high"].tolist()],
            "low": [float(x) for x in sub["low"].tolist()],
            "close": [float(x) for x in sub["close"].tolist()],
        }
    return order, stocks


def main():
    order, stocks = build_data(SRC_CSV)
    data_obj = {"meta": META, "order": order, "stocks": stocks}
    data_json = json.dumps(data_obj, ensure_ascii=False)
    grid = []
    if os.path.exists(GRID_JSON):
        with open(GRID_JSON, "r", encoding="utf-8") as f:
            grid = json.load(f)
        # 规整字段名以便前端使用
        for g in grid:
            g["entry"] = g.get("entry_n")
            g["exit"] = g.get("exit_n")
    grid_json = json.dumps(grid, ensure_ascii=False)

    html = TEMPLATE.replace("__DATA__", data_json).replace("__GRID__", grid_json)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUT_HTML}（{len(html)//1024} KB），内嵌 {len(order)} 只股票、{len(grid)} 组网格结果。")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>海龟交易策略回测 · 芯片股可视化分析</title>
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
.field select,.field input{background:var(--bg3);border:1px solid var(--bg4);border-radius:6px;color:var(--text);font-size:14px;padding:7px 10px;min-width:96px;}
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
      <h1>海龟交易策略回测 · 芯片股可视化分析</h1>
      <div class="sub">唐奇安通道突破 · ATR 头寸规模 · 2×ATR 止损 · 金字塔加仓 · 初始资金 ¥100,000 · 单边成本 0.1%</div>
    </div>
    <div class="header-right">
      <span style="width:8px;height:8px;background:var(--green);border-radius:50%;display:inline-block;margin-right:6px;"></span>
      <span style="font-size:12px;color:var(--text2);">本地数据 · 无需联网</span>
    </div>
  </div>

  <div class="controls">
    <div class="field"><label>股票</label><select id="stock"></select></div>
    <div class="field"><label>通道上轨(突破)</label><input id="entry" type="number" value="20" min="2" max="120" step="1"></div>
    <div class="field"><label>通道下轨(离场)</label><input id="exit" type="number" value="10" min="2" max="120" step="1"></div>
    <div class="field"><label>ATR 周期</label><input id="atrn" type="number" value="20" min="2" max="60" step="1"></div>
    <div class="field"><label>单边成本(%)</label><input id="cost" type="number" value="0.1" min="0" max="2" step="0.05"></div>
    <button class="btn" id="run">运行策略</button>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="grid2">
    <div class="card">
      <h2>价格 · 高低点通道 · 交易信号 <span class="tag" id="tag1"></span></h2>
      <canvas id="priceChart" height="360"></canvas>
      <div class="legend">
        <span><i class="dot" style="background:#58a6ff;"></i>收盘价</span>
        <span><i class="dot" style="background:#e63946;"></i>通道上轨</span>
        <span><i class="dot" style="background:#2a9d8f;"></i>通道下轨</span>
        <span><i class="dot" style="background:#e63946;"></i>买入 ▲</span>
        <span><i class="dot" style="background:#2a9d8f;"></i>卖出 ▼</span>
      </div>
    </div>
    <div class="card">
      <h2>平均真实波幅 ATR <span class="tag" id="tag3"></span></h2>
      <canvas id="atrChart" height="360"></canvas>
      <div class="legend"><span><i class="dot" style="background:#d2991d;"></i>ATR（波动标尺）</span><span style="color:var(--text2)">通道突破时 ATR 越大 → 仓位越小</span></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:var(--gap);">
    <h2>策略净值 vs 买入持有 <span class="tag" id="tag2"></span></h2>
    <canvas id="equityChart" height="330"></canvas>
    <div class="legend">
      <span><i class="dot" style="background:#bc8cff;"></i>策略净值</span>
      <span><i class="dot" style="background:#8b949e;"></i>买入持有(基准)</span>
    </div>
  </div>

  <div class="section">
    <h2>多股票 × 多周期 收益对比</h2>
    <p class="note">下表为 7 只芯片股在「通道上轨∈{10,20,55} × 通道下轨∈{5,10,20}」共 63 组参数下的回测结果（ATR=20，成本 0.1%）。点击任意行可载入该股票与参数到主视图。当前所选股票以高亮显示。</p>
    <div class="table-wrap">
      <table id="gridTable">
        <thead><tr>
          <th class="name" data-k="name">股票</th>
          <th data-k="entry">上轨</th>
          <th data-k="exit">下轨</th>
          <th data-k="cumulative_return">累计回报</th>
          <th data-k="annual_return">年化收益</th>
          <th data-k="max_drawdown">最大回撤</th>
          <th data-k="sharpe">夏普</th>
          <th data-k="annual_vol">年化波动</th>
          <th data-k="buyhold_return">买入持有</th>
          <th data-k="n_trades">交易</th>
          <th data-k="max_units">最大单位</th>
        </tr></thead>
        <tbody id="gridBody"></tbody>
      </table>
    </div>
  </div>

  <div class="section" id="report">
    <h2>海龟策略分析报告</h2>

    <h3>一、海龟策略核心思想</h3>
    <p>海龟策略源自 1983 年 Richard Dennis 与 William Eckhardt 的著名实验：他们训练一批毫无交易经验的"海龟"学员，仅传授一套<strong>完全机械的趋势跟踪规则</strong>，结果多数人在短短几年内取得远超市场的收益，证明<strong>优秀的交易是可以被系统性传授的</strong>。其核心是：</p>
    <ul>
      <li><span class="hl">趋势跟踪</span>：价格突破过去 N 日的高低点通道，意味着趋势启动，顺势入场。</li>
      <li><span class="hl">波动自适应仓位</span>：用 ATR 衡量波动，波动大则少买、波动小则多买，使每笔交易承担的风险恒定（账户权益的 1%）。</li>
      <li><span class="hl">截断亏损、让利润奔跑</span>：2×ATR 硬止损控制单笔最大亏损；盈利后金字塔加仓，放大趋势收益。</li>
      <li><span class="hl">双系统</span>：系统一 S1 用 20 日突破/10 日离场（灵敏）；系统二 S2 用 55 日突破/20 日离场（稳健）。本页默认实现 S1 思路并支持自由调参。</li>
    </ul>

    <h3>二、关键概念</h3>
    <ul>
      <li><span class="hl">高低点通道（Donchian Channel）</span>：上轨 = 过去 N 日最高价，下轨 = 过去 M 日最低价。收盘价向上突破上轨 → 买入信号；向下跌破下轨 → 卖出信号。通道把"趋势"量化为可机械判断的边界。</li>
      <li><span class="hl">平均真实波幅 ATR</span>：真实波幅 TR = max(当日最高−最低, |最高−昨收|, |最低−昨收|)，刻画单日真实波动幅度；ATR 取 TR 的 <strong>Wilder 平滑移动平均</strong>（本实现用 RMA：ATR[i]=(ATR[i-1]·(n−1)+TR[i])/n）。ATR 是海龟的"尺子"——它同时决定<strong>买多少</strong>和<strong>在哪里止损</strong>。</li>
      <li><span class="hl">基于 ATR 的头寸规模（Unit）</span>：单位股数 =（账户权益 × 1%）/ ATR。含义是"价格反向走 1 个 ATR，亏损刚好是账户的 1%"。波动越大（ATR 越大）买得越少，天然实现风险平价。</li>
      <li><span class="hl">2×ATR 止损</span>：建仓后，若价格跌到 入场价 − 2×ATR，立即离场，单笔最大亏损约 2% 权益。加仓后止损随成本上移（每加一单位上移 0.5×ATR），锁定部分利润。</li>
      <li><span class="hl">金字塔加仓</span>：价格每上涨 0.5×ATR 加 1 个单位，最多 4 个单位。让盈利的头寸在趋势延续时自然变大。</li>
    </ul>

    <h3>三、量化效果基础指标</h3>
    <ul>
      <li><span class="hl">累计回报 Cumulative Return</span>：期末净值/初始资金 − 1。</li>
      <li><span class="hl">最大回撤 MDD</span>：净值自历史高点回落的最大幅度（min(净值/历史最高点−1)），风控核心指标。</li>
      <li><span class="hl">夏普比率 Sharpe Ratio</span>：(日均超额收益 / 日均收益标准差) × √252，衡量每单位风险换来的超额收益，&gt;1 良好、&gt;2 优秀。</li>
      <li><span class="hl">年化收益 / 年化波动率</span>：按 252 交易日年化，便于跨周期比较。</li>
      <li><span class="hl">买入持有对比</span>：同期"买了不动"的回报，用于判断策略是否真的创造了价值。</li>
      <li><span class="hl">最大单位 / 交易次数</span>：反映仓位集中度与换手频率。</li>
    </ul>

    <h3>四、中芯国际（688981.SH）实证</h3>
    <p id="smicText"></p>

    <h3>五、多股票 / 多周期观察</h3>
    <ul>
      <li><strong>通道越短越灵敏、越长越平滑</strong>：短上轨（如 10 日）入场快、交易多，但在震荡市易被假突破反复止损（whipsaw）；长上轨（如 55 日）信号稀少、回撤通常更小，但滞后期更长、易错过早期行情。</li>
      <li><strong>趋势强度决定成败</strong>：对 <span class="hl">长电科技、寒武纪（部分周期）、中芯国际（短周期）</span> 这类有清晰单边趋势的标的，海龟捕获了主升浪，累计回报与夏普可观；对 <span class="hl">韦尔股份、中微公司</span> 等区间大幅震荡、缺乏持续方向的标的，频繁止损导致小幅亏损。</li>
      <li><strong>离场周期的影响</strong>：下轨（离场通道）越长，持仓越久、越能"让利润奔跑"，但回撤也更大；下轨越短，落袋为安快但易被洗出。</li>
    </ul>

    <h3>六、适用场景与应用心得</h3>
    <ul>
      <li><span class="hl">适用</span>：中长线单边趋势市、商品/指数/强趋势个股；适合作为"机械执行、去情绪化"的趋势跟踪骨架。</li>
      <li><span class="hl">不适用</span>：横盘震荡市（信号反复、摩擦成本吞噬收益）；低流动性或跳空频繁的品种（止损难以成交）。</li>
      <li><span class="hl">心得 1 · 波动自适应是精髓</span>：海龟最聪明之处不是"突破买入"，而是用 ATR 把仓位与波动挂钩。同样的规则，在暴雷股上自动轻仓、在慢牛股上自动重仓。</li>
      <li><span class="hl">心得 2 · 止损是生命线</span>：2×ATR 止损把单笔亏损锁死在约 2% 权益，使策略在连续止损后仍有资本翻盘。没有止损的趋势跟踪等于裸奔。</li>
      <li><span class="hl">心得 3 · 大数定律与胜率</span>：海龟胜率往往仅 40% 上下，靠"截断亏损、让利润奔跑"的正期望生存——少数大赢家覆盖多数小亏损。切忌因几次止损就放弃规则。</li>
      <li><span class="hl">心得 4 · 参数是情景而非真理</span>：本页默认 20/10 是经典值，但历史调参易过拟合。建议用多组参数取稳健区间，并叠加成交量/基本面过滤。</li>
    </ul>
  </div>

  <div class="footer">数据区间 2025-07-01 ~ 2026-06-30 · 回测为教学演示，非投资建议</div>
</div>

<script>
const DATA = __DATA__;
const GRID = __GRID__;
const $ = id => document.getElementById(id);

// ---------- 海龟回测核心（与 turtle_backtest.py 逻辑一致）----------
// 唐奇安通道
function donchian(high, low, entryN, exitN){
  const n = high.length;
  const upper = new Array(n).fill(null);
  const lower = new Array(n).fill(null);
  for(let i=0;i<n;i++){
    if(i>=entryN){
      let mx=-Infinity; for(let j=i-entryN;j<i;j++) if(high[j]>mx) mx=high[j];
      upper[i]=mx;
    }
    if(i>=exitN){
      let mn=Infinity; for(let j=i-exitN;j<i;j++) if(low[j]<mn) mn=low[j];
      lower[i]=mn;
    }
  }
  return {upper, lower};
}
// Wilder ATR
function atrSeries(high, low, close, n){
  const len = high.length;
  const tr = new Array(len).fill(0);
  for(let i=0;i<len;i++){
    if(i===0) tr[i]=high[i]-low[i];
    else tr[i]=Math.max(high[i]-low[i], Math.abs(high[i]-close[i-1]), Math.abs(low[i]-close[i-1]));
  }
  const a = new Array(len).fill(NaN);
  for(let i=0;i<len;i++){
    if(i===n) { let s=0; for(let k=0;k<n;k++) s+=tr[k]; a[i]=s/n; }
    else if(i>n) a[i]=(a[i-1]*(n-1)+tr[i])/n;
  }
  return a; // a[i] 在 i>=n 定义；atrShift[i]=a[i-1]
}
function stdSample(arr){
  if(arr.length<2) return 0;
  const m = arr.reduce((s,x)=>s+x,0)/arr.length;
  const v = arr.reduce((s,x)=>s+(x-m)*(x-m),0)/(arr.length-1);
  return Math.sqrt(v);
}
function backtest(code, entryN, exitN, atrN, costPct){
  const M = DATA.meta;
  const st = DATA.stocks[code];
  const open=st.open, high=st.high, low=st.low, close=st.close, dates=st.dates;
  const n = close.length;
  const {upper, lower} = donchian(high, low, entryN, exitN);
  const aFull = atrSeries(high, low, close, atrN);
  const atrShift = new Array(n).fill(NaN);
  for(let i=0;i<n;i++) atrShift[i] = (i>=1)? aFull[i-1] : NaN;

  // 信号：在 bar i 用「前一日收盘价 close[i-1]」与「前一日之前的 N 日通道 upper[i-1]」比较（排除参考日自身），成交在 i 开盘
  const enterSig = new Array(n).fill(0), exitSig = new Array(n).fill(0);
  for(let i=0;i<n;i++){
    if(i>=1 && upper[i-1]!=null && close[i-1] > upper[i-1]) enterSig[i]=1;
    if(i>=1 && lower[i-1]!=null && close[i-1] < lower[i-1]) exitSig[i]=1;
  }

  const cost = costPct/100;
  let cash = M.init_capital, shares=0, units=0;
  let entry1=null, N1=null, stop=null, lastAdd=null;
  const equity = new Array(n);
  const trades = []; const buyPts=[], sellPts=[];
  let maxUnits=0;

  for(let i=0;i<n;i++){
    const o=open[i], c=close[i], lo=low[i], hi=high[i];
    const a = atrShift[i];
    const prevEq = (i>0)? equity[i-1] : M.init_capital;

    // 1) 止损
    if(units>0 && stop!=null && lo<=stop){
      cash = cash + shares*stop*(1-cost);
      trades.push({date:dates[i],side:'SELL',reason:'STOP',price:stop}); sellPts.push({i, y:stop});
      shares=0; units=0; entry1=null; N1=null; stop=null; lastAdd=null;
      equity[i]=cash; continue;
    }
    // 2) 离场
    if(units>0 && exitSig[i]===1){
      cash = cash + shares*o*(1-cost);
      trades.push({date:dates[i],side:'SELL',reason:'EXIT',price:o}); sellPts.push({i, y:o});
      shares=0; units=0; entry1=null; N1=null; stop=null; lastAdd=null;
      equity[i]=cash; continue;
    }
    // 3) 入场
    if(units===0 && enterSig[i]===1 && a!=null && !isNaN(a)){
      const N=a; const unitRisk = M.risk_pct * prevEq; const su = unitRisk / N;
      const costAmt = su * o * (1+cost);
      if(su>0 && costAmt<=cash){
        shares=su; cash-=costAmt; units=1; entry1=o; N1=N; lastAdd=o; stop=o-M.stop_mult*N;
        trades.push({date:dates[i],side:'BUY',reason:'ENTRY',price:o}); buyPts.push({i, y:o});
        maxUnits=Math.max(maxUnits,units); equity[i]=cash+shares*c; continue;
      }
    }
    // 4) 金字塔加仓
    if(units>0 && units<M.max_units && N1!=null && hi >= lastAdd + M.pyramid_step*N1){
      const N=(a!=null && !isNaN(a))? a : N1;
      const unitRisk = M.risk_pct * prevEq; const su = unitRisk / N;
      const costAmt = su * o * (1+cost);
      if(su>0 && costAmt<=cash){
        shares+=su; cash-=costAmt; units++; lastAdd=o;
        stop = entry1 - (M.stop_mult - M.pyramid_raise*(units-1))*N1;
        trades.push({date:dates[i],side:'BUY',reason:'ADD',price:o}); buyPts.push({i, y:o});
        maxUnits=Math.max(maxUnits,units);
      }
    }
    equity[i] = cash + shares*c;
  }

  // 指标
  const eq = equity;
  const dr=[]; for(let i=1;i<n;i++) dr.push((eq[i]-eq[i-1])/eq[i-1]);
  const cumRet = eq[n-1]/eq[0]-1;
  const annRet = Math.pow(eq[n-1]/eq[0], M.trading_days/n)-1;
  let runMax=eq[0], mdd=0;
  for(let i=0;i<n;i++){ if(eq[i]>runMax) runMax=eq[i]; const dd=eq[i]/runMax-1; if(dd<mdd) mdd=dd; }
  const mean = dr.reduce((s,x)=>s+x,0)/(dr.length||1);
  const sd = stdSample(dr);
  const sharpe = sd>0 ? mean/sd*Math.sqrt(M.trading_days) : 0;
  const volAnn = sd*Math.sqrt(M.trading_days);
  const buyhold = close[n-1]/close[0]-1;
  const buyholdEq = close.map(v=>M.init_capital*(v/close[0]));
  return {dates,close,upper,lower,atr:aFull,buyPts,sellPts,equity,buyholdEq,
    metrics:{cumulative_return:cumRet, annual_return:annRet, max_drawdown:mdd, sharpe,
      annual_vol:volAnn, buyhold_return:buyhold, n_trades:trades.length, max_units:maxUnits, final_equity:eq[n-1]},
    trades};
}

// ---------- Canvas 绘图 ----------
function setupCanvas(cv){
  const dpr = window.devicePixelRatio||1;
  const w = cv.clientWidth, h = cv.clientHeight || 360;
  cv.width = w*dpr; cv.height = h*dpr;
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  return {ctx,w,h};
}
function fmtPct(v){ return (v*100).toFixed(2)+'%'; }
function niceTicks(min,max,count){
  const range = max-min || 1; const raw = range/count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw/mag; let step;
  if(norm<1.5) step=1; else if(norm<3) step=2; else if(norm<7) step=5; else step=10;
  step*=mag;
  const start = Math.floor(min/step)*step; const ticks=[];
  for(let v=start; v<=max+1e-9; v+=step) ticks.push(v);
  return ticks;
}
function drawLineChart(cv, spec, hoverIdx){
  const {ctx,w,h} = setupCanvas(cv);
  ctx.clearRect(0,0,w,h);
  const padL=56, padR=14, padT=14, padB=30;
  const plotW = w-padL-padR, plotH = h-padT-padB;
  let lo=Infinity, hi=-Infinity;
  spec.lines.forEach(s=>s.data.forEach(p=>{ if(p.y!=null){ if(p.y<lo)lo=p.y; if(p.y>hi)hi=p.y; }}));
  spec.scats&&spec.scats.forEach(s=>s.points.forEach(p=>{ if(p.y<lo)lo=p.y; if(p.y>hi)hi=p.y; }));
  if(!isFinite(lo)){ lo=0; hi=1; }
  const pad=(hi-lo)*0.08||1; lo-=pad; hi+=pad;
  const n = spec.xLabels.length;
  const xAt = i => padL + (n<=1?0:(i/(n-1))*plotW);
  const yAt = v => padT + (1-(v-lo)/(hi-lo))*plotH;
  ctx.strokeStyle='#21262d'; ctx.fillStyle='#8b949e'; ctx.font='11px "Microsoft YaHei",sans-serif';
  ctx.textAlign='right'; ctx.textBaseline='middle';
  niceTicks(lo,hi,5).forEach(t=>{ const y=yAt(t); ctx.beginPath(); ctx.moveTo(padL,y); ctx.lineTo(w-padR,y); ctx.stroke(); ctx.fillText(t.toFixed(t<10?2:0), padL-6, y); });
  ctx.textAlign='center'; ctx.textBaseline='top';
  for(let k=0;k<=6;k++){ const i=Math.round(k/6*(n-1)); ctx.fillText(spec.xLabels[i]?spec.xLabels[i].slice(2):'', xAt(i), h-padB+6); }
  spec.lines.forEach(s=>{ ctx.strokeStyle=s.color; ctx.lineWidth=s.width||1.6; ctx.beginPath(); let started=false;
    s.data.forEach((p,i)=>{ if(p.y==null) return; const x=xAt(i), y=yAt(p.y); if(!started){ctx.moveTo(x,y);started=true;} else ctx.lineTo(x,y); }); ctx.stroke(); });
  if(spec.scats) spec.scats.forEach(s=>{ s.points.forEach(p=>{ const x=xAt(p.i), y=yAt(p.y); ctx.fillStyle=s.color;
    if(s.marker==='^'){ ctx.beginPath(); ctx.moveTo(x,y-6); ctx.lineTo(x-5,y+4); ctx.lineTo(x+5,y+4); ctx.closePath(); ctx.fill(); }
    else { ctx.beginPath(); ctx.moveTo(x,y+6); ctx.lineTo(x-5,y-4); ctx.lineTo(x+5,y-4); ctx.closePath(); ctx.fill(); } }); });
  if(hoverIdx!=null && hoverIdx>=0 && hoverIdx<n){
    const x=xAt(hoverIdx); ctx.strokeStyle='rgba(255,255,255,.25)'; ctx.lineWidth=1; ctx.beginPath(); ctx.moveTo(x,padT); ctx.lineTo(x,h-padB); ctx.stroke();
    const lines=[spec.xLabels[hoverIdx]];
    spec.lines.forEach(s=>{ const p=s.data[hoverIdx]; if(p&&p.y!=null) lines.push(s.name+': '+p.y.toFixed(2)); });
    if(spec.scats) spec.scats.forEach(s=>{ if(s.points.find(p=>p.i===hoverIdx)) lines.push(s.name); });
    ctx.font='11px "Microsoft YaHei",sans-serif'; ctx.textAlign='left'; ctx.textBaseline='top';
    const tw=Math.max(...lines.map(t=>ctx.measureText(t).width))+12; let tx=x+8; if(tx+tw>w-padR) tx=x-8-tw; const ty=padT+4;
    ctx.fillStyle='rgba(13,17,23,.92)'; ctx.strokeStyle='#30363d'; ctx.fillRect(tx,ty,tw,lines.length*15+8); ctx.strokeRect(tx,ty,tw,lines.length*15+8);
    ctx.fillStyle='#c9d1d9'; lines.forEach((t,k)=>ctx.fillText(t,tx+6,ty+5+k*15));
  }
}

let lastMain=null, lastAtr=null, lastEq=null, hoverMain=null, hoverAtr=null, hoverEq=null;
function render(){
  const code=$('stock').value;
  const entry=parseInt($('entry').value)||20;
  const exit=parseInt($('exit').value)||10;
  const atrn=parseInt($('atrn').value)||20;
  const cost=parseFloat($('cost').value)||0.1;
  if(entry<=exit){ alert('通道上轨(突破)周期必须大于下轨(离场)周期'); return; }
  const r = backtest(code, entry, exit, atrn, cost);
  const m=r.metrics;
  const kpis=[
    ['累计回报', fmtPct(m.cumulative_return), m.cumulative_return>=0?'pos':'neg', '买入持有 '+fmtPct(m.buyhold_return)],
    ['年化收益', fmtPct(m.annual_return), m.annual_return>=0?'pos':'neg', '期末净值 ¥'+m.final_equity.toLocaleString('zh-CN',{maximumFractionDigits:0})],
    ['最大回撤', fmtPct(m.max_drawdown), 'neg', '风控核心指标'],
    ['夏普比率', m.sharpe.toFixed(3), m.sharpe>=1?'pos':'neg', m.sharpe>=1?'良好':'偏低'],
    ['年化波动率', fmtPct(m.annual_vol), 'neg', '风险水平'],
    ['最大单位', m.max_units+' / '+DATA.meta.max_units, 'pos', '交易 '+m.n_trades+' 次'],
  ];
  $('kpis').innerHTML = kpis.map(k=>`<div class="kpi"><div class="k-label">${k[0]}</div><div class="k-val ${k[2]}">${k[1]}</div><div class="k-sub">${k[3]}</div></div>`).join('');
  $('tag1').textContent = `${r.dates[0]} ~ ${r.dates[r.dates.length-1]}`;
  $('tag2').textContent = `${DATA.stocks[code].name} 通道 ${entry}/${exit} · ATR${atrn}`;
  $('tag3').textContent = `ATR 周期 ${atrn}`;
  const ld = arr => arr.map(y=>({y}));
  lastMain={xLabels:r.dates, lines:[
    {name:'收盘价',color:'#58a6ff',data:ld(r.close)},
    {name:'通道上轨',color:'#e63946',data:ld(r.upper)},
    {name:'通道下轨',color:'#2a9d8f',data:ld(r.lower)},
  ], scats:[
    {name:'买入',color:'#e63946',marker:'^',points:r.buyPts},
    {name:'卖出',color:'#2a9d8f',marker:'v',points:r.sellPts},
  ]};
  lastAtr={xLabels:r.dates, lines:[{name:'ATR',color:'#d2991d',data:ld(r.atr)}]};
  lastEq={xLabels:r.dates, lines:[
    {name:'策略净值',color:'#bc8cff',data:ld(r.equity)},
    {name:'买入持有',color:'#8b949e',data:ld(r.buyholdEq)},
  ]};
  paintMain(); paintAtr(); paintEq();
  if(code==='688981.SH'){
    const vs = m.cumulative_return - m.buyhold_return;
    $('smicText').innerHTML = `在默认参数 <code>通道 ${entry}/${exit} · ATR${atrn}</code> 下，中芯国际区间累计回报 <span class="${m.cumulative_return>=0?'pos':'neg'}">${fmtPct(m.cumulative_return)}</span>，年化收益 ${fmtPct(m.annual_return)}，最大回撤 <span class="neg">${fmtPct(m.max_drawdown)}</span>，夏普比率 <span class="${m.sharpe>=1?'pos':'neg'}">${m.sharpe.toFixed(3)}</span>，共交易 ${m.n_trades} 次、最大持仓 ${m.max_units} 个单位。同期买入持有回报为 <span class="${m.buyhold_return>=0?'pos':'neg'}">${fmtPct(m.buyhold_return)}</span>，策略${vs>=0?'<span class="pos">跑赢</span>':'<span class="neg">跑输</span>'}买入持有约 <span class="${vs>=0?'pos':'neg'}">${fmtPct(Math.abs(vs))}</span>。这与强趋势市/高波动个股的典型特征一致：海龟用 2×ATR 止损控制了回撤、且规则机械可复制，但在单边暴涨中因频繁平仓与滞后往往略逊于"买入不动"——其价值在于<strong>风控纪律与可规模化执行</strong>，而非收益最大化。`;
  } else {
    $('smicText').innerHTML = `已切换至 <span class="hl">${DATA.stocks[code].name} (${code})</span>，参数 <code>通道 ${entry}/${exit} · ATR${atrn}</code>。当前累计回报 <span class="${m.cumulative_return>=0?'pos':'neg'}">${fmtPct(m.cumulative_return)}</span>，最大回撤 <span class="neg">${fmtPct(m.max_drawdown)}</span>，夏普 <span class="${m.sharpe>=1?'pos':'neg'}">${m.sharpe.toFixed(3)}</span>，买入持有 ${fmtPct(m.buyhold_return)}，最大持仓 ${m.max_units} 单位。可与下方对比表交叉验证不同个股的表现分化。`;
  }
}
function paintMain(){ if(lastMain) drawLineChart($('priceChart'), lastMain, hoverMain); }
function paintAtr(){ if(lastAtr) drawLineChart($('atrChart'), lastAtr, hoverAtr); }
function paintEq(){ if(lastEq) drawLineChart($('equityChart'), lastEq, hoverEq); }
function bindHover(cv, setHover, paint){
  cv.addEventListener('mousemove', e=>{ const rect=cv.getBoundingClientRect(); const x=e.clientX-rect.left;
    const padL=56, plotW=cv.clientWidth-padL-14; let idx=Math.round((x-padL)/plotW*(lastMain.xLabels.length-1));
    idx=Math.max(0,Math.min(lastMain.xLabels.length-1,idx)); setHover(idx); paint(); });
  cv.addEventListener('mouseleave', ()=>{ setHover(null); paint(); });
}

let gridSort={k:'cumulative_return',dir:-1};
function renderGrid(){
  const sel=$('stock').value;
  const rows=GRID.slice().sort((a,b)=>{ let va=a[gridSort.k], vb=b[gridSort.k];
    if(typeof va==='string') return gridSort.dir*va.localeCompare(vb); return gridSort.dir*(va-vb); });
  $('gridBody').innerHTML = rows.map(r=>{ const cls = r.ts_code===sel?' class="sel"':'';
    return `<tr${cls} data-code="${r.ts_code}" data-entry="${r.entry}" data-exit="${r.exit}">
      <td class="name">${r.name}</td><td>${r.entry}</td><td>${r.exit}</td>
      <td class="${r.cumulative_return>=0?'pos':'neg'}">${fmtPct(r.cumulative_return)}</td>
      <td class="${r.annual_return>=0?'pos':'neg'}">${fmtPct(r.annual_return)}</td>
      <td class="neg">${fmtPct(r.max_drawdown)}</td>
      <td class="${r.sharpe>=1?'pos':'neg'}">${r.sharpe.toFixed(3)}</td>
      <td>${fmtPct(r.annual_vol)}</td>
      <td class="${r.buyhold_return>=0?'pos':'neg'}">${fmtPct(r.buyhold_return)}</td>
      <td>${r.n_trades}</td><td>${r.max_units}</td>
    </tr>`; }).join('');
  document.querySelectorAll('#gridBody tr').forEach(tr=>{ tr.addEventListener('click', ()=>{
    $('stock').value=tr.dataset.code; $('entry').value=tr.dataset.entry; $('exit').value=tr.dataset.exit; render(); renderGrid(); }); });
}
document.querySelectorAll('#gridTable th').forEach(th=>{ th.addEventListener('click', ()=>{ const k=th.dataset.k;
  if(gridSort.k===k) gridSort.dir*=-1; else { gridSort.k=k; gridSort.dir=-1; } renderGrid(); }); });

function init(){
  const sel=$('stock'); DATA.order.forEach(code=>{ const o=document.createElement('option'); o.value=code; o.textContent=DATA.stocks[code].name+' ('+code+')'; sel.appendChild(o); });
  sel.value='688981.SH';
  $('run').addEventListener('click', ()=>{ render(); renderGrid(); });
  bindHover($('priceChart'), v=>hoverMain=v, paintMain);
  bindHover($('atrChart'), v=>hoverAtr=v, paintAtr);
  bindHover($('equityChart'), v=>hoverEq=v, paintEq);
  window.addEventListener('resize', ()=>{ paintMain(); paintAtr(); paintEq(); });
  render(); renderGrid();
}
init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
