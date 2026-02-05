#!/usr/bin/env python3
"""
股票价格监控脚本
监控用户持仓的股票价格，有异动时发送提醒
"""

import requests
import json
import os
from datetime import datetime

# 股票持仓数据
PORTFOLIO = {
    "港股": {
        "07709.HK": {"name": "XL二南方海力士", "shares": 1600, "cost": 29.76, "alert_threshold": 0.05}
    },
    "美股": {
        "SNXX.US": {"name": "Tradr 2X Long", "shares": 162, "cost": 36.38, "alert_threshold": 0.05},
        "MUU.US": {"name": "Direxion 2X做多MUU", "shares": 28, "cost": 232.20, "alert_threshold": 0.05},
        "AGQ.US": {"name": "2X做多白银ETF", "shares": 15, "cost": 244.50, "alert_threshold": 0.05}
    }
}

# 汇率
HKD_TO_CNY = 0.8718
USD_TO_CNY = 7.19

# 价格API配置
# 使用免费的Yahoo Finance API
def get_stock_price(symbol):
    """获取股票当前价格"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return result['meta']['regularMarketPrice']
    except Exception as e:
        print(f"获取 {symbol} 价格失败: {e}")
    return None

def calculate_change(current_price, cost_price):
    """计算涨跌幅"""
    if current_price is None or cost_price == 0:
        return None
    return (current_price - cost_price) / cost_price

def format_change(change):
    """格式化涨跌幅显示"""
    if change is None:
        return "N/A"
    pct = change * 100
    sign = "+" if pct > 0 else ""
    color = "📈" if pct > 0 else "📉"
    return f"{color} {sign}{pct:.2f}%"

def check_prices():
    """检查所有股票价格"""
    results = []
    total_value = 0
    total_cost = 0
    
    print(f"\n{'='*60}")
    print(f"🕐 股票价格检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    for market, stocks in PORTFOLIO.items():
        print(f"--- {market} ---")
        for symbol, info in stocks.items():
            name = info['name']
            shares = info['shares']
            cost = info['cost']
            threshold = info['alert_threshold']
            
            price = get_stock_price(symbol)
            change = calculate_change(price, cost)
            
            current_value = price * shares if price else 0
            cost_value = cost * shares
            
            total_value += current_value
            total_cost += cost_value
            
            emoji = "🔔" if abs(change or 0) >= threshold else "  "
            change_str = format_change(change)
            
            print(f"{emoji} {symbol} {name}")
            print(f"    成本: {cost:.2f} | 当前: {price:.2f if price else 'N/A'} | 涨跌: {change_str}")
            
            if change and abs(change) >= threshold:
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "change": change,
                    "current_price": price,
                    "cost": cost,
                    "market": market
                })
        print()
    
    # 计算总市值
    print(f"{'='*60}")
    print(f"📊 持仓总览 (人民币)")
    print(f"{'='*60}")
    
    hkd_value = PORTFOLIO["港股"]["07709.HK"]["shares"] * (get_stock_price("07709.HK") or 0)
    hkd_cost = PORTFOLIO["港股"]["07709.HK"]["shares"] * PORTFOLIO["港股"]["07709.HK"]["cost"]
    
    usd_value = sum(
        PORTFOLIO["美股"][s]["shares"] * (get_stock_price(s) or 0)
        for s in PORTFOLIO["美股"]
    )
    usd_cost = sum(
        PORTFOLIO["美股"][s]["shares"] * PORTFOLIO["美股"][s]["cost"]
        for s in PORTFOLIO["美股"]
    )
    
    total_cny = hkd_value * HKD_TO_CNY + usd_value * USD_TO_CNY
    total_cost_cny = hkd_cost * HKD_TO_CNY + usd_cost * USD_TO_CNY
    
    total_change = (total_cny - total_cost_cny) / total_cost_cny if total_cost_cny else 0
    change_str = format_change(total_change)
    
    print(f"💰 总成本: ¥{total_cost_cny:,.2f}")
    print(f"📈 当前值: ¥{total_cny:,.2f}")
    print(f"📉 浮盈亏: {change_str}")
    
    # 保存结果
    save_results(results, total_cny, total_cost_cny, change_str)
    
    return results

def save_results(alerts, total_value, total_cost, change_str):
    """保存检查结果"""
    result = {
        "check_time": datetime.now().isoformat(),
        "alerts": alerts,
        "total_value": total_value,
        "total_cost": total_cost,
        "change_str": change_str
    }
    
    with open("/root/.openclaw/workspace/stock_check_result.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    alerts = check_prices()
    
    if alerts:
        print(f"\n⚠️  发现 {len(alerts)} 只股票有显著异动！")
        for alert in alerts:
            direction = "大涨" if alert["change"] > 0 else "大跌"
            print(f"   🔔 {alert['symbol']} {alert['name']} {direction} {alert['change']*100:.2f}%")
    else:
        print("\n✅ 所有股票价格波动在正常范围内")

if __name__ == "__main__":
    main()
