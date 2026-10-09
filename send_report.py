import os
import json
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASS = os.environ.get("SENDER_PASS")

ALL_PSX_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 
    'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 
    'PSO', 'CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK'
]

TOP_CRYPTO_TOKENS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']

STOCK_FUNDAMENTALS = {
    'FFC': {'promoter': 72.5, 'fii': 5.2, 'shares_m': 1272},
    'OGDC': {'promoter': 74.0, 'fii': 4.1, 'shares_m': 4300},
    'LUCK': {'promoter': 55.0, 'fii': 8.5, 'shares_m': 313},
    'HUBC': {'promoter': 48.0, 'fii': 6.2, 'shares_m': 1297},
    'PPL': {'promoter': 67.5, 'fii': 3.8, 'shares_m': 2720},
    'ENGRO': {'promoter': 56.2, 'fii': 9.1, 'shares_m': 576},
    'EFERT': {'promoter': 56.3, 'fii': 4.5, 'shares_m': 1335},
    'SYS': {'promoter': 71.0, 'fii': 12.4, 'shares_m': 290},
    'MLCF': {'promoter': 73.5, 'fii': 4.2, 'shares_m': 1073},
    'DGKC': {'promoter': 72.0, 'fii': 3.9, 'shares_m': 438},
}

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def fetch_live_price(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            price_div = soup.find("div", {"class": "quote__close"})
            if price_div:
                return float(price_div.text.strip().replace("Rs.", "").replace(",", ""))
    except Exception:
        pass
    return 0.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_full_market_report():
    pro_filtered_list = []
    dow_buy_signals = []
    crypto_alerts = []
    
    print("🔍 PSX و کرپٹو مارکیٹ اسکین جاری ہے...")
    
    # 1. PSX Screener
    for sym in ALL_PSX_STOCKS:
        price = fetch_live_price(sym)
        f_info = STOCK_FUNDAMENTALS.get(sym, {'promoter': 71.5, 'fii': 3.8, 'shares_m': 250})
        if price > 0:
            mcap_m = price * f_info['shares_m']
            if f_info['promoter'] > 70.0 and f_info['fii'] > 3.5 and mcap_m < 10000.0:
                pro_filtered_list.append({
                    "اسٹاک": sym, "قیمت (Rs.)": f"{price:,.2f}",
                    "پروموٹر": f"{f_info['promoter']}%", "FII": f"{f_info['fii']}%", "MCap": f"Rs. {mcap_m:,.2f} M"
                })

    # 2. Top Crypto Scan
    for c_ticker in TOP_CRYPTO_TOKENS:
        try:
            df_c = yf.download(c_ticker, period="1mo", interval="1d", progress=False)
            if not df_c.empty:
                c_close = df_c['Close'].iloc[:, 0] if isinstance(df_c['Close'], pd.DataFrame) else df_c['Close']
                c_price = c_close.iloc[-1]
                rsi_c = calculate_rsi(c_close).iloc[-1]
                
                sig = "HOLD"
                if rsi_c < 42:
                    sig = "🟢 BUY / LONG"
                elif rsi_c > 68:
                    sig = "🔴 SELL / SHORT"
                    
                crypto_alerts.append(f"🪙 <b>{c_ticker.replace('-USD','')}</b>: `${c_price:,.2f}` | RSI: `{rsi_c:.1f}` | سگنل: <b>{sig}</b>")
        except Exception:
            pass

    # HTML Construction
    html_out = "<h3>🎯 پرو فلٹر میچز (PSX Multi-Baggers)</h3>"
    if pro_filtered_list:
        df_pro = pd.DataFrame(pro_filtered_list)
        html_out += df_pro.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت پورا فلٹر میچ کرنے والی کوئی نئی PSX کمپنی نہیں ملی۔</p>"
        
    html_out += "<br><hr><h3>⚡ ٹاپ کرپٹو AI الرٹس (Top Digital Currencies)</h3><ul>"
    for c_al in crypto_alerts:
        html_out += f"<li>{c_al}</li>"
    html_out += "</ul>"
        
    return html_out

def send_email_to_user(user_email, user_name, portfolio_data, market_report_html):
    if not SENDER_EMAIL or not SENDER_PASS or not user_email:
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛️ PSX & Crypto AI آٹو پورٹل رپورٹ - {user_name}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email
    
    port_html = f"<h3>💼 {user_name} کا پورٹ فولیو خلاصہ:</h3>"
    if portfolio_data:
        port_html += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;'>"
        port_html += "<tr style='background-color:#004d40;color:white;'><th>اسٹاک</th><th>تعداد</th><th>خرید قیمت</th><th>لائیو قیمت</th><th>نفع / نقصان</th></tr>"
        for sym, data in portfolio_data.items():
            l_price = fetch_live_price(sym)
            b_price = data.get("Buy Price", 0)
            qty = data.get("Quantity", 0)
            pnl = (l_price - b_price) * qty
            pnl_color = "green" if pnl >= 0 else "red"
            port_html += f"<tr><td><b>{sym}</b></td><td>{qty}</td><td>Rs. {b_price:,.2f}</td><td>Rs. {l_price:,.2f}</td><td style='color:{pnl_color};font-weight:bold;'>Rs. {pnl:+,.2f}</td></tr>"
        port_html += "</table>"
    else:
        port_html += "<p>آپ کے پورٹ فولیو میں فی الوقت کوئی شیئر شامل نہیں ہے۔</p>"
        
    full_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>السلام علیکم {user_name}!</h2>
        <p>پاکستان اسٹاک ایکسچینج (PSX) اور ٹاپ کرپٹو مارکیٹ کا لائیو خلاصہ ذیل میں پیش ہے:</p>
        <hr>{port_html}<br><hr>{market_report_html}<br>
        <p style="font-size:12px; color:#777;">یہ رپورٹ PSX & Crypto AI سسٹم کے ذریعے خودکار تیار کی گئی ہے۔</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(full_body, "html"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        print(f"✅ ای میل کامیابی سے ارسال کی گئی: {user_email}")
    except Exception as e:
        print(f"❌ ای میل ناکامی ({user_email}): {e}")

if __name__ == "__main__":
    users_db = load_json("users_db.json")
    ports_db = load_json("portfolios_db.json")
    report_content = generate_full_market_report()
    
    for user_name, u_info in users_db.items():
        user_email = u_info.get("email", "") if isinstance(u_info, dict) else ("masterjaved@gmail.com" if user_name.lower() == "javed" else "")
        if user_email:
            send_email_to_user(user_email, user_name, ports_db.get(user_name, {}), report_content)
