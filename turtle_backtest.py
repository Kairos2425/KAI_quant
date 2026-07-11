# -*- coding: utf-8 -*-
"""
海龟交易策略 (Turtle Trading Strategy) 回测
============================================
核心要素：
  - Donchian 通道（高低点通道）：上轨 = N 日最高价，下轨 = M 日最低价
  - ATR（平均真实波幅，Wilder 平滑）：衡量波动率的标尺
  - 基于 ATR 的头寸规模（Unit）：每单位风险 = 账户权益的 1% / ATR
  - 2×ATR 止损：价格跌破 入场价 - 2×ATR 时强制离场
  - 金字塔加仓：价格每上涨 0.5×ATR 加 1 单位，最多 4 单位

前视偏差规避：信号由当日收盘价计算，实际成交在「次日开盘价」执行
（action = signal.shift(1)），与 dual_ma_backtest.py 一致。

用法：
  python turtle_backtest.py --code 688981.SH --entry 20 --exit 10
  python turtle_backtest.py --grid
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------- 全局参数 ----------------
TRADING_DAYS = 252
RISK_FREE_ANNUAL = 0.0
COST_RATE = 0.001          # 单边交易成本 0.1%
ATR_N = 20                 # ATR 计算周期
RISK_PCT = 0.01            # 每单位风险 = 1% 账户权益
MAX_UNITS = 4              # 单一标的最多 4 个单位
PYRAMID_STEP = 0.5         # 每上涨 0.5×N 加仓一次
PYRAMID_RAISE = 0.5        # 每加仓一次，整体止损上移 0.5×N
STOP_MULT = 2.0            # 止损距离 = 2×N
INIT_CAPITAL = 100000.0
OUT_DIR = "turtle_output"
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"

try:
    from matplotlib import font_manager as fm
    if os.path.exists(FONT_PATH):
        fm.fontManager.addfont(FONT_PATH)
        plt.rcParams["font.family"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


# ---------------- 数据加载 ----------------
def load_data(csv_path):
    """读取本地已存储的股价数据，按股票+日期排序。"""
    df = pd.read_csv(csv_path)
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    return df


# ---------------- Donchian 高低点通道 ----------------
def compute_donchian(sub, entry_n, exit_n):
    """计算唐奇安通道。
    upper = entry_n 日最高价（上轨/突破线）
    lower = exit_n 日最低价（下轨/离场线）
    均 shift(1) 以避免前视偏差。
    """
    sub = sub.copy()
    sub["upper"] = sub["high"].rolling(entry_n).max().shift(1)
    sub["lower"] = sub["low"].rolling(exit_n).min().shift(1)
    return sub


# ---------------- ATR（平均真实波幅，Wilder 平滑） ----------------
def compute_atr(sub, n=ATR_N):
    """真实波幅 TR = max(H-L, |H-C_prev|, |L-C_prev|)。
    ATR 使用 Wilder 平滑（RMA）：
      ATR[n]   = mean(TR[0..n-1])                  # 种子
      ATR[i]   = (ATR[i-1]*(n-1) + TR[i]) / n      # i>n
    atr_shift = ATR.shift(1)，次日可用。
    """
    sub = sub.copy()
    high = sub["high"].values
    low = sub["low"].values
    close = sub["close"].values
    tr = np.empty(len(sub), dtype=float)
    for i in range(len(sub)):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(high[i] - low[i],
                        abs(high[i] - close[i - 1]),
                        abs(low[i] - close[i - 1]))
    atr = np.full(len(sub), np.nan)
    for i in range(len(sub)):
        if i == n:
            atr[i] = np.mean(tr[0:n])
        elif i > n:
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    sub["tr"] = tr
    sub["atr"] = atr
    sub["atr_shift"] = sub["atr"].shift(1)
    return sub


# ---------------- 交易信号 ----------------
def gen_signals(sub, entry_n, exit_n):
    """生成突破信号（基于收盘价，次日开盘成交）。
    enter_sig[i] = 1  若 前一日收盘价 > 前一日上轨（向上突破）
    exit_sig[i]  = 1  若 前一日收盘价 < 前一日下轨（向下突破离场）
    """
    sub = compute_donchian(sub, entry_n, exit_n)
    sub = compute_atr(sub, ATR_N)
    upper = sub["upper"].values
    lower = sub["lower"].values
    close = sub["close"].values
    n = len(sub)
    enter_sig = np.zeros(n, dtype=int)
    exit_sig = np.zeros(n, dtype=int)
    # 前视偏差规避：在 bar i 用「前一日收盘价 close[i-1]」与「前一日之前的 N 日通道
    # upper[i-1]」比较（upper[i-1] 已排除参考日自身，即截至 i-2 的 N 日最高价），成交在 i 开盘。
    for i in range(1, n):
        if not np.isnan(upper[i - 1]) and close[i - 1] > upper[i - 1]:
            enter_sig[i] = 1
        if not np.isnan(lower[i - 1]) and close[i - 1] < lower[i - 1]:
            exit_sig[i] = 1
    sub["enter_sig"] = enter_sig
    sub["exit_sig"] = exit_sig
    return sub


# ---------------- 回测（多头 + ATR 头寸 + 止损 + 金字塔） ----------------
def backtest(sub, cost=COST_RATE, init_capital=INIT_CAPITAL,
             risk_pct=RISK_PCT, max_units=MAX_UNITS,
             pyramid_step=PYRAMID_STEP, pyramid_raise=PYRAMID_RAISE,
             stop_mult=STOP_MULT):
    """模拟交易并回测。返回 (sub, trades, max_units_seen)。"""
    sub = sub.copy()
    n = len(sub)
    openp = sub["open"].values
    highp = sub["high"].values
    lowp = sub["low"].values
    closep = sub["close"].values
    enter = sub["enter_sig"].values.astype(int)
    exit_sig = sub["exit_sig"].values.astype(int)
    atr_shift = sub["atr_shift"].values

    cash = init_capital
    shares = 0.0
    units = 0
    entry1 = None
    N1 = None
    stop_price = None
    last_add = None
    equity = np.zeros(n)
    max_units_seen = 0
    trades = []

    for i in range(n):
        o = openp[i]
        c = closep[i]
        lo = lowp[i]
        hi = highp[i]
        a = atr_shift[i] if i < len(atr_shift) else np.nan
        prev_equity = equity[i - 1] if i > 0 else init_capital

        # 1) 止损（日内触发，优先级最高）
        if units > 0 and stop_price is not None and lo <= stop_price:
            cash = cash + shares * stop_price * (1 - cost)
            trades.append({"side": "SELL", "reason": "STOP", "price": float(stop_price), "i": int(i)})
            shares = 0.0
            units = 0
            entry1 = None
            N1 = None
            stop_price = None
            last_add = None
            equity[i] = cash
            continue

        # 2) 离场信号（跌破下轨，次日开盘离场）
        if units > 0 and exit_sig[i] == 1:
            cash = cash + shares * o * (1 - cost)
            trades.append({"side": "SELL", "reason": "EXIT", "price": float(o), "i": int(i)})
            shares = 0.0
            units = 0
            entry1 = None
            N1 = None
            stop_price = None
            last_add = None
            equity[i] = cash
            continue

        # 3) 入场信号（突破上轨，次日开盘建首仓）
        if units == 0 and enter[i] == 1 and a is not None and not np.isnan(a):
            N = float(a)
            unit_risk = risk_pct * prev_equity
            shares_unit = unit_risk / N
            cost_amt = shares_unit * o * (1 + cost)
            if shares_unit > 0 and cost_amt <= cash:
                shares = shares_unit
                cash -= cost_amt
                units = 1
                entry1 = o
                N1 = N
                last_add = o
                stop_price = o - stop_mult * N
                trades.append({"side": "BUY", "reason": "ENTRY", "price": float(o), "i": int(i)})
                max_units_seen = max(max_units_seen, units)
                equity[i] = cash + shares * c
                continue

        # 4) 金字塔加仓（每上涨 0.5×N1 加 1 单位，最多 max_units）
        if units > 0 and units < max_units and N1 is not None and hi >= last_add + pyramid_step * N1:
            N = float(a) if (a is not None and not np.isnan(a)) else N1
            unit_risk = risk_pct * prev_equity
            shares_unit = unit_risk / N
            cost_amt = shares_unit * o * (1 + cost)
            if shares_unit > 0 and cost_amt <= cash:
                shares += shares_unit
                cash -= cost_amt
                units += 1
                last_add = o
                stop_price = entry1 - (stop_mult - pyramid_raise * (units - 1)) * N1
                trades.append({"side": "BUY", "reason": "ADD", "price": float(o), "i": int(i)})
                max_units_seen = max(max_units_seen, units)

        equity[i] = cash + shares * c

    sub["equity"] = equity
    return sub, trades, int(max_units_seen)


# ---------------- 量化指标 ----------------
def compute_metrics(sub, init_capital=INIT_CAPITAL):
    eq = sub["equity"].values.astype(float)
    close = sub["close"].values.astype(float)
    n = len(eq)
    dr = np.diff(eq) / eq[:-1]
    dr = dr[~np.isnan(dr)]
    cum = eq[-1] / eq[0] - 1
    ann = (eq[-1] / eq[0]) ** (TRADING_DAYS / n) - 1

    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1
    mdd = float(dd.min())

    mean = float(dr.mean()) if len(dr) > 0 else 0.0
    sd = float(dr.std(ddof=1)) if len(dr) > 1 else 0.0
    sharpe = mean / sd * np.sqrt(TRADING_DAYS) if sd > 0 else 0.0
    ann_vol = sd * np.sqrt(TRADING_DAYS)
    buyhold = close[-1] / close[0] - 1

    return {
        "cumulative_return": float(cum),
        "annual_return": float(ann),
        "max_drawdown": mdd,
        "sharpe": float(sharpe),
        "annual_vol": float(ann_vol),
        "buyhold_return": float(buyhold),
        "final_equity": float(eq[-1]),
    }


# ---------------- 可视化 ----------------
def plot_strategy(sub, ts_code, name, entry_n, exit_n, trades, out_path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    x = sub["trade_date"].astype(str).values
    ax1.plot(x, sub["close"].values, label="收盘价", color="#1f77b4", lw=1.2)
    ax1.plot(x, sub["upper"].values, label=f"{entry_n}日通道上轨", color="#d62728", ls="--", lw=1.0)
    ax1.plot(x, sub["lower"].values, label=f"{exit_n}日通道下轨", color="#2ca02c", ls="--", lw=1.0)

    for t in trades:
        i = t["i"]
        if t["side"] == "BUY":
            ax1.scatter(x[i], t["price"], marker="^", color="#d62728", s=90, zorder=5)
        else:
            ax1.scatter(x[i], t["price"], marker="v", color="#2ca02c", s=90, zorder=5)

    ax1.set_title(f"{name} ({ts_code})  海龟策略  通道 {entry_n}/{exit_n}  买卖信号")
    ax1.set_ylabel("价格")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(alpha=0.3)

    ax2.plot(x, sub["equity"].values, label="策略净值", color="#9467bd", lw=1.4)
    ax2.plot(x, sub["equity"].values[0] * (sub["close"].values / sub["close"].values[0]),
             label="买入持有", color="#7f7f7f", ls=":", lw=1.2)
    ax2.set_ylabel("净值")
    ax2.set_xlabel("交易日")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(alpha=0.3)

    # 每隔一段显示 xtick，避免过密
    step = max(1, len(x) // 12)
    ax2.set_xticks(range(0, len(x), step))
    ax2.set_xticklabels(x[::step], rotation=45, ha="right", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


# ---------------- 串联：单只回测 ----------------
def run_one(df, ts_code, entry_n=20, exit_n=10, atr_n=ATR_N,
            cost=COST_RATE, init_capital=INIT_CAPITAL, plot=True):
    sub0 = df[df["ts_code"] == ts_code].copy()
    if sub0.empty:
        raise ValueError(f"无该股票数据: {ts_code}")
    name = str(sub0["name"].iloc[0])
    sub = gen_signals(sub0, entry_n, exit_n)
    sub, trades, max_units = backtest(sub, cost=cost, init_capital=init_capital)
    metrics = compute_metrics(sub, init_capital=init_capital)
    metrics.update({
        "ts_code": ts_code, "name": name,
        "entry_n": entry_n, "exit_n": exit_n, "atr_n": atr_n,
        "cost": cost, "init_capital": init_capital,
        "n_trades": len(trades),
        "n_buy": sum(1 for t in trades if t["side"] == "BUY"),
        "n_sell": sum(1 for t in trades if t["side"] == "SELL"),
        "max_units": max_units,
    })
    if plot:
        os.makedirs(OUT_DIR, exist_ok=True)
        png = os.path.join(OUT_DIR, f"{ts_code}_e{entry_n}_x{exit_n}.png")
        plot_strategy(sub, ts_code, name, entry_n, exit_n, trades, png)
        metrics["plot"] = png
        with open(os.path.join(OUT_DIR, f"{ts_code}_e{entry_n}_x{exit_n}_trades.json"),
                  "w", encoding="utf-8") as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
    return metrics


# ---------------- 网格：多股票 × 多周期 ----------------
def run_grid(df, entry_list, exit_list, codes=None, atr_n=ATR_N,
             cost=COST_RATE, init_capital=INIT_CAPITAL):
    if codes is None:
        codes = sorted(df["ts_code"].unique())
    results = []
    for code in codes:
        for en in entry_list:
            for xn in exit_list:
                try:
                    m = run_one(df, code, en, xn, atr_n=atr_n,
                                cost=cost, init_capital=init_capital, plot=False)
                    results.append(m)
                    print(f"  {m['name']:6} E{en:2}/X{xn:2}  累计={m['cumulative_return']*100:7.2f}%  "
                          f"夏普={m['sharpe']:6.3f}  回撤={m['max_drawdown']*100:7.2f}%  交易={m['n_trades']}")
                except Exception as e:
                    print(f"  skip {code} E{en}/X{xn}: {e}")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


# ---------------- CLI ----------------
def main():
    p = argparse.ArgumentParser(description="海龟交易策略回测")
    p.add_argument("--code", default="688981.SH", help="股票代码")
    p.add_argument("--entry", type=int, default=20, help="通道上轨周期(突破)")
    p.add_argument("--exit", type=int, default=10, help="通道下轨周期(离场)")
    p.add_argument("--atr", type=int, default=ATR_N, help="ATR 周期")
    p.add_argument("--cost", type=float, default=COST_RATE, help="单边交易成本")
    p.add_argument("--grid", action="store_true", help="运行多股多周期网格")
    p.add_argument("--data", default="chip_stocks_daily.csv", help="数据文件")
    args = p.parse_args()

    df = load_data(args.data)
    if args.grid:
        results = run_grid(df,
                           entry_list=[10, 20, 55],
                           exit_list=[5, 10, 20],
                           atr_n=args.atr, cost=args.cost)
        print(f"\n网格回测完成：{len(results)} 组 -> {OUT_DIR}/results.json")
    else:
        m = run_one(df, args.code, args.entry, args.exit,
                    atr_n=args.atr, cost=args.cost, plot=True)
        print(json.dumps(m, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
