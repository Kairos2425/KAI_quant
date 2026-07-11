# -*- coding: utf-8 -*-
"""
双均线（Dual Moving Average）策略回测脚本
============================================
功能：
  1) 加载已存储的股价数据（chip_stocks_daily.csv）
  2) 设定短/长均线周期，计算均线
  3) 计算金叉（买入）/死叉（卖出）交易信号
  4) 绘制可视化图形：股价 + 长短均线 + 买卖信号标记
  5) 模拟交易与回测，计算核心量化指标
        - 累计回报 Cumulative Return
        - 最大回撤 Max Drawdown (MDD)
        - 夏普比率 Sharpe Ratio
        - （附）年化收益、交易次数、买入持有对比

执行方式：
  python dual_ma_backtest.py                 # 默认：中芯国际 短5/长15
  python dual_ma_backtest.py --code 688012.SH --short 10 --long 30
  python dual_ma_backtest.py --grid          # 跑多组周期对比并生成 results.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # 无界面绘图
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ---------- 中文字体（Windows SimHei）----------
_FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"
if os.path.exists(_FONT_PATH):
    font_manager.fontManager.addfont(_FONT_PATH)
    _FONT_NAME = font_manager.FontProperties(fname=_FONT_PATH).get_name()
    plt.rcParams["font.sans-serif"] = [_FONT_NAME, "DejaVu Sans"]
else:
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---------- 全局参数 ----------
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chip_stocks_daily.csv")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_output")
TRADING_DAYS = 252          # 每年交易日（年化用）
RISK_FREE_ANNUAL = 0.0      # 年化无风险利率（教学用设为0，可改为0.02）
COST_RATE = 0.001           # 单边交易成本 0.1%（佣金+滑点近似）

STOCK_NAMES = {
    "688981.SH": "中芯国际", "603501.SH": "韦尔股份", "002371.SZ": "北方华创",
    "688012.SH": "中微公司", "002049.SZ": "紫光国微", "600584.SH": "长电科技",
    "688256.SH": "寒武纪",
}


# ====================== 数据加载 ======================
def load_data(csv_path=CSV_PATH):
    """加载股价数据，返回排序后的 DataFrame。"""
    df = pd.read_csv(csv_path)
    df["trade_date"] = df["trade_date"].astype(str)
    for c in ["open", "high", "low", "close", "pre_close"]:
        df[c] = df[c].astype(float)
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    return df


def get_stock(df, ts_code):
    sub = df[df["ts_code"] == ts_code].copy().reset_index(drop=True)
    if sub.empty:
        raise ValueError(f"未找到股票代码 {ts_code} 的数据")
    return sub


# ====================== 指标与信号 ======================
def compute_ma(sub, short, long):
    """计算短/长简单移动平均线（收盘价）。"""
    sub = sub.copy()
    sub[f"ma{short}"] = sub["close"].rolling(short, min_periods=short).mean()
    sub[f"ma{long}"] = sub["close"].rolling(long, min_periods=long).mean()
    return sub


def gen_signals(sub, short, long):
    """
    生成交易信号（金叉买入 / 死叉卖出）。
    金叉：短均线由下向上穿越长均线  -> signal = +1 (买入)
    死叉：短均线由上向下穿越长均线  -> signal = -1 (卖出)
    其余为 0（持有/空仓，无操作）。
    """
    sub = sub.copy()
    s = sub[f"ma{short}"]
    l = sub[f"ma{long}"]
    diff = s - l
    prev_diff = diff.shift(1)
    sub["signal"] = 0
    golden = (prev_diff <= 0) & (diff > 0)
    death = (prev_diff >= 0) & (diff < 0)
    sub.loc[golden, "signal"] = 1
    sub.loc[death, "signal"] = -1
    # 实际下单动作推迟到次日开盘，避免前视偏差（信号由收盘价算出）
    sub["action"] = sub["signal"].shift(1)
    return sub


# ====================== 回测 ======================
def backtest(sub, cost=COST_RATE, init_capital=100000.0):
    """
    多头-only 回测：金叉满仓买入，死叉清仓。
    交易价格取信号次日开盘价（规避前视偏差）。
    返回 (sub 含 equity 列, trades 列表)
    """
    sub = sub.copy()
    cash = float(init_capital)
    shares = 0.0
    position = 0  # 0=空仓, 1=持仓
    equity = []
    trades = []
    first_action_idx = sub["action"].first_valid_index()

    for i in range(len(sub)):
        row = sub.iloc[i]
        action = row.get("action", np.nan)
        px_open = row["open"]
        px_close = row["close"]

        # 执行动作（在当日开盘价）
        if pd.notna(action) and action != 0:
            if action == 1 and position == 0:
                # 买入
                shares = cash / (px_open * (1 + cost))
                cash = 0.0
                position = 1
                trades.append({"date": row["trade_date"], "side": "BUY", "price": px_open})
            elif action == -1 and position == 1:
                # 卖出
                cash = shares * px_open * (1 - cost)
                trades.append({"date": row["trade_date"], "side": "SELL", "price": px_open})
                shares = 0.0
                position = 0

        # 盯市净值
        eq = cash + shares * px_close
        equity.append(eq)

    sub["equity"] = equity
    return sub, trades


# ====================== 量化指标 ======================
def compute_metrics(sub, init_capital=100000.0, cost=COST_RATE):
    """计算累计回报、最大回撤、夏普比率及辅助指标。"""
    eq = sub["equity"].values.astype(float)
    dates = sub["trade_date"].values
    # 仅统计有净值的区间
    valid = ~np.isnan(eq)
    eq = eq[valid]
    if len(eq) < 2:
        return {}
    daily_ret = np.diff(eq) / eq[:-1]

    # 累计回报
    cum_ret = eq[-1] / eq[0] - 1.0
    # 年化收益
    n_days = len(eq)
    ann_ret = (eq[-1] / eq[0]) ** (TRADING_DAYS / n_days) - 1.0
    # 最大回撤
    running_max = np.maximum.accumulate(eq)
    drawdown = eq / running_max - 1.0
    mdd = drawdown.min()
    # 夏普比率
    rf_daily = RISK_FREE_ANNUAL / TRADING_DAYS
    excess = daily_ret - rf_daily
    sharpe = np.mean(excess) / np.std(excess, ddof=1) * np.sqrt(TRADING_DAYS) if np.std(excess, ddof=1) > 0 else 0.0
    # 波动率（年化）
    vol_ann = np.std(daily_ret, ddof=1) * np.sqrt(TRADING_DAYS)

    # 买入持有（从首个有效净值日到最后一日，按收盘价）
    start_close = sub["close"].values[valid][0]
    end_close = sub["close"].values[valid][-1]
    buyhold_ret = end_close / start_close - 1.0

    return {
        "cumulative_return": float(cum_ret),
        "annual_return": float(ann_ret),
        "max_drawdown": float(mdd),
        "sharpe": float(sharpe),
        "annual_vol": float(vol_ann),
        "buyhold_return": float(buyhold_ret),
        "final_equity": float(eq[-1]),
        "init_capital": float(init_capital),
        "n_days": int(n_days),
    }


def summarize_trades(trades):
    n = len(trades)
    round_trips = n // 2
    return {"n_trades": n, "n_round_trips": round_trips}


# ====================== 可视化 ======================
def plot_strategy(sub, trades, ts_code, short, long, out_path):
    name = STOCK_NAMES.get(ts_code, ts_code)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), sharex=True,
                                   gridspec_kw={"height_ratios": [2.2, 1]})

    x = sub["trade_date"]
    ax1.plot(x, sub["close"], label="收盘价", color="#1f77b4", lw=1.2)
    ax1.plot(x, sub[f"ma{short}"], label=f"短均线 MA{short}", color="#ff7f0e", lw=1.4)
    ax1.plot(x, sub[f"ma{long}"], label=f"长均线 MA{long}", color="#2ca02c", lw=1.4)

    # 买卖标记（用 action 当日开盘价对应的收盘价位置更直观，这里用信号日近似）
    buy_dates = sub.loc[sub["action"] == 1, "trade_date"]
    sell_dates = sub.loc[sub["action"] == -1, "trade_date"]
    buy_px = sub.loc[sub["action"] == 1, "close"]
    sell_px = sub.loc[sub["action"] == -1, "close"]
    ax1.scatter(buy_dates, buy_px, marker="^", color="#d62728", s=110, zorder=5, label="买入信号(金叉)")
    ax1.scatter(sell_dates, sell_px, marker="v", color="#000000", s=110, zorder=5, label="卖出信号(死叉)")

    ax1.set_title(f"{name} ({ts_code})  双均线策略  MA{short}/MA{long}", fontsize=13)
    ax1.set_ylabel("价格 (元)")
    ax1.legend(loc="best", fontsize=9)
    ax1.grid(True, alpha=0.3)

    # 权益曲线
    ax2.plot(x, sub["equity"], label="策略净值", color="#9467bd", lw=1.4)
    ax2.set_ylabel("净值 (元)")
    ax2.set_xlabel("交易日")
    ax2.legend(loc="best", fontsize=9)
    ax2.grid(True, alpha=0.3)

    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


# ====================== 主流程 ======================
def run_one(df, ts_code, short, long, cost=COST_RATE, plot=True):
    sub = get_stock(df, ts_code)
    sub = compute_ma(sub, short, long)
    sub = gen_signals(sub, short, long)
    sub, trades = backtest(sub, cost=cost)
    metrics = compute_metrics(sub, cost=cost)
    trade_sum = summarize_trades(trades)
    metrics.update(trade_sum)

    if plot:
        os.makedirs(OUT_DIR, exist_ok=True)
        name = STOCK_NAMES.get(ts_code, ts_code)
        safe = f"{ts_code}_ma{short}_{long}".replace(".", "_")
        out_png = os.path.join(OUT_DIR, f"{safe}.png")
        plot_strategy(sub, trades, ts_code, short, long, out_png)
        metrics["plot"] = out_png
        # 同时保存交易明细
        with open(os.path.join(OUT_DIR, f"{safe}_trades.json"), "w", encoding="utf-8") as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)

    return sub, trades, metrics


def print_metrics(ts_code, short, long, metrics):
    name = STOCK_NAMES.get(ts_code, ts_code)
    print("=" * 60)
    print(f"股票: {name} ({ts_code})   参数: 短MA{short} / 长MA{long}")
    print("-" * 60)
    print(f"  累计回报 Cumulative Return : {metrics['cumulative_return']*100:8.2f}%")
    print(f"  年化收益 Annual Return     : {metrics['annual_return']*100:8.2f}%")
    print(f"  最大回撤 Max Drawdown      : {metrics['max_drawdown']*100:8.2f}%")
    print(f"  夏普比率 Sharpe Ratio      : {metrics['sharpe']:8.3f}")
    print(f"  年化波动率 Volatility      : {metrics['annual_vol']*100:8.2f}%")
    print(f"  买入持有 Buy&Hold Return   : {metrics['buyhold_return']*100:8.2f}%")
    print(f"  交易次数 Trades            : {metrics['n_trades']:8d}  (完整回合 {metrics['n_round_trips']})")
    print(f"  期末净值 Final Equity      : {metrics['final_equity']:,.2f}")
    print("=" * 60)


def run_grid(df, codes, configs):
    """多股票 × 多周期 对比，结果存 results.json 供报告/网页使用。"""
    results = []
    for code in codes:
        for short, long in configs:
            try:
                _, _, m = run_one(df, code, short, long, plot=False)
                m.update({"ts_code": code, "name": STOCK_NAMES.get(code, code),
                          "short": short, "long": long})
                results.append(m)
            except Exception as e:
                print(f"  [WARN] {code} {short}/{long}: {e}")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


def main():
    parser = argparse.ArgumentParser(description="双均线策略回测")
    parser.add_argument("--code", default="688981.SH", help="股票代码，默认中芯国际")
    parser.add_argument("--short", type=int, default=5, help="短均线周期")
    parser.add_argument("--long", type=int, default=15, help="长均线周期")
    parser.add_argument("--cost", type=float, default=COST_RATE, help="单边交易成本")
    parser.add_argument("--grid", action="store_true", help="运行多组周期对比")
    args = parser.parse_args()

    df = load_data()

    if args.grid:
        codes = list(STOCK_NAMES.keys())
        configs = [(5, 15), (5, 20), (10, 30), (10, 60), (20, 60)]
        print(">>> 运行多组周期对比 ...")
        res = run_grid(df, codes, configs)
        print(f">>> 已生成 {len(res)} 条结果 -> backtest_output/results.json")
        return

    sub, trades, metrics = run_one(df, args.code, args.short, args.long, cost=args.cost)
    print_metrics(args.code, args.short, args.long, metrics)
    print(f"\n已生成图表: {metrics.get('plot')}")


if __name__ == "__main__":
    main()
