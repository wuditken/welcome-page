#!/usr/bin/env python3
"""
股票价格监控脚本 (腾讯财经API版 v3)
使用腾讯财经API获取实时价格，稳定快速
"""

import requests
import json
import time
from datetime import datetime

# 股票持仓配置
# 港股代码: hk开头 + 代码
# 美股代码: us开头 + 代码
PORTFOLIO = {
    "港股": {
        "07709": {"name": "XL二南方海力士", "shares": 1600, "cost": 29.76, "currency": "HKD", "threshold": 0.05}
    },
    "美股": {
        "SNXX": {"name": "Tradr 2X Long", "shares": 162, "cost": 36.38, "currency": "USD", "threshold": 0.05},
        "MUU": {"name": "Direxion 2X做多MUU", "shares": 28, "cost": 232.20, "currency": "USD", "threshold": 0.05},
        "AGQ": {"name": "2X做多白银ETF", "shares": 15, "cost": 244.50, "currency": "USD", "threshold": 0.05}
    }
}

# 汇率
HKD_TO_CNY = 0.8718
USD_TO_CNY = 7.19

def get_price_from_tencent(code, market):
    """从腾讯财经API获取价格"""
    try:
        # 港股: us美股
        if market == "港股":
            url = f"https://qt.gtimg.cn/q=hk{code}"
        else:
            url = f"https://qt.gtimg.cn/q=us{code}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 解析返回数据 (格式: v_usSNXX="200~...")
            text = response.text
            # 找到 = 后面的数据
            if '=' in text:
                data = text.split('=')[1].strip('";')
                parts = data.split('~')
                if len(parts) > 32:
                    current_price = float(parts[3])  # 当前价
                    return current_price
    except Exception as e:
        print(f"  ❌ 获取 {code} 价格失败: {e}")
    return None

def check_prices():
    """检查所有股票价格"""
    alerts = []
    total_cost = 0
    total_value = 0
    
    print(f"\n{'='*60}")
    print(f"📊 股票价格检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据来源: 腾讯财经API")
    print(f"{'='*60}\n")
    
    for market, stocks in PORTFOLIO.items():
        print(f"--- {market} ---")
        for code, info in stocks.items():
            name = info['name']
            shares = info['shares']
            cost = info['cost']
            currency = info['currency']
            threshold = info['threshold']
            
            price = get_price_from_tencent(code, market)
            time.sleep(1)  # 避免请求过快
            
            change = (price - cost) / cost if price and cost else None
            
            rate = HKD_TO_CNY if currency == "HKD" else USD_TO_CNY
            cost_cny = cost * shares * rate
            value_cny = price * shares * rate if price else 0
            
            total_cost += cost_cny
            total_value += value_cny
            
            # 检查异动
            if change and abs(change) >= threshold:
                direction = "↑" if change > 0 else "↓"
                alerts.append(f"🔔 {code} {name}: {direction}{abs(change)*100:.2f}% (当前:¥{price:.2f})")
            
            price_str = f"¥{price:.2f}" if price else "N/A"
            change_str = f"{'+' if change and change > 0 else ''}{change*100:.2f}%" if change else "N/A"
            emoji = "🔔" if change and abs(change) >= threshold else "  "
            
            print(f"  {emoji} {code} | {name}")
            print(f"      成本: ¥{cost:.2f} ({currency}) | 当前: {price_str} | 涨跌: {change_str}")
        print()
    
    # 汇总
    print(f"{'='*60}")
    print(f"💰 持仓总览 (人民币)")
    print(f"{'='*60}")
    print(f"📈 总成本: ¥{total_cost:,.2f}")
    print(f"💵 当前值: ¥{total_value:,.2f}")
    
    total_change = (total_value - total_cost) / total_cost if total_cost else 0
    print(f"{'📉' if total_change < 0 else '📈'} 浮盈亏: {'+' if total_change > 0 else ''}{total_change*100:.2f}%")
    
    # 保存结果
    result = {
        "check_time": datetime.now().isoformat(),
        "alerts": alerts,
        "total_value": total_value,
        "total_cost": total_cost,
        "total_change_pct": total_change * 100
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
