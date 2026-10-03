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

SHARIAH_STOCKS = ['FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 'PSO']
PENNY_STOCKS = ['CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK', 'ANL', 'HASCOL', 'BOP', 'FNEL', 'FLYNG', 'LOADS']

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
        res = requests.get(url, headers=headers, timeout=5)
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

def generate_market_opportunities():
    buy_signals = []
    overbought = []
    
    all_symbols = list(set(SHARIAH_STOCKS + PENNY_STOCKS))
    for sym in all_symbols:
        try:
            df = yf.download(f"{sym}.KA", period="1mo", interval="1d", progress=False)
            if not df.empty:
                c_close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                price = c_close.iloc[-1]
                rsi_val = calculate_rsi(c_close).iloc[-1]
                
                if rsi_val <= 35:
                    buy_signals.append(f"🟢 <b>{sym}</b>: قیمت Rs.{price:,.2f} | RSI = {rsi_val:.1f} (خریدنے کا اچھا موقع)")
                elif rsi_val >= 70:
                    overbought.append(f"🔴 <b>{sym}</b>: قیمت Rs.{price:,.2f} | RSI = {rsi_val:.1f} (زیادہ خریدا جا چکا ہے، محتاط رہیں)")
        except Exception:
            pass
            
    html = "<h3>📊 مارکیٹ سگنلز و موقعے (KSE-100 / KMI-30 Shariah Analysis)</h3>"
    if buy_signals:
        html += "<h4>🟢 خریداری کے بہترین مواقع (Oversold):</h4><ul>"
        for b in buy_signals:
            html += f"<li>{b}</li>"
        html += "</ul>"
    else:
        html += "<p>🟢 اس وقت KSE-100/KMI-30 کا کوئی شیئر اوور سولڈ نہیں ہے۔</p>"
        
    if overbought:
        html += "<h4>🔴 الرٹ / زیادہ خریدے گئے شیئرز (Overbought):</h4><ul>"
        for o in overbought:
            html += f"<li>{o}</li>"
        html += "</ul>"
        
    return html

def send_email_to_user(user_email, user_name, portfolio_data, market_report_html):
    if not SENDER_EMAIL or not SENDER_PASS or not user_email:
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛️ PSX AI ڈیلی اٹو رپورٹ - {user_name}"
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
        port_html += "<p>آپ کے پورٹ فولیو میں ابھی تک کوئی شیئر شامل نہیں ہے۔</p>"
        
    full_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>السلام علیکم {user_name}!</h2>
        <p>پاکستان اسٹاک ایکسچینج (PSX) کی خودکار پورٹ فولیو اور مارکیٹ رپورٹ ذیل میں پیش ہے:</p>
        <hr>
        {port_html}
        <br>
        <hr>
        {market_report_html}
        <br>
        <p style="font-size:12px; color:#777;">یہ رپورٹ PSX AI سسٹم کے ذریعے خودکار تیار کی گئی ہے۔</p>
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
        print(f"❌ ای میل بھیجنے میں ناکامی ({user_email}): {e}")

if __name__ == "__main__":
    users_db = load_json("users_db.json")
    ports_db = load_json("portfolios_db.json")
    
    market_report_html = generate_market_opportunities()
    
    # Send email to each registered user
    for user_name, u_info in users_db.items():
        user_email = ""
        if isinstance(u_info, dict):
            user_email = u_info.get("email", "")
        elif user_name == "javed":
            user_email = "masterjaved@gmail.com"
            
        if user_email:
            user_portfolio = ports_db.get(user_name, {})
            send_email_to_user(user_email, user_name, user_portfolio, market_report_html)
