#!/usr/bin/env python3
"""
KAI Quant v2 - 增强版数据获取（含完整技术指标计算）
通过 Tushare HTTP API 获取数据 + 计算技术指标
"""
import requests, json, os, math
from collections import deque

TOKEN = "a61f8a9ca3f4fc4d728bd4c923c926b0f204a13984c68abcec717162"
API_URL = "https://api.tushare.pro/"
OUT = r"E:\BA_learn\task\task1"

STOCKS = {
    "688981.SH": "中芯国际", "603501.SH": "韦尔股份", "002371.SZ": "北方华创",
    "688012.SH": "中微公司", "002049.SZ": "紫光国微", "600584.SH": "长电科技",
    "688256.SH": "寒武纪",
}
STOCK_INFO = {
    "688981.SH": {"sector": "晶圆制造", "desc": "中国大陆规模最大的集成电路制造企业"},
    "603501.SH": {"sector": "芯片设计", "desc": "全球领先的图像传感器芯片设计公司"},
    "002371.SZ": {"sector": "半导体设备", "desc": "国内半导体设备龙头，产品覆盖刻蚀/薄膜/清洗等"},
    "688012.SH": {"sector": "半导体设备", "desc": "国产刻蚀设备龙头，等离子体刻蚀/MOCVD"},
    "002049.SZ": {"sector": "芯片设计", "desc": "国内特种集成电路龙头，FPGA/智能卡芯片"},
    "600584.SH": {"sector": "封装测试", "desc": "全球第三大半导体封测企业"},
    "688256.SH": {"sector": "AI芯片", "desc": "国内AI芯片领军企业，智能处理器研发"},
}

def fetch_daily(ts_code, start="20250701", end="20260630"):
    payload = {"api_name": "daily", "token": TOKEN,
        "params": {"ts_code": ts_code, "start_date": start, "end_date": end},
        "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"}
    r = requests.post(API_URL, json=payload, timeout=30)
    data = r.json()
    if "data" not in data:
        raise Exception(data.get("msg", "Unknown error"))
    fields = data["data"]["fields"]
    items = data["data"]["items"]
    return [dict(zip(fields, i)) for i in items]

# === 技术指标计算函数 ===
def calc_ema(data, period):
    """指数移动平均"""
    if len(data) < period: return [None]*len(data)
    k = 2.0/(period+1)
    result = [None]*(period-1) + [sum(data[:period])/period]
    for i in range(period, len(data)):
        result.append(data[i]*k + result[i-1]*(1-k))
    return result

def calc_sma(data, period):
    """简单移动平均"""
    if len(data) < period: return [None]*len(data)
    result = [None]*(period-1)
    window = deque(data[:period], maxlen=period)
    for i in range(period-1, len(data)):
        if i >= period: window.append(data[i])
        result.append(sum(window)/period)
    return result

def calc_macd(closes, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    dif = [f-s if f and s else None for f,s in zip(ema_fast, ema_slow)]
    dea = calc_ema([d if d else 0 for d in dif], signal)
    macd_bar = [(d-e)*2 if d and e else None for d,e in zip(dif, dea)]
    return dif, dea, macd_bar

def calc_rsi(closes, period=14):
    if len(closes) < period+1: return [None]*len(closes)
    result = [None]*period
    gains, losses = [], []
    for i in range(1, len(closes)):
        chg = closes[i]-closes[i-1]
        gains.append(max(chg,0)); losses.append(max(-chg,0))
    avg_gain = sum(gains[:period])/period
    avg_loss = sum(losses[:period])/period
    result.append(100-(100/(1+avg_gain/avg_loss)) if avg_loss>0 else 100)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain*(period-1)+gains[i])/period
        avg_loss = (avg_loss*(period-1)+losses[i])/period
        result.append(100-(100/(1+avg_gain/avg_loss)) if avg_loss>0 else 100)
    return result

