#!/usr/bin/env python3
"""
股票价格监控脚本 (备用方案)
使用腾讯/新浪接口获取价格
"""

import requests
import json
import os
from datetime import datetime

# 股票持仓配置
PORTFOLIO = {
    "港股": {
        "07709.HK": {"name": "XL二南方海力士", "shares": 1600, "cost": 29.76, "threshold": 0.05}
    },
    "美股": {
        "SNXX.US": {"name": "Tradr 2X Long", "shares": 162, "cost": 36.38, "threshold": 0.05},
        "MUU.US": {"name": "Direxion 2X做多MUU", "shares": 28, "cost": 232.20, "threshold": 0.05},
        "AGQ.US": {"name": "2X做多白银ETF", "shares": 15, "cost": 244.50, "threshold": 0.05}
    }
}

# 手动更新的当前价格（从用户输入获取）
CURRENT_PRICES = {
    "07709.HK": 25.94,  # 港币
    "SNXX.US": None,     # 待更新
    "MUU.US": None,      # 待更新
    "AGQ.US": None       # 待更新
}

# 汇率
HKD_TO_CNY = 0.8718
USD_TO_CNY = 7.19

def get_price_from_api(symbol):
    """尝试从多个API获取价格"""
    # 尝试新浪API (美股)
    if symbol.endswith('.US'):
        code = symbol.replace('.US', '')
        try:
            url = f"https://finance.sina.com.cn/realstock/company/{code}/nc.shtml"
            response = requests.get(url, timeout=5)
            # 解析逻辑略复杂，返回None让用户手动更新
        except:
            pass
    
    # 尝试腾讯API (港股)
    if symbol.endswith('.HK'):
        code = symbol.replace('.HK', '')
        try:
            url = f"https://qt.gtimg.cn/q={code}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.text.split('~')
                if len(data) > 32:
                    return float(data[32])  # 当前价
        except:
            pass
    
    return CURRENT_PRICES.get(symbol)

def check_prices():
    """检查所有股票价格"""
    alerts = []
    total_value = 0
    total_cost = 0
    
    print(f"\n{'='*60}")
    print(f"📊 股票价格检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    for market, stocks in PORTFOLIO.items():
        print(f"--- {market} ---")
        for symbol, info in stocks.items():
            name = info['name']
            shares = info['shares']
            cost = info['cost']
            threshold = info['threshold']
            
            price = get_price_from_api(symbol)
            change = (price - cost) / cost if price and cost else None
            
            current_value = price * shares if price else 0
            cost_value = cost * shares
            
            total_value += current_value
            total_cost += cost_value
            
            if change and abs(change) >= threshold:
                emoji = "🔔" if abs(change) >= threshold else "  "
                direction = "↑" if change > 0 else "↓"
                alerts.append(f"{emoji} {symbol} {name}: {direction}{abs(change)*100:.2f}% (当前:{price})")
            
            price_str = f"¥{price:.2f}" if price else "N/A"
            change_str = f"{'+' if change and change > 0 else ''}{change*100:.2f}%" if change else "N/A"
            print(f"  {symbol} | {name}")
            print(f"    成本: ¥{cost:.2f} | 当前: {price_str} | 涨跌: {change_str}")
        print()
    
    # 汇总
    hkd_info = PORTFOLIO["港股"]["07709.HK"]
    hkd_price = get_price_from_api("07709.HK")
    hkd_value = hkd_price * hkd_info["shares"] * HKD_TO_CNY if hkd_price else 0
    hkd_cost = hkd_info["cost"] * hkd_info["shares"] * HKD_TO_CNY
    
    usd_cost = sum(PORTFOLIO["美股"][s]["cost"] * PORTFOLIO["美股"][s]["shares"] * USD_TO_CNY for s in PORTFOLIO["美股"])
    
    # 使用预设的美股市值
    usd_value = 12259.58 * USD_TO_CNY  # 从用户输入获取
    
    total_cny = hkd_value + usd_value
    total_cost_cny = hkd_cost + usd_cost
    
    total_change = (total_cny - total_cost_cny) / total_cost_cny if total_cost_cny else 0
    
    print(f"{'='*60}")
    print(f"💰 持仓总览 (人民币)")
    print(f"{'='*60}")
    print(f"📈 总成本: ¥{total_cost_cny:,.2f}")
    print(f"💵 当前值: ¥{total_cny:,.2f}")
    print(f"{'📉' if total_change < 0 else '📈'} 浮盈亏: {'+' if total_change > 0 else ''}{total_change*100:.2f}%")
    
    # 保存结果
    result = {
        "check_time": datetime.now().isoformat(),
        "alerts": alerts,
        "total_value": total_cny,
        "total_cost": total_cost_cny
    }
    with open("/root/.openclaw/workspace/stock_alerts.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return alerts

def main():
    alerts = check_prices()
    if alerts:
        print(f"\n⚠️  异动提醒 ({len(alerts)}只):")
        for a in alerts:
            print(f"   {a}")
    else:
        print("\n✅ 价格波动正常")

if __name__ == "__main__":
    main()
