# -*- coding: utf-8 -*-
"""
fetch_realtime.py — 实时行情获取（本地运行，无需 token）

从东方财富公开日线接口拉取 7 只芯片股的最新 OHLC 日线，
更新 chip_stocks_daily.csv（兼容双均线 / 海龟回测脚本的字段格式）。
可选触发重新生成统一门户网页 index.html。

用法：
    python fetch_realtime.py                # 拉取全部 7 只，更新 CSV
    python fetch_realtime.py --rebuild      # 拉取后顺便重新生成 index.html
    python fetch_realtime.py --codes 688981.SH 603501.SH   # 只拉指定股票

依赖：仅 Python 标准库（urllib / json / csv / datetime），无需 pip 安装。
说明：本文件在隔离沙箱中可能无法联网，请在本地终端运行。
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.request
import urllib.parse

SRC_CSV = "chip_stocks_daily.csv"
STOCKS = [
    ("688981.SH", "中芯国际"),
    ("688012.SH", "中微公司"),
    ("688256.SH", "寒武纪"),
    ("600584.SH", "长电科技"),
    ("603501.SH", "韦尔股份"),
    ("002049.SZ", "紫光国微"),
    ("002371.SZ", "北方华创"),
]

# 东方财富 secid 前缀：沪市 1.，深市 0.
def to_secid(ts_code):
    code, market = ts_code.split(".")
    return ("1." if market == "SH" else "0.") + code


EM_KLINE = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    "?secid={secid}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f57,f58"
    "&klt=101&fqt=0&beg={beg}&end=20500101"
)


def fetch_one(ts_code, name, beg="20250101"):
    secid = to_secid(ts_code)
    url = EM_KLINE.format(secid=secid, beg=beg)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    obj = json.loads(raw)
    data = (obj.get("data") or {}).get("klines") or []
    rows = []
    for ln in data:
        parts = ln.split(",")
        # f51日期, f52开, f53收, f54最低, f55最高, f57代码, f58名称
        date = parts[0].replace("-", "")
        o, c, lo, hi = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        # 缺失字段用推导值补齐（pre_close/change/pct_chg/vol/amount）
        pre = lo  # 近似：无昨收时取最低，仅用于格式兼容
        change = round(c - pre, 2)
        pct = round(change / pre * 100, 2) if pre else 0.0
        rows.append({
            "ts_code": ts_code, "name": name, "trade_date": date,
            "open": o, "high": hi, "low": lo, "close": c,
            "pre_close": pre, "change": change, "pct_chg": pct,
            "vol": 0, "amount": 0.0,
        })
    return rows


def load_existing(path):
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["ts_code"], {})[r["trade_date"]] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="拉取后重新生成 index.html")
    ap.add_argument("--codes", nargs="*", default=None, help="只拉指定 ts_code")
    ap.add_argument("--beg", default="20250101", help="开始日期 YYYYMMDD")
    args = ap.parse_args()

    want = {c for c, _ in STOCKS}
    if args.codes:
        want = {c for c in args.codes if c in want}

    existing = load_existing(SRC_CSV)
    total_new = 0
    for ts_code, name in STOCKS:
        if ts_code not in want:
            continue
        try:
            rows = fetch_one(ts_code, name, beg=args.beg)
        except Exception as e:
            print(f"  ✗ {name} ({ts_code}) 拉取失败：{e}")
            continue
        book = existing.get(ts_code, {})
        added = 0
        for r in rows:
            if r["trade_date"] not in book:
                book[r["trade_date"]] = r
                added += 1
        existing[ts_code] = book
        total_new += added
        print(f"  ✓ {name} ({ts_code}) 共 {len(book)} 条（本次新增 {added}）")

    # 写回 CSV
    fieldnames = ["ts_code", "name", "trade_date", "open", "high", "low", "close",
                  "pre_close", "change", "pct_chg", "vol", "amount"]
    with open(SRC_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for ts_code, _ in STOCKS:
            book = existing.get(ts_code, {})
            for d in sorted(book.keys()):
                w.writerow(book[d])
    print(f"\n已更新 {SRC_CSV}（新增 {total_new} 条）。")

    if args.rebuild:
        try:
            import build_portal
            build_portal.main()
            print("已重新生成 index.html。")
        except Exception as e:
            print(f"重新生成 index.html 失败：{e}")


if __name__ == "__main__":
    main()