def calc_kdj(highs, lows, closes, period=9, k_period=3, d_period=3):
    n = len(closes)
    if n < period: return [None]*n, [None]*n, [None]*n
    k_vals, d_vals, j_vals = [None]*n, [None]*n, [None]*n
    for i in range(period-1, n):
        hh = max(highs[i-period+1:i+1])
        ll = min(lows[i-period+1:i+1])
        rsv = (closes[i]-ll)/(hh-ll)*100 if hh!=ll else 50
        if i == period-1:
            k_vals[i] = rsv
        else:
            k_vals[i] = (k_vals[i-1]*(k_period-1)+rsv)/k_period if k_vals[i-1] else rsv
    for i in range(period-1+k_period-1, n):
        if k_vals[i] and (d_vals[i-1] if i>period-1 else k_vals[i]):
            prev_d = d_vals[i-1] if d_vals[i-1] else k_vals[i]
            d_vals[i] = (prev_d*(d_period-1)+k_vals[i])/d_period
    d_vals_raw = [x if x else None for x in d_vals]
    for i in range(n):
        if k_vals[i] is not None and d_vals_raw[i] is not None:
            j_vals[i] = 3*k_vals[i]-2*d_vals_raw[i]
    return k_vals, d_vals_raw, j_vals

def calc_bollinger(closes, period=20, std_dev=2):
    ma = calc_sma(closes, period)
    upper, lower = [None]*len(closes), [None]*len(closes)
    for i in range(period-1, len(closes)):
        window = closes[i-period+1:i+1]
        mean = sum(window)/period
        std = math.sqrt(sum((x-mean)**2 for x in window)/period)
        upper[i] = mean+std_dev*std
        lower[i] = mean-std_dev*std
    return upper, ma, lower

def calc_support_resistance(closes, highs, lows):
    """计算支撑位和阻力位"""
    n = len(closes)
    if n < 20: return None, None, None
    recent = 20
    r_closes = closes[-recent:]
    r_highs = highs[-recent:]
    r_lows = lows[-recent:]
    resistance = max(r_highs)
    support = min(r_lows)
    current = closes[-1]
    pivot = (resistance + support + current) / 3
    return support, pivot, resistance

def calc_investment_score(indicators):
    """
    综合投资评分系统 (0-100分)
    技术面: 60分 | 基本面动量: 20分 | 成交量: 20分
    """
    score = 50  # 基准分
    details = []
    
    # 1. 均线趋势 (15分)
    if indicators.get('ma5') and indicators.get('ma20'):
        ma5 = indicators['ma5'][-1]; ma20 = indicators['ma20'][-1]
        if ma5 and ma20:
            if ma5 > ma20: score += 10; details.append("MA5>MA20 多头排列")
            elif ma5 < ma20: score -= 10; details.append("MA5<MA20 空头排列")
    
    # 2. MACD信号 (10分)
    if indicators.get('macd_dif') and indicators.get('macd_dea'):
        dif = indicators['macd_dif'][-1]; dea = indicators['macd_dea'][-1]
        if dif and dea:
            if dif > dea: score += 6; details.append("MACD DIF>DEA 偏多")
            else: score -= 6; details.append("MACD DIF<DEA 偏空")
    
    # 3. RSI状态 (10分)
    rsi_val = indicators.get('rsi', [None])[-1]
    if rsi_val is not None:
        if 40 <= rsi_val <= 60: score += 5; details.append(f"RSI={rsi_val:.1f} 中性区间")
        elif rsi_val > 70: details.append(f"RSI={rsi_val:.1f} 超买")
        elif rsi_val < 30: details.append(f"RSI={rsi_val:.1f} 超卖")
    
    # 4. 价格位置 vs 布林带 (10分)
    if indicators.get('boll_upper') and indicators.get('boll_lower'):
        price = indicators['close'][-1]; upper = indicators['boll_upper'][-1]
        lower = indicators['boll_lower'][-1]; middle = indicators['boll_middle'][-1]
        if price and upper and lower and middle:
            if price > middle: score += 3; details.append("价格在布林中轨上方")
            else: score -= 3; details.append("价格在布林中轨下方")
    
    # 5. 近期涨跌幅动量 (10分)
    closes = indicators['close']
    if len(closes) >= 5:
        chg_5d = (closes[-1]-closes[-5])/closes[-5]*100
        if chg_5d > 5: score += 8; details.append(f"5日涨幅{chg_5d:.1f}%")
        elif chg_5d > 0: score += 4
        elif chg_5d < -5: score -= 8; details.append(f"5日跌幅{chg_5d:.1f}%")
    
    # 6. 成交量分析 (5分)
    vols = indicators['vol']
    if len(vols) >= 20:
        avg_vol_20 = sum(v for v in vols[-20:] if v)/20
        if vols[-1] and avg_vol_20:
            vol_ratio = vols[-1]/avg_vol_20
            if vol_ratio > 1.5: score += 3; details.append("放量")
            elif vol_ratio < 0.5: score -= 2; details.append("缩量")
    
    score = max(0, min(100, score))
    
    # 投资建议
    if score >= 70: recommendation = "强烈买入"; color = "#e63946"
    elif score >= 60: recommendation = "买入"; color = "#f4a261"
    elif score >= 45: recommendation = "观望/持有"; color = "#6c757d"
    elif score >= 35: recommendation = "减仓"; color = "#457b9d"
    else: recommendation = "卖出"; color = "#2a9d8f"
    
    risk_level = "低风险" if score >= 65 else ("中风险" if score >= 40 else "高风险")
    
    return {"score": score, "recommendation": recommendation, "color": color,
            "risk_level": risk_level, "details": details}

