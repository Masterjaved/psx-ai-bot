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
    'PSO', 'CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK', 
    'ANL', 'HASCOL', 'BOP', 'FNEL', 'FLYNG', 'LOADS', 'ATRL', 'NRL', 'GTYR', 'GHNI', 
    'GHGL', 'INIL', 'ISL', 'ASTL', 'MUGHAL', 'CHCC', 'PIOC', 'KOHC', 'ACPL', 'BWCL',
    'TREET', 'GGL', 'UNITY', 'AGP', 'ABOT', 'GLAXO', 'HINOON', 'FEROZ', 'PSMC', 'INDU'
]

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
    'POL': {'promoter': 71.2, 'fii': 5.8, 'shares_m': 283},
    'PAEL': {'promoter': 71.5, 'fii': 3.7, 'shares_m': 850},
    'AIRLINK': {'promoter': 74.5, 'fii': 6.5, 'shares_m': 395},
    'FCCL': {'promoter': 70.8, 'fii': 3.6, 'shares_m': 2100},
    'SEARL': {'promoter': 72.1, 'fii': 4.8, 'shares_m': 380},
    'AVN': {'promoter': 73.0, 'fii': 5.1, 'shares_m': 320},
    'CNERGY': {'promoter': 73.2, 'fii': 3.8, 'shares_m': 5400},
    'KEL': {'promoter': 72.0, 'fii': 4.0, 'shares_m': 27600},
    'TELE': {'promoter': 71.0, 'fii': 3.9, 'shares_m': 400},
    'WTL': {'promoter': 70.5, 'fii': 3.6, 'shares_m': 3700},
    'HUMNL': {'promoter': 71.8, 'fii': 3.7, 'shares_m': 940},
    'TRG': {'promoter': 65.0, 'fii': 11.2, 'shares_m': 545},
    'ATRL': {'promoter': 71.5, 'fii': 4.3, 'shares_m': 106},
    'CHCC': {'promoter': 72.8, 'fii': 3.9, 'shares_m': 200},
    'PIOC': {'promoter': 73.1, 'fii': 3.7, 'shares_m': 227},
    'MUGHAL': {'promoter': 74.0, 'fii': 4.1, 'shares_m': 335},
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

def evaluate_dow_theory(df):
    if df.empty or len(df) < 15:
        return "HOLD", "ڈیٹا ناکافی ہے"
    
    close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
    vol = df['Volume'].iloc[:, 0] if isinstance(df['Volume'], pd.DataFrame) else df['Volume']
    
    recent_price = close.iloc[-1]
    prev_high = close.iloc[-15:-1].max()
    prev_low = close.iloc[-15:-1].min()
    
    avg_vol = vol.iloc[-15:-1].mean()
    recent_vol = vol.iloc[-1]
    
    if recent_price > prev_high and recent_vol > avg_vol:
        return "BUY", "Higher High بنے کے ساتھ والیوم میں زبردست اضافہ ہوا ہے! (اپ ٹرینڈ)"
    elif recent_price < prev_low:
        return "SELL", "قیمت نے پچھلی نچلی سطح کو توڑ دیا ہے! (ڈاؤن ٹرینڈ خطرہ)"
    else:
        return "HOLD", "قیمت نارمل رینج میں ترسیل ہو رہی ہے۔"

