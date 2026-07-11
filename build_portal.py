# -*- coding: utf-8 -*-
"""
build_portal.py — 生成统一量化策略门户 index.html

整合：
  · 双均线策略（金叉/死叉）
  · 海龟策略（Donchian 通道 / ATR / 2×ATR 止损 / 金字塔加仓）
  · 策略指导（概念 + 指标 + 适用场景 + 心得）
  · 实时数据（JSONP 拉取东方财富公开行情 + CSV 导入兜底 + fetch_realtime.py 说明）

数据内嵌（无需联网），Canvas 手绘图表（无需外部库）。
JS 回测逻辑分别与 dual_ma_backtest.py / turtle_backtest.py 完全一致。
"""
import json
import os

import pandas as pd

SRC_CSV = "chip_stocks_daily.csv"
GRID_MA_JSON = "backtest_output/results.json"
GRID_TURTLE_JSON = "turtle_output/results.json"
OUT_HTML = "index.html"

META = {
    "trading_days": 252,
    "cost": 0.001,
    "init_capital": 100000.0,
    "risk_pct": 0.01,
    "atr_n": 20,
    "max_units": 4,
    "pyramid_step": 0.5,
    "pyramid_raise": 0.5,
    "stop_mult": 2.0,
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


def load_grid_ma(path):
    if not os.path.exists(path):
        return []
    g = json.load(open(path, encoding="utf-8"))
    for r in g:
        r["short"] = r.get("short")
        r["long"] = r.get("long")
    return g


def load_grid_turtle(path):
    if not os.path.exists(path):
        return []
    g = json.load(open(path, encoding="utf-8"))
    for r in g:
        r["entry"] = r.get("entry_n")
        r["exit"] = r.get("exit_n")
    return g


def main():
    order, stocks = build_data(SRC_CSV)
    data_obj = {"meta": META, "order": order, "stocks": stocks}
    data_json = json.dumps(data_obj, ensure_ascii=False)
    grid_ma = load_grid_ma(GRID_MA_JSON)
    grid_turtle = load_grid_turtle(GRID_TURTLE_JSON)
    grid_ma_json = json.dumps(grid_ma, ensure_ascii=False)
    grid_turtle_json = json.dumps(grid_turtle, ensure_ascii=False)

    html = TEMPLATE.replace("__DATA__", data_json) \
                   .replace("__GRID_MA__", grid_ma_json) \
                   .replace("__GRID_TURTLE__", grid_turtle_json)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"已生成 {OUT_HTML}（{len(html)//1024} KB），内嵌 {len(order)} 只股票、"
          f"双均线 {len(grid_ma)} 组、海龟 {len(grid_turtle)} 组对比。")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>量化策略门户 · 双均线 & 海龟 · 芯片股可视化分析</title>
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
.container{max-width:1340px;margin:0 auto;padding:14px 18px;}
.header{background:linear-gradient(135deg,#0d1117,#161b22);border:1px solid var(--bg4);border-radius:var(--radius);padding:16px 22px;margin-bottom:var(--gap);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;}
.header-left h1{font-size:21px;font-weight:700;background:linear-gradient(90deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.header-left .sub{font-size:12px;color:var(--text2);margin-top:3px;}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:var(--gap);}
.nav button{flex:1;min-width:120px;padding:11px 14px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:1px solid var(--bg4);background:var(--bg2);color:var(--text2);transition:all .15s;}
.nav button.active{background:var(--accent);color:#fff;border-color:var(--accent);}
.controls{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;background:var(--bg2);border:1px solid var(--bg4);border-radius:var(--radius);padding:14px 18px;margin-bottom:var(--gap);}
.field{display:flex;flex-direction:column;gap:4px;}
.field label{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;}
.field select,.field input{background:var(--bg3);border:1px solid var(--bg4);border-radius:6px;color:var(--text);font-size:14px;padding:7px 10px;min-width:96px;}
.btn{padding:9px 20px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;border:none;background:var(--accent);color:#fff;transition:filter .15s;}
.btn:hover{filter:brightness(1.15);}
.btn.ghost{background:var(--bg3);border:1px solid var(--bg4);color:var(--text);}
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
.pos{color:var(--up);} .neg{color:var(--down);}
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
.section h4{font-size:14px;margin:14px 0 6px;color:var(--yellow);}
.section p,.section li{color:var(--text);margin-bottom:8px;}
.section ul,.section ol{padding-left:22px;margin-bottom:10px;}
.section code{background:var(--bg3);padding:2px 6px;border-radius:4px;font-size:12px;color:var(--yellow);}
.note{font-size:12px;color:var(--text2);}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--text2);margin-top:8px;}
.legend span{display:inline-flex;align-items:center;gap:5px;}
.dot{width:10px;height:10px;border-radius:2px;display:inline-block;}
.footer{text-align:center;color:var(--text2);font-size:12px;padding:20px;}
.hl{color:var(--yellow);font-weight:600;}
.tabpane{display:none;}
.tabpane.active{display:block;}
.hidden{display:none !important;}
.rt-box{background:var(--bg3);border:1px solid var(--bg4);border-radius:8px;padding:14px 16px;margin-bottom:12px;}
.rt-status{font-size:13px;color:var(--text2);min-height:20px;margin-top:8px;}
.rt-status.ok{color:var(--green);} .rt-status.err{color:var(--red);}
textarea{width:100%;min-height:90px;background:var(--bg3);border:1px solid var(--bg4);border-radius:6px;color:var(--text);font-size:12px;padding:8px;font-family:monospace;}
pre{background:var(--bg3);border:1px solid var(--bg4);border-radius:8px;padding:12px 14px;overflow:auto;font-size:12px;color:var(--green);}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="header-left">
      <h1>量化策略门户 · 双均线 &amp; 海龟</h1>
      <div class="sub">趋势跟踪策略可视化分析 · 芯片股 7 只 · 初始资金 ¥100,000 · 单边成本 0.1% · 离线自包含</div>
    </div>
    <div class="header-right">
      <span style="width:8px;height:8px;background:var(--green);border-radius:50%;display:inline-block;margin-right:6px;"></span>
      <span style="font-size:12px;color:var(--text2);">本地数据 · 可实时刷新</span>
    </div>
  </div>

  <div class="nav">
    <button data-tab="ma" class="active">📈 双均线策略</button>
    <button data-tab="turtle">🐢 海龟策略</button>
    <button data-tab="guide">📚 策略指导</button>
    <button data-tab="rt">🔄 实时数据</button>
  </div>

  <!-- ===================== 双均线 ===================== -->
  <section class="tabpane active" id="maPane">
    <div class="controls">
      <div class="field"><label>股票</label><select id="maStock"></select></div>
      <div class="field"><label>短均线周期</label><input id="maShort" type="number" value="5" min="2" max="120" step="1"></div>
      <div class="field"><label>长均线周期</label><input id="maLong" type="number" value="15" min="3" max="250" step="1"></div>
      <div class="field"><label>单边成本(%)</label><input id="maCost" type="number" value="0.1" min="0" max="2" step="0.05"></div>
      <button class="btn" id="maRun">运行策略</button>
    </div>
    <div class="kpis" id="maKpis"></div>
    <div class="grid2">
      <div class="card">
        <h2>价格 · 长短均线 · 交易信号 <span class="tag" id="maTag1"></span></h2>
        <canvas id="maPriceChart" height="360"></canvas>
        <div class="legend">
          <span><i class="dot" style="background:#58a6ff;"></i>收盘价</span>
          <span><i class="dot" style="background:#e63946;"></i>短均线</span>
          <span><i class="dot" style="background:#2a9d8f;"></i>长均线</span>
          <span><i class="dot" style="background:#e63946;"></i>买入 ▲</span>
          <span><i class="dot" style="background:#2a9d8f;"></i>卖出 ▼</span>
        </div>
      </div>
      <div class="card">
        <h2>策略净值 vs 买入持有 <span class="tag" id="maTag2"></span></h2>
        <canvas id="maEquityChart" height="360"></canvas>
        <div class="legend"><span><i class="dot" style="background:#bc8cff;"></i>策略净值</span><span><i class="dot" style="background:#8b949e;"></i>买入持有(基准)</span></div>
      </div>
    </div>
    <div class="section">
      <h2>双均线 · 多股票 × 多周期 收益对比</h2>
      <p class="note">7 只芯片股在 5 组周期（MA5/15、MA5/20、MA10/30、MA10/60、MA20/60）下的回测结果。点击任意行可载入该股票与参数。当前所选股票以高亮显示。</p>
      <div class="table-wrap">
        <table id="maGridTable">
          <thead><tr>
            <th class="name" data-k="name">股票</th>
            <th data-k="short">短</th><th data-k="long">长</th>
            <th data-k="cumulative_return">累计回报</th>
            <th data-k="annual_return">年化收益</th>
            <th data-k="max_drawdown">最大回撤</th>
            <th data-k="sharpe">夏普</th>
            <th data-k="annual_vol">年化波动</th>
            <th data-k="buyhold_return">买入持有</th>
            <th data-k="n_trades">交易</th>
          </tr></thead>
          <tbody id="maGridBody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================== 海龟 ===================== -->
  <section class="tabpane" id="turtlePane">
    <div class="controls">
      <div class="field"><label>股票</label><select id="tStock"></select></div>
      <div class="field"><label>通道上轨(突破)</label><input id="tEntry" type="number" value="20" min="2" max="120" step="1"></div>
      <div class="field"><label>通道下轨(离场)</label><input id="tExit" type="number" value="10" min="2" max="120" step="1"></div>
      <div class="field"><label>ATR 周期</label><input id="tAtrn" type="number" value="20" min="2" max="60" step="1"></div>
      <div class="field"><label>单边成本(%)</label><input id="tCost" type="number" value="0.1" min="0" max="2" step="0.05"></div>
      <button class="btn" id="tRun">运行策略</button>
    </div>
    <div class="kpis" id="tKpis"></div>
    <div class="grid2">
      <div class="card">
        <h2>价格 · 高低点通道 · 交易信号 <span class="tag" id="tTag1"></span></h2>
        <canvas id="tPriceChart" height="360"></canvas>
        <div class="legend">
          <span><i class="dot" style="background:#58a6ff;"></i>收盘价</span>
          <span><i class="dot" style="background:#e63946;"></i>通道上轨</span>
          <span><i class="dot" style="background:#2a9d8f;"></i>通道下轨</span>
          <span><i class="dot" style="background:#e63946;"></i>买入 ▲</span>
          <span><i class="dot" style="background:#2a9d8f;"></i>卖出 ▼</span>
        </div>
      </div>
      <div class="card">
        <h2>平均真实波幅 ATR <span class="tag" id="tTag3"></span></h2>
        <canvas id="tAtrChart" height="360"></canvas>
        <div class="legend"><span><i class="dot" style="background:#d2991d;"></i>ATR（波动标尺）</span><span style="color:var(--text2)">通道突破时 ATR 越大 → 仓位越小</span></div>
      </div>
    </div>
    <div class="card" style="margin-bottom:var(--gap);">
      <h2>策略净值 vs 买入持有 <span class="tag" id="tTag2"></span></h2>
      <canvas id="tEquityChart" height="330"></canvas>
      <div class="legend"><span><i class="dot" style="background:#bc8cff;"></i>策略净值</span><span><i class="dot" style="background:#8b949e;"></i>买入持有(基准)</span></div>
    </div>
    <div class="section">
      <h2>海龟 · 多股票 × 多周期 收益对比</h2>
      <p class="note">7 只芯片股在「通道上轨∈{10,20,55} × 通道下轨∈{5,10,20}」共 63 组参数下的回测结果（ATR=20，成本 0.1%）。点击任意行可载入该股票与参数。</p>
      <div class="table-wrap">
        <table id="tGridTable">
          <thead><tr>
            <th class="name" data-k="name">股票</th>
            <th data-k="entry">上轨</th><th data-k="exit">下轨</th>
            <th data-k="cumulative_return">累计回报</th>
            <th data-k="annual_return">年化收益</th>
            <th data-k="max_drawdown">最大回撤</th>
            <th data-k="sharpe">夏普</th>
            <th data-k="annual_vol">年化波动</th>
            <th data-k="buyhold_return">买入持有</th>
            <th data-k="n_trades">交易</th>
            <th data-k="max_units">最大单位</th>
          </tr></thead>
          <tbody id="tGridBody"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================== 策略指导 ===================== -->
  <section class="tabpane" id="guidePane">
    <div class="section">
      <h2>一、量化策略基础指标（两策略通用）</h2>
      <ul>
        <li><span class="hl">累计回报 Cumulative Return</span>：期末净值/初始资金 − 1。</li>
        <li><span class="hl">最大回撤 MDD</span>：min(净值/历史最高点 − 1)，最坏潜在亏损，风控核心。</li>
        <li><span class="hl">夏普比率 Sharpe Ratio</span>：(日均超额收益 / 日均收益标准差) × √252，每单位风险的超额回报，&gt;1 良好、&gt;2 优秀。</li>
        <li><span class="hl">年化收益 / 年化波动率</span>：按 252 交易日年化，便于跨周期比较。</li>
        <li><span class="hl">买入持有对比</span>：同期"买了不动"的回报，判断策略是否创造价值。</li>
      </ul>

      <h2>二、双均线策略（Dual Moving Average）</h2>
      <h3>核心思想</h3>
      <p>用两条简单移动平均线（SMA）捕捉趋势惯性：<span class="hl">金叉</span>（短均线由下向上穿越长均线）视为多头启动→买入；<span class="hl">死叉</span>（短均线下穿长均线）视为趋势转弱→卖出。本实现为<b>多头-only</b>：金叉满仓、死叉清仓，成交放在<b>次日开盘</b>以规避前视偏差。</p>
      <h3>关键概念</h3>
      <ul>
        <li><span class="hl">短/长均线</span>：如 MA5（短期动能）与 MA15（中期趋势）。周期越短越灵敏、换手越多。</li>
        <li><span class="hl">前视偏差规避</span>：信号由当日收盘价算，真实成交在次日开盘（<code>action = signal.shift(1)</code>），否则用"未来信息"虚增收益。</li>
      </ul>
      <h3>中芯国际实证（MA5/15）</h3>
      <p>累计 <span class="pos">+75.63%</span>、年化 +82.46%、最大回撤 <span class="neg">−22.07%</span>、夏普 <span class="pos">1.489</span>、买入持有 +80.97%。<b>策略小幅跑输买入持有</b>——强趋势市典型特征；其价值在回撤可控、规则透明、可机械执行。</p>
      <h3>适用与心得</h3>
      <ul>
        <li>✅ 单边趋势市、主升浪；❌ 横盘震荡市（假突破反复止损）。</li>
        <li>寒武纪反例：买入持有 +183%，双均线 −0.68%（高波动单边暴涨被洗出）。</li>
        <li>参数过拟合是头号陷阱；成本与 MDD 控制优先；宜与量价/基本面结合。</li>
      </ul>

      <h2>三、海龟策略（Turtle Trading）</h2>
      <h3>核心思想</h3>
      <p>源自 1983 年 Richard Dennis 的实验：用完全机械的趋势跟踪规则训练学员，证明<b>优秀交易可被系统传授</b>。四大支柱：趋势跟踪、波动自适应仓位、截断亏损（2×ATR 止损）、让利润奔跑（金字塔加仓）。</p>
      <h3>关键概念</h3>
      <ul>
        <li><span class="hl">高低点通道 Donchian</span>：上轨 = 过去 N 日最高价，下轨 = 过去 M 日最低价；收盘突破上轨买入、跌破下轨卖出。</li>
        <li><span class="hl">平均真实波幅 ATR</span>：TR = max(最高−最低, |最高−昨收|, |最低−昨收|)，ATR 取 Wilder 平滑（RMA）。它同时决定<b>买多少</b>和<b>在哪止损</b>。</li>
        <li><span class="hl">ATR 头寸规模</span>：单位股数 =（权益×1%）/ ATR，波动大则少买，天然风险平价。</li>
        <li><span class="hl">2×ATR 止损</span>：价格跌到 入场价−2×ATR 即离场，单笔最大亏损约 2% 权益。</li>
        <li><span class="hl">金字塔加仓</span>：每上涨 0.5×ATR 加 1 单位，最多 4 单位，止损随成本上移。</li>
      </ul>
      <h3>中芯国际实证（通道 20/10 · ATR20）</h3>
      <p>累计 <span class="pos">+8.48%</span>、最大回撤 <span class="neg">−21.35%</span>、夏普 <span class="neg">0.414</span>、买入持有 +80.97%。海龟在高波动单边品种被 2×ATR 止损反复洗出、跑输买入持有，但其价值在<b>纪律可复制、回撤可控</b>。</p>
      <h3>适用与心得</h3>
      <ul>
        <li>✅ 中长线单边趋势市、商品/指数/强趋势个股；❌ 横盘震荡市、低流动性品种。</li>
        <li>长电科技最佳（E10/X20 +111%，夏普 1.91）；中微公司反例：买入持有 +156% 但海龟 −6.44%。</li>
        <li>波动自适应是精髓；止损是生命线；胜率常仅 40%，靠"截断亏损、让利润奔跑"生存；参数是情景而非真理。</li>
      </ul>
    </div>
  </section>

  <!-- ===================== 实时数据 ===================== -->
  <section class="tabpane" id="rtPane">
    <div class="section">
      <h2>实时行情获取</h2>
      <p class="note">网页内置<b>实时数据获取</b>能力：点击下方按钮，前端通过东方财富公开日线接口（JSONP，无需 token）拉取最新行情，合并到内存数据后即时重算策略。若离线或接口受限，可用 CSV 导入兜底，或本地运行 <code>fetch_realtime.py</code> 批量刷新。</p>

      <div class="rt-box">
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
          <button class="btn" id="rtCurrent">🔄 刷新当前股票（双均线所选）</button>
          <button class="btn ghost" id="rtAll">🔄 刷新全部 7 只</button>
          <span class="note">数据源：东方财富 push2his（公开接口）· 仅日线，非实时 tick</span>
        </div>
        <div class="rt-status" id="rtStatus">尚未刷新。点击上方按钮获取最新行情（需联网）。</div>
      </div>

      <div class="rt-box">
        <h4>方式二：粘贴 CSV 导入（离线兜底）</h4>
        <p class="note">格式：<code>ts_code,name,date,open,high,low,close</code> 每行一条，或东方财富导出的日线文本（日期,开,收,低,高）。将更新对应股票的内存数据。</p>
        <textarea id="rtCsv" placeholder="例如：&#10;688981.SH,中芯国际,20260710,108.5,110.2,107.0,111.0&#10;688981.SH,中芯国际,20260711,110.0,112.3,109.5,112.8"></textarea>
        <div style="margin-top:8px;"><button class="btn ghost" id="rtImport">导入并更新</button></div>
        <div class="rt-status" id="rtImportStatus"></div>
      </div>

      <h3>方式三：本地脚本批量刷新（推荐日常使用）</h3>
      <p class="note">在<strong>本地终端</strong>运行（沙箱可能无外网）。仅用 Python 标准库，无需安装依赖：</p>
      <pre># 拉取全部 7 只最新日线，更新 chip_stocks_daily.csv
python fetch_realtime.py

# 拉取后再重新生成本门户网页
python fetch_realtime.py --rebuild

# 只拉指定股票
python fetch_realtime.py --codes 688981.SH 603501.SH</pre>
      <p class="note">字段映射：东方财富 kline 接口返回 <code>日期,开,收,低,高</code>，脚本写入 <code>chip_stocks_daily.csv</code>（兼容 dual_ma_backtest.py / turtle_backtest.py 读取格式），随后 <code>python build_portal.py</code> 重新生成 index.html。</p>
    </div>
  </section>

  <div class="footer">数据区间 2025-07-01 ~ 2026-06-30 · 回测为教学演示，非投资建议 · 双均线/海龟 JS 回测已分别与 Python 在 35/63 组实验核对一致</div>
</div>

<script>
const DATA = __DATA__;
const GRID_MA = __GRID_MA__;
const GRID_TURTLE = __GRID_TURTLE__;
const $ = id => document.getElementById(id);

// ---------- 通用工具 ----------
function stdSample(arr){ if(arr.length<2) return 0; const m=arr.reduce((s,x)=>s+x,0)/arr.length; const v=arr.reduce((s,x)=>s+(x-m)*(x-m),0)/(arr.length-1); return Math.sqrt(v); }
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
function computeMetrics(equity, close, M){
  const n = equity.length;
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
  return {cumulative_return:cumRet, annual_return:annRet, max_drawdown:mdd, sharpe, annual_vol:volAnn, buyhold_return:buyhold, buyholdEq, final_equity:eq[n-1]};
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
function bindHover(cv, getLast, setHover, paint){
  let hover=null;
  cv.addEventListener('mousemove', e=>{ const rect=cv.getBoundingClientRect(); const x=e.clientX-rect.left;
    const padL=56, plotW=cv.clientWidth-padL-14; let idx=Math.round((x-padL)/plotW*(getLast().xLabels.length-1));
    idx=Math.max(0,Math.min(getLast().xLabels.length-1,idx)); hover=idx; paint(hover); });
  cv.addEventListener('mouseleave', ()=>{ hover=null; paint(null); });
}

// ================= 双均线 =================
function sma(arr,w){ const out=new Array(arr.length).fill(null); let sum=0;
  for(let i=0;i<arr.length;i++){ sum+=arr[i]; if(i>=w) sum-=arr[i-w]; if(i>=w-1) out[i]=sum/w; } return out; }
let maLast=null, maHover=null;
function maBacktest(code, short, long, costPct){
  const M=DATA.meta, st=DATA.stocks[code];
  const open=st.open, close=st.close, dates=st.dates, n=close.length;
  const s=sma(close,short), l=sma(close,long);
  const signal=new Array(n).fill(0);
  for(let i=1;i<n;i++){ if(s[i]==null||l[i]==null||s[i-1]==null||l[i-1]==null) continue;
    const diff=s[i]-l[i], pdiff=s[i-1]-l[i-1];
    if(pdiff<=0&&diff>0) signal[i]=1; else if(pdiff>=0&&diff<0) signal[i]=-1; }
  const action=new Array(n).fill(null);
  for(let i=0;i<n;i++) action[i]=(i>0)?signal[i-1]:null;
  const cost=costPct/100; let cash=M.init_capital, shares=0, pos=0;
  const equity=new Array(n); const buyPts=[], sellPts=[];
  for(let i=0;i<n;i++){ const act=action[i], o=open[i], c=close[i];
    if(act!==null&&act!==0){
      if(act===1&&pos===0){ shares=cash/(o*(1+cost)); cash=0; pos=1; buyPts.push({i,y:o}); }
      else if(act===-1&&pos===1){ cash=shares*o*(1-cost); shares=0; pos=0; sellPts.push({i,y:o}); }
    }
    equity[i]=cash+shares*c;
  }
  const m=computeMetrics(equity, close, M);
  m.n_trades = buyPts.length + sellPts.length;
  return {dates,close,maShort:s,maLong:l,buyPts,sellPts,equity,metrics:m};
}
function maRender(paint){
  const code=$('maStock').value;
  const short=parseInt($('maShort').value)||5, long=parseInt($('maLong').value)||15;
  const cost=parseFloat($('maCost').value)||0.1;
  if(short>=long){ alert('短均线周期必须小于长均线周期'); return; }
  const r=maBacktest(code, short, long, cost); const m=r.metrics;
  const kpis=[
    ['累计回报', fmtPct(m.cumulative_return), m.cumulative_return>=0?'pos':'neg', '买入持有 '+fmtPct(m.buyhold_return)],
    ['年化收益', fmtPct(m.annual_return), m.annual_return>=0?'pos':'neg', '期末 ¥'+m.final_equity.toLocaleString('zh-CN',{maximumFractionDigits:0})],
    ['最大回撤', fmtPct(m.max_drawdown), 'neg', '风控核心指标'],
    ['夏普比率', m.sharpe.toFixed(3), m.sharpe>=1?'pos':'neg', m.sharpe>=1?'良好':'偏低'],
    ['年化波动率', fmtPct(m.annual_vol), 'neg', '风险水平'],
    ['交易次数', m.n_trades, 'pos', '换手频率'],
  ];
  $('maKpis').innerHTML = kpis.map(k=>`<div class="kpi"><div class="k-label">${k[0]}</div><div class="k-val ${k[2]}">${k[1]}</div><div class="k-sub">${k[3]}</div></div>`).join('');
  $('maTag1').textContent = `${r.dates[0]} ~ ${r.dates[r.dates.length-1]}`;
  $('maTag2').textContent = `${DATA.stocks[code].name} MA${short}/${long}`;
  const ld = arr => arr.map(y=>({y}));
  maLast={xLabels:r.dates, lines:[
    {name:'收盘价',color:'#58a6ff',data:ld(r.close)},
    {name:'短均线',color:'#e63946',data:ld(r.maShort)},
    {name:'长均线',color:'#2a9d8f',data:ld(r.maLong)},
  ], scats:[
    {name:'买入',color:'#e63946',marker:'^',points:r.buyPts},
    {name:'卖出',color:'#2a9d8f',marker:'v',points:r.sellPts},
  ], eq:[
    {name:'策略净值',color:'#bc8cff',data:ld(r.equity)},
    {name:'买入持有',color:'#8b949e',data:ld(m.buyholdEq)},
  ]};
  if(paint) maPaint();
}
function maPaint(hover){
  if(!maLast) return;
  drawLineChart($('maPriceChart'), maLast, hover);
  drawLineChart($('maEquityChart'), {xLabels:maLast.xLabels, lines:maLast.eq}, hover);
}
let maSort={k:'cumulative_return',dir:-1};
function maRenderGrid(){
  const sel=$('maStock').value;
  const rows=GRID_MA.slice().sort((a,b)=>{ let va=a[maSort.k], vb=b[maSort.k];
    if(typeof va==='string') return maSort.dir*va.localeCompare(vb); return maSort.dir*(va-vb); });
  $('maGridBody').innerHTML = rows.map(r=>{ const cls=r.ts_code===sel?' class="sel"':'';
    return `<tr${cls} data-code="${r.ts_code}" data-short="${r.short}" data-long="${r.long}">
      <td class="name">${r.name}</td><td>${r.short}</td><td>${r.long}</td>
      <td class="${r.cumulative_return>=0?'pos':'neg'}">${fmtPct(r.cumulative_return)}</td>
      <td class="${r.annual_return>=0?'pos':'neg'}">${fmtPct(r.annual_return)}</td>
      <td class="neg">${fmtPct(r.max_drawdown)}</td>
      <td class="${r.sharpe>=1?'pos':'neg'}">${r.sharpe.toFixed(3)}</td>
      <td>${fmtPct(r.annual_vol)}</td>
      <td class="${r.buyhold_return>=0?'pos':'neg'}">${fmtPct(r.buyhold_return)}</td>
      <td>${r.n_trades}</td></tr>`; }).join('');
  document.querySelectorAll('#maGridBody tr').forEach(tr=>{ tr.addEventListener('click', ()=>{
    $('maStock').value=tr.dataset.code; $('maShort').value=tr.dataset.short; $('maLong').value=tr.dataset.long; maRender(true); maRenderGrid(); }); });
}
document.querySelectorAll('#maGridTable th').forEach(th=>{ th.addEventListener('click', ()=>{ const k=th.dataset.k;
  if(maSort.k===k) maSort.dir*=-1; else { maSort.k=k; maSort.dir=-1; } maRenderGrid(); }); });

// ================= 海龟 =================
function donchian(high, low, entryN, exitN){
  const n=high.length, upper=new Array(n).fill(null), lower=new Array(n).fill(null);
  for(let i=0;i<n;i++){
    if(i>=entryN){ let mx=-Infinity; for(let j=i-entryN;j<i;j++) if(high[j]>mx) mx=high[j]; upper[i]=mx; }
    if(i>=exitN){ let mn=Infinity; for(let j=i-exitN;j<i;j++) if(low[j]<mn) mn=low[j]; lower[i]=mn; }
  }
  return {upper, lower};
}
function atrSeries(high, low, close, n){
  const len=high.length, tr=new Array(len).fill(0);
  for(let i=0;i<len;i++){ if(i===0) tr[i]=high[i]-low[i]; else tr[i]=Math.max(high[i]-low[i], Math.abs(high[i]-close[i-1]), Math.abs(low[i]-close[i-1])); }
  const a=new Array(len).fill(NaN);
  for(let i=0;i<len;i++){ if(i===n){ let s=0; for(let k=0;k<n;k++) s+=tr[k]; a[i]=s/n; } else if(i>n) a[i]=(a[i-1]*(n-1)+tr[i])/n; }
  return a;
}
let tLast=null, tHover=null;
function turtleBacktest(code, entryN, exitN, atrN, costPct){
  const M=DATA.meta, st=DATA.stocks[code];
  const open=st.open, high=st.high, low=st.low, close=st.close, dates=st.dates, n=close.length;
  const {upper, lower}=donchian(high, low, entryN, exitN);
  const aFull=atrSeries(high, low, close, atrN);
  const atrShift=new Array(n).fill(NaN);
  for(let i=0;i<n;i++) atrShift[i]=(i>=1)?aFull[i-1]:NaN;
  const enterSig=new Array(n).fill(0), exitSig=new Array(n).fill(0);
  for(let i=0;i<n;i++){ if(i>=1 && upper[i-1]!=null && close[i-1]>upper[i-1]) enterSig[i]=1;
    if(i>=1 && lower[i-1]!=null && close[i-1]<lower[i-1]) exitSig[i]=1; }
  const cost=costPct/100; let cash=M.init_capital, shares=0, units=0;
  let entry1=null, N1=null, stop=null, lastAdd=null;
  const equity=new Array(n); const buyPts=[], sellPts=[]; let maxUnits=0;
  for(let i=0;i<n;i++){
    const o=open[i], c=close[i], lo=low[i], hi=high[i], a=atrShift[i];
    const prevEq=(i>0)?equity[i-1]:M.init_capital;
    if(units>0 && stop!=null && lo<=stop){ cash=cash+shares*stop*(1-cost); sellPts.push({i,y:stop}); shares=0; units=0; entry1=null; N1=null; stop=null; lastAdd=null; equity[i]=cash; continue; }
    if(units>0 && exitSig[i]===1){ cash=cash+shares*o*(1-cost); sellPts.push({i,y:o}); shares=0; units=0; entry1=null; N1=null; stop=null; lastAdd=null; equity[i]=cash; continue; }
    if(units===0 && enterSig[i]===1 && a!=null && !isNaN(a)){
      const N=a, unitRisk=M.risk_pct*prevEq, su=unitRisk/N, costAmt=su*o*(1+cost);
      if(su>0 && costAmt<=cash){ shares=su; cash-=costAmt; units=1; entry1=o; N1=N; lastAdd=o; stop=o-M.stop_mult*N; buyPts.push({i,y:o}); maxUnits=Math.max(maxUnits,units); equity[i]=cash+shares*c; continue; }
    }
    if(units>0 && units<M.max_units && N1!=null && hi>=lastAdd+M.pyramid_step*N1){
      const N=(a!=null && !isNaN(a))?a:N1, unitRisk=M.risk_pct*prevEq, su=unitRisk/N, costAmt=su*o*(1+cost);
      if(su>0 && costAmt<=cash){ shares+=su; cash-=costAmt; units++; lastAdd=o; stop=entry1-(M.stop_mult-M.pyramid_raise*(units-1))*N1; buyPts.push({i,y:o}); maxUnits=Math.max(maxUnits,units); }
    }
    equity[i]=cash+shares*c;
  }
  const m=computeMetrics(equity, close, M);
  m.n_trades=buyPts.length+sellPts.length; m.max_units=maxUnits;
  return {dates,close,upper,lower,atr:aFull,buyPts,sellPts,equity,metrics:m};
}
function turtleRender(paint){
  const code=$('tStock').value;
  const entry=parseInt($('tEntry').value)||20, exit=parseInt($('tExit').value)||10;
  const atrn=parseInt($('tAtrn').value)||20, cost=parseFloat($('tCost').value)||0.1;
  if(entry<=exit){ alert('通道上轨(突破)周期必须大于下轨(离场)周期'); return; }
  const r=turtleBacktest(code, entry, exit, atrn, cost); const m=r.metrics;
  const kpis=[
    ['累计回报', fmtPct(m.cumulative_return), m.cumulative_return>=0?'pos':'neg', '买入持有 '+fmtPct(m.buyhold_return)],
    ['年化收益', fmtPct(m.annual_return), m.annual_return>=0?'pos':'neg', '期末 ¥'+m.final_equity.toLocaleString('zh-CN',{maximumFractionDigits:0})],
    ['最大回撤', fmtPct(m.max_drawdown), 'neg', '风控核心指标'],
    ['夏普比率', m.sharpe.toFixed(3), m.sharpe>=1?'pos':'neg', m.sharpe>=1?'良好':'偏低'],
    ['年化波动率', fmtPct(m.annual_vol), 'neg', '风险水平'],
    ['最大单位', m.max_units+' / '+DATA.meta.max_units, 'pos', '交易 '+m.n_trades+' 次'],
  ];
  $('tKpis').innerHTML = kpis.map(k=>`<div class="kpi"><div class="k-label">${k[0]}</div><div class="k-val ${k[2]}">${k[1]}</div><div class="k-sub">${k[3]}</div></div>`).join('');
  $('tTag1').textContent = `${r.dates[0]} ~ ${r.dates[r.dates.length-1]}`;
  $('tTag2').textContent = `${DATA.stocks[code].name} 通道 ${entry}/${exit} · ATR${atrn}`;
  $('tTag3').textContent = `ATR 周期 ${atrn}`;
  const ld = arr => arr.map(y=>({y}));
  tLast={xLabels:r.dates, lines:[
    {name:'收盘价',color:'#58a6ff',data:ld(r.close)},
    {name:'通道上轨',color:'#e63946',data:ld(r.upper)},
    {name:'通道下轨',color:'#2a9d8f',data:ld(r.lower)},
  ], scats:[
    {name:'买入',color:'#e63946',marker:'^',points:r.buyPts},
    {name:'卖出',color:'#2a9d8f',marker:'v',points:r.sellPts},
  ], atr:[{name:'ATR',color:'#d2991d',data:ld(r.atr)}],
    eq:[{name:'策略净值',color:'#bc8cff',data:ld(r.equity)},
        {name:'买入持有',color:'#8b949e',data:ld(m.buyholdEq)}]};
  if(paint) turtlePaint();
}
function turtlePaint(hover){
  if(!tLast) return;
  drawLineChart($('tPriceChart'), tLast, hover);
  drawLineChart($('tAtrChart'), {xLabels:tLast.xLabels, lines:tLast.atr}, hover);
  drawLineChart($('tEquityChart'), {xLabels:tLast.xLabels, lines:tLast.eq}, hover);
}
let tSort={k:'cumulative_return',dir:-1};
function turtleRenderGrid(){
  const sel=$('tStock').value;
  const rows=GRID_TURTLE.slice().sort((a,b)=>{ let va=a[tSort.k], vb=b[tSort.k];
    if(typeof va==='string') return tSort.dir*va.localeCompare(vb); return tSort.dir*(va-vb); });
  $('tGridBody').innerHTML = rows.map(r=>{ const cls=r.ts_code===sel?' class="sel"':'';
    return `<tr${cls} data-code="${r.ts_code}" data-entry="${r.entry}" data-exit="${r.exit}">
      <td class="name">${r.name}</td><td>${r.entry}</td><td>${r.exit}</td>
      <td class="${r.cumulative_return>=0?'pos':'neg'}">${fmtPct(r.cumulative_return)}</td>
      <td class="${r.annual_return>=0?'pos':'neg'}">${fmtPct(r.annual_return)}</td>
      <td class="neg">${fmtPct(r.max_drawdown)}</td>
      <td class="${r.sharpe>=1?'pos':'neg'}">${r.sharpe.toFixed(3)}</td>
      <td>${fmtPct(r.annual_vol)}</td>
      <td class="${r.buyhold_return>=0?'pos':'neg'}">${fmtPct(r.buyhold_return)}</td>
      <td>${r.n_trades}</td><td>${r.max_units}</td></tr>`; }).join('');
  document.querySelectorAll('#tGridBody tr').forEach(tr=>{ tr.addEventListener('click', ()=>{
    $('tStock').value=tr.dataset.code; $('tEntry').value=tr.dataset.entry; $('tExit').value=tr.dataset.exit; turtleRender(true); turtleRenderGrid(); }); });
}
document.querySelectorAll('#tGridTable th').forEach(th=>{ th.addEventListener('click', ()=>{ const k=th.dataset.k;
  if(tSort.k===k) tSort.dir*=-1; else { tSort.k=k; tSort.dir=-1; } turtleRenderGrid(); }); });

// ================= 实时数据 (JSONP) =================
function emSecid(ts_code){ const [code,mkt]=ts_code.split('.'); return (mkt==='SH'?'1.':'0.')+code; }
function emJsonp(url, cbName, onDone){
  window[cbName]=function(d){ try{ onDone(null,d); } finally { delete window[cbName]; } };
  const sep = url.indexOf('?')>=0?'&':'?';
  const s=document.createElement('script');
  s.src=url+sep+'cb='+cbName;
  s.onerror=function(){ delete window[cbName]; onDone(new Error('network'), null); };
  document.body.appendChild(s);
}
function fetchRealtime(code, onDone){
  const secid=emSecid(code);
  const url=`https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=${secid}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55&klt=101&fqt=0&beg=20250101&end=20500101`;
  const cb='__emcb'+Date.now()+Math.floor(Math.random()*1e6);
  emJsonp(url, cb, (err,d)=>{
    if(err||!d||!d.data||!d.data.klines){ onDone(err||new Error('空数据'), null); return; }
    const rows=d.data.klines.map(ln=>{ const p=ln.split(','); return {date:p[0].replace(/-/g,''), open:parseFloat(p[1]), close:parseFloat(p[2]), low:parseFloat(p[3]), high:parseFloat(p[4])}; });
    onDone(null, rows);
  });
}
function mergeStock(code, rows){
  const st=DATA.stocks[code]; if(!st) return 0;
  const idx={}; st.dates.forEach((d,i)=>idx[d]=i);
  let added=0;
  rows.forEach(r=>{
    if(idx[r.date]!=null){ const i=idx[r.date]; st.open[i]=r.open; st.high[i]=r.high; st.low[i]=r.low; st.close[i]=r.close; }
    else { idx[r.date]=st.dates.length; st.dates.push(r.date); st.open.push(r.open); st.high.push(r.high); st.low.push(r.low); st.close.push(r.close); added++; }
  });
  // 重排序保证时间递增
  const ord=st.dates.map((d,i)=>i).sort((a,b)=>st.dates[a]<st.dates[b]?-1:1);
  st.dates=ord.map(i=>st.dates[i]); st.open=ord.map(i=>st.open[i]); st.high=ord.map(i=>st.high[i]); st.low=ord.map(i=>st.low[i]); st.close=ord.map(i=>st.close[i]);
  return added;
}
function refreshStock(code, label, done){
  const status=$('rtStatus');
  status.className='rt-status'; status.textContent=`正在拉取 ${label} ...`;
  fetchRealtime(code, (err, rows)=>{
    if(err){ status.className='rt-status err'; status.textContent='✗ '+label+' 拉取失败：'+(err.message||err)+'（可能离线或接口受限，请用 CSV 导入或 fetch_realtime.py）'; done&&done(); return; }
    const added=mergeStock(code, rows);
    status.className='rt-status ok';
    status.textContent=`✓ ${label} 已更新（共 ${DATA.stocks[code].dates.length} 条，新增 ${added}）。切换回对应策略 Tab 即可看到最新行情回测。`;
    done&&done();
  });
}
$('rtCurrent').addEventListener('click', ()=>{ const code=$('maStock').value; refreshStock(code, DATA.stocks[code].name+' ('+code+')', ()=>{ maRender(false); }); });
$('rtAll').addEventListener('click', ()=>{
  const status=$('rtStatus'); status.className='rt-status'; status.textContent='正在刷新全部 7 只 ...';
  let pending=DATA.order.length, okc=0, errc=0;
  DATA.order.forEach((code,i)=>{
    setTimeout(()=>{ refreshStock(code, DATA.stocks[code].name, ()=>{
      pending--; if(status.className.indexOf('ok')>=0) okc++; if(status.className.indexOf('err')>=0) errc++;
      if(pending===0){ status.textContent=`✓ 全部完成：成功 ${DATA.order.length-errc} 只，失败 ${errc} 只。切换策略 Tab 查看最新行情。`; }
    }); }, i*250);
  });
});
$('rtImport').addEventListener('click', ()=>{
  const txt=$('rtCsv').value.trim(); const out=$('rtImportStatus');
  if(!txt){ out.className='rt-status err'; out.textContent='请先粘贴 CSV 数据。'; return; }
  let added=0, parsed=0;
  txt.split(/\n+/).forEach(line=>{
    line=line.trim(); if(!line) return;
    const p=line.split(/[,\t]/);
    let code,name,date,o,h,l,c;
    if(p.length>=7){ code=p[0]; name=p[1]; date=p[2]; o=+p[3]; h=+p[4]; l=+p[5]; c=+p[6]; }
    else if(p.length>=5){ date=p[0].replace(/-/g,''); o=+p[1]; c=+p[2]; l=+p[3]; h=+p[4]; code=Object.keys(DATA.stocks)[0]; name=DATA.stocks[code].name; }
    else return;
    if(!DATA.stocks[code]) { out.className='rt-status err'; out.textContent='✗ 未知股票代码 '+code; return; }
    added+=mergeStock(code, [{date,open:o,high:h,low:l,close:c}]); parsed++;
  });
  if(parsed>0){ out.className='rt-status ok'; out.textContent=`✓ 导入 ${parsed} 行，新增/更新 ${added} 条。切换策略 Tab 查看回测。`; maRender(false); }
  else { out.className='rt-status err'; out.textContent='✗ 未能解析任何有效行。'; }
});

// ================= Tab 切换 =================
function showTab(name){
  document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active', b.dataset.tab===name));
  document.querySelectorAll('.tabpane').forEach(p=>p.classList.toggle('active', p.id===name+'Pane'));
  if(name==='ma') maPaint(null);
  else if(name==='turtle') turtlePaint(null);
}
document.querySelectorAll('.nav button').forEach(b=>{ b.addEventListener('click', ()=>showTab(b.dataset.tab)); });

// ================= 初始化 =================
function init(){
  ['maStock','tStock'].forEach(id=>{ const sel=$(id); DATA.order.forEach(code=>{ const o=document.createElement('option'); o.value=code; o.textContent=DATA.stocks[code].name+' ('+code+')'; sel.appendChild(o); }); });
  $('maStock').value='688981.SH'; $('tStock').value='688981.SH';
  $('maRun').addEventListener('click', ()=>{ maRender(true); });
  $('tRun').addEventListener('click', ()=>{ turtleRender(true); });
  bindHover($('maPriceChart'), ()=>maLast, null, maPaint);
  bindHover($('maEquityChart'), ()=>maLast, null, maPaint);
  bindHover($('tPriceChart'), ()=>tLast, null, turtlePaint);
  bindHover($('tAtrChart'), ()=>tLast, null, turtlePaint);
  bindHover($('tEquityChart'), ()=>tLast, null, turtlePaint);
  window.addEventListener('resize', ()=>{ maPaint(null); turtlePaint(null); });
  maRender(false); maRenderGrid();
  turtleRender(false); turtleRenderGrid();
  showTab('ma');
}
init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