print("="*60)
print("KAI Quant v2 - 增强版数据获取（含技术指标）")
print("="*60)

all_data = {}

for code, name in STOCKS.items():
    print(f"\n  获取 {name} ({code})...", end=" ")
    try:
        records = fetch_daily(code)
        records.sort(key=lambda x: x["trade_date"])
        
        closes = [r["close"] for r in records]
        opens = [r["open"] for r in records]
        highs = [r["high"] for r in records]
        lows = [r["low"] for r in records]
        vols = [r["vol"] for r in records]
        amounts = [r["amount"] for r in records]
        changes = [r["pct_chg"] for r in records]
        dates = [r["trade_date"] for r in records]
        
        # 技术指标
        ma5 = calc_sma(closes, 5)
        ma10 = calc_sma(closes, 10)
        ma20 = calc_sma(closes, 20)
        ma60 = calc_sma(closes, 60)
        macd_dif, macd_dea, macd_bar = calc_macd(closes)
        rsi = calc_rsi(closes, 14)
        kdj_k, kdj_d, kdj_j = calc_kdj(highs, lows, closes)
        boll_upper, boll_middle, boll_lower = calc_bollinger(closes)
        support, pivot, resistance = calc_support_resistance(closes, highs, lows)
        
        # 投资评分
        indicators = {
            'close': closes, 'high': highs, 'low': lows, 'vol': vols,
            'ma5': ma5, 'ma20': ma20, 'ma60': ma60,
            'macd_dif': macd_dif, 'macd_dea': macd_dea,
            'rsi': rsi, 'boll_upper': boll_upper,
            'boll_middle': boll_middle, 'boll_lower': boll_lower,
        }
        inv_score = calc_investment_score(indicators)
        
        info = STOCK_INFO.get(code, {"sector":"", "desc":""})
        
        all_data[name] = {
            "code": code,
            "sector": info.get("sector",""),
            "desc": info.get("desc",""),
            "dates": dates,
            "opens": opens, "highs": highs, "lows": lows,
            "closes": closes, "changes": changes,
            "vols": vols, "amounts": amounts,
            "ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60,
            "macd_dif": macd_dif, "macd_dea": macd_dea, "macd_bar": macd_bar,
            "rsi": rsi,
            "kdj_k": kdj_k, "kdj_d": kdj_d, "kdj_j": kdj_j,
            "boll_upper": boll_upper, "boll_middle": boll_middle, "boll_lower": boll_lower,
            "support": support, "pivot": pivot, "resistance": resistance,
            "investment_score": inv_score,
            "n_days": len(records),
        }
        chg = (closes[-1]-closes[0])/closes[0]*100 if closes[0]>0 else 0
        print(f"{len(records)}天 | 涨跌{chg:+.1f}% | 评分{inv_score['score']}/100 | {inv_score['recommendation']}")
    except Exception as e:
        print(f"失败: {e}")

# 归一化对比
normalized = {}
for name, d in all_data.items():
    base = d["closes"][0]
    if base and base > 0:
        normalized[name] = {"dates": d["dates"], "values": [round(c/base*100,2) for c in d["closes"]]}

# 保存JSON
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
output = {"stocks": sorted(all_data.keys()), "raw": all_data, "normalized": normalized}
json_path = os.path.join(OUT, "data", "stocks_data_v2.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)

print(f"\nJSON: {json_path}")
print(f"文件大小: {os.path.getsize(json_path)/1024:.1f} KB")

# 投资建议汇总
print(f"\n=== 投资建议汇总 ===")
for name in sorted(all_data.keys()):
    s = all_data[name]["investment_score"]
    print(f"  {name:8s} | 评分:{s['score']:3d} | {s['recommendation']:6s} | {s['risk_level']}")

print("\n完成!")