def generate_full_market_report():
    pro_filtered_list = []
    dow_buy_signals = []
    dow_sell_signals = []
    rsi_oversold = []
    
    print("🔍 PSX مارکیٹ کا ڈیٹا اسکین کیا جا رہا ہے...")
    
    for sym in ALL_PSX_STOCKS:
        price = fetch_live_price(sym)
        
        # Fundamental Pro Screener
        f_info = STOCK_FUNDAMENTALS.get(sym, {'promoter': 71.5, 'fii': 3.8, 'shares_m': 250})
        promoter = f_info['promoter']
        fii = f_info['fii']
        shares_m = f_info['shares_m']
        
        if price > 0:
            mcap_m = price * shares_m
            if promoter > 70.0 and fii > 3.5 and mcap_m < 10000.0:
                pro_filtered_list.append({
                    "اسٹاک": sym,
                    "قیمت (Rs.)": f"{price:,.2f}",
                    "پروموٹر ہولڈنگ": f"{promoter}%",
                    "FII ہولڈنگ": f"{fii}%",
                    "مارکیٹ کیپ": f"Rs. {mcap_m:,.2f} M"
                })
        
        # Technical & Dow Theory Evaluation
        try:
            df = yf.download(f"{sym}.KA", period="1mo", interval="1d", progress=False)
            if not df.empty:
                c_close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                r_val = calculate_rsi(c_close).iloc[-1]
                dow_sig, dow_desc = evaluate_dow_theory(df)
                
                if dow_sig == "BUY" and price > 0:
                    dow_buy_signals.append(f"🟢 <b>{sym}</b>: قیمت Rs.{price:,.2f} | {dow_desc}")
                elif dow_sig == "SELL" and price > 0:
                    dow_sell_signals.append(f"🔴 <b>{sym}</b>: قیمت Rs.{price:,.2f} | {dow_desc}")
                    
                if r_val <= 35 and price > 0:
                    rsi_oversold.append(f"🔵 <b>{sym}</b>: قیمت Rs.{price:,.2f} | RSI = {r_val:.1f}")
        except Exception:
            pass

    # HTML Construction
    html_out = "<h3>🎯 پرو فلٹر میچز (Promoter > 70% | FII > 3.5% | MCap < 10,000M PKR)</h3>"
    if pro_filtered_list:
        df_pro = pd.DataFrame(pro_filtered_list)
        html_out += df_pro.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت پورا فلٹر میچ کرنے والی کوئی نئی کمپنی نہیں ملی۔</p>"
        
    html_out += "<br><hr><h3>🏛️ ڈاؤ تھیوری بائنگ و سیلنگ سگنلز</h3>"
    
    html_out += "<h4>🟢 ڈاؤ تھیوری خریداری کا زون (Buying Zone):</h4>"
    if dow_buy_signals:
        html_out += "<ul>"
        for d_buy in dow_buy_signals:
            html_out += f"<li>{d_buy}</li>"
        html_out += "</ul>"
    else:
        html_out += "<p>اس وقت کوئی شیئر ڈاؤ تھیوری کے بریک آؤٹ بائنگ زون میں نہیں ہے۔</p>"
        
    html_out += "<h4>🔴 ڈاؤ تھیوری فروخت/خطرہ کا زون (Selling Zone):</h4>"
    if dow_sell_signals:
        html_out += "<ul>"
        for d_sell in dow_sell_signals:
            html_out += f"<li>{d_sell}</li>"
        html_out += "</ul>"
    else:
        html_out += "<p>اس وقت کوئی شیئر ڈاؤ تھیوری کے سیلنگ زون میں نہیں ہے۔</p>"

    html_out += "<br><hr><h3>📊 RSI اوور سولڈ سگنلز (RSI <= 35)</h3>"
    if rsi_oversold:
        html_out += "<ul>"
        for r_os in rsi_oversold:
            html_out += f"<li>{r_os}</li>"
        html_out += "</ul>"
    else:
        html_out += "<p>اس وقت کوئی شیئر RSI کے مطابق اوور سولڈ رینج میں نہیں ہے۔</p>"
        
    return html_out

def send_email_to_user(user_email, user_name, portfolio_data, market_report_html):
    if not SENDER_EMAIL or not SENDER_PASS or not user_email:
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛️ PSX AI مکمل مارکیٹ و ڈاؤ تھیوری رپورٹ - {user_name}"
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
        <p>پاکستان اسٹاک ایکسچینج (PSX) کا پورٹ فولیو خلاصہ، پرو اسکرینر اور ڈاؤ تھیوری کی جامع رپورٹ ذیل میں پیش ہے:</p>
        <hr>
        {port_html}
        <br>
        <hr>
        {market_report_html}
        <br>
        <p style="font-size:12px; color:#777;">یہ رپورٹ PSX AI سمارٹ سسٹم کے ذریعے خودکار تیار کی گئی ہے۔</p>
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
    
    report_content = generate_full_market_report()
    
    for user_name, u_info in users_db.items():
        user_email = ""
        if isinstance(u_info, dict):
            user_email = u_info.get("email", "")
        elif user_name.lower() == "javed":
            user_email = "masterjaved@gmail.com"
            
        if user_email:
            user_portfolio = ports_db.get(user_name, {})
            send_email_to_user(user_email, user_name, user_portfolio, report_content)
