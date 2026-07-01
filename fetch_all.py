#!/usr/bin/env python3
"""
KAI Quant - 完整数据获取与处理
通过 Tushare HTTP API 获取7只芯片股一年交易数据 → CSV + JSON
"""
import requests, json, csv, os

TOKEN = "a61f8a9ca3f4fc4d728bd4c923c926b0f204a13984c68abcec717162"
API_URL = "https://api.tushare.pro/"
OUT = r"E:\BA_learn\task\task1"

STOCKS = {
    "688981.SH": "中芯国际",
    "603501.SH": "韦尔股份",
    "002371.SZ": "北方华创",
    "688012.SH": "中微公司",
    "002049.SZ": "紫光国微",
    "600584.SH": "长电科技",
    "688256.SH": "寒武纪",
}

def fetch_daily(ts_code, start="20250701", end="20260630"):
    """通过Tushare HTTP API获取日线数据"""
    payload = {
        "api_name": "daily",
        "token": TOKEN,
        "params": {"ts_code": ts_code, "start_date": start, "end_date": end},
        "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"
    }
    r = requests.post(API_URL, json=payload, timeout=30)
    data = r.json()
    if "data" not in data:
        raise Exception(data.get("msg", "Unknown error"))
    fields = data["data"]["fields"]
    items = data["data"]["items"]
    return [dict(zip(fields, item)) for item in items]

print("=" * 60)
print("KAI Quant - 芯片股数据获取")
print("=" * 60)

# === Step 1: 获取所有股票数据 ===
all_records = []
chart_data = {}

for code, name in STOCKS.items():
    print(f"  获取 {name} ({code})...", end=" ")
    try:
        records = fetch_daily(code)
        records.sort(key=lambda x: x["trade_date"])
        for r in records:
            r["name"] = name
            all_records.append(r)
        
        closes = [r["close"] for r in records]
        chg = (closes[-1] - closes[0]) / closes[0] * 100
        print(f"{len(records)}天, {min(closes):.2f}-{max(closes):.2f}, {chg:+.1f}%")
        
        chart_data[name] = {
            "dates": [r["trade_date"] for r in records],
            "closes": closes,
            "changes": [r["pct_chg"] for r in records],
            "vols": [r["vol"] for r in records],
            "amounts": [r["amount"] for r in records],
            "code": code,
        }
    except Exception as e:
        print(f"失败: {e}")

# === Step 2: 保存CSV ===
all_records.sort(key=lambda x: (x["name"], x["trade_date"]))
csv_path = os.path.join(OUT, "chip_stocks_daily.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["ts_code","name","trade_date","open","high","low","close",
                     "pre_close","change","pct_chg","vol","amount"])
    for r in all_records:
        writer.writerow([r.get(k,"") for k in 
            ["ts_code","name","trade_date","open","high","low","close",
             "pre_close","change","pct_chg","vol","amount"]])
print(f"\nCSV: {csv_path} ({len(all_records)} 条)")

# === Step 3: 生成JSON ===
normalized = {}
for name, d in chart_data.items():
    base = d["closes"][0]
    if base and base > 0:
        normalized[name] = {
            "dates": d["dates"],
            "values": [round(c / base * 100, 2) for c in d["closes"]],
        }

os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
json_path = os.path.join(OUT, "data", "stocks_data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({"stocks": sorted(chart_data.keys()), "raw": chart_data, "normalized": normalized}, 
              f, ensure_ascii=False)
print(f"JSON: {json_path}")

print(f"\n=== 数据统计 ({len(chart_data)}只股票) ===")
for name in sorted(chart_data.keys()):
    d = chart_data[name]
    c = d["closes"]
    chg = (c[-1] - c[0]) / c[0] * 100
    print(f"  {name} ({d['code']}): {len(c)}天 | {min(c):.2f}-{max(c):.2f} | {chg:+.1f}%")
print("\n完成!")
