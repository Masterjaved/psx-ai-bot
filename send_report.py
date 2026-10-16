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

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def fetch_psx_price_robust(symbol):
    clean_sym = symbol.upper().replace(".KA", "").strip()
    # Priority 1: PSX DPS Official Scraping
    url = f"https://dps.psx.com.pk/company/{clean_sym}"
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
        
    # Priority 2: Yahoo Finance Fallback (.KA)
    try:
        df = yf.download(f"{clean_sym}.KA", period="5d", interval="1d", progress=False)
        if not df.empty:
            c_close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
            return float(c_close.iloc[-1])
    except Exception:
        pass
    return 0.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_separated_market_report():
    psx_buy_list = []
    psx_sell_list = []
    crypto_buy_list = []
    crypto_sell_list = []
    
    # 1. PSX STOCKS SCANNING
    for sym in ALL_PSX_STOCKS:
        try:
            price = fetch_psx_price_robust(sym)
            if price > 0:
                df_p = yf.download(f"{sym}.KA", period="1mo", interval="1d", progress=False)
                if not df_p.empty:
                    c_close = df_p['Close'].iloc[:, 0] if isinstance(df_p['Close'], pd.DataFrame) else df_p['Close']
                    c_high = df_p['High'].iloc[:, 0] if isinstance(df_p['High'], pd.DataFrame) else df_p['High']
                    c_low = df_p['Low'].iloc[:, 0] if isinstance(df_p['Low'], pd.DataFrame) else df_p['Low']
                    
                    rsi_p = float(calculate_rsi(c_close).iloc[-1])
                    atr = float((c_high - c_low).iloc[-14:].mean()) if len(df_p) >= 14 else (price * 0.02)
                    
                    buy_low = round(price * 0.992, 2)
                    buy_high = round(price * 1.008, 2)
                    tp1 = round(price + (atr * 1.5), 2)
                    tp2 = round(price + (atr * 3.0), 2)
                    sl = round(price - (atr * 1.5), 2)
                    
                    if rsi_p < 48:
                        psx_buy_list.append({
                            "اسٹاک (PSX)": f"🏛️ {sym}",
                            "لائیو قیمت": f"Rs. {price:,.2f}",
                            "خریداری کی حد (Buy Range)": f"Rs. {buy_low} - {buy_high}",
                            "پہلا ٹارگٹ (TP1)": f"Rs. {tp1}",
                            "دوسرا ٹارگٹ (TP2)": f"Rs. {tp2}",
                            "اسٹاپ لاس (SL)": f"Rs. {sl}"
                        })
                    elif rsi_p > 65:
                        psx_sell_list.append({
                            "اسٹاک (PSX)": f"🏛️ {sym}",
                            "لائیو قیمت": f"Rs. {price:,.2f}",
                            "RSI": f"{rsi_p:.1f}",
                            "ہدایت": "🔴 منافع بک کریں (Take Profit / Sell)"
                        })
        except Exception:
            pass

    # 2. CRYPTO SCANNING
    for c_ticker in TOP_CRYPTO_TOKENS:
        try:
            df_c = yf.download(c_ticker, period="1mo", interval="1d", progress=False)
            if not df_c.empty:
                c_close = df_c['Close'].iloc[:, 0] if isinstance(df_c['Close'], pd.DataFrame) else df_c['Close']
                c_high = df_c['High'].iloc[:, 0] if isinstance(df_c['High'], pd.DataFrame) else df_c['High']
                c_low = df_c['Low'].iloc[:, 0] if isinstance(df_c['Low'], pd.DataFrame) else df_c['Low']
                
                c_price = float(c_close.iloc[-1])
                rsi_c = float(calculate_rsi(c_close).iloc[-1])
                atr = float((c_high - c_low).iloc[-14:].mean())
                
                name = c_ticker.replace("-USD", "")
                
                if rsi_c < 48:
                    buy_low = round(c_price * 0.995, 2)
                    buy_high = round(c_price * 1.008, 2)
                    tp1 = round(c_price + (atr * 1.5), 2)
                    tp2 = round(c_price + (atr * 3.0), 2)
                    sl = round(c_price - (atr * 1.5), 2)
                    
                    crypto_buy_list.append({
                        "ٹوکن (Crypto)": f"🪙 {name}",
                        "موجودہ قیمت": f"${c_price:,.2f}",
                        "خریداری کی حد (Buy Range)": f"${buy_low} - ${buy_high}",
                        "پہلا ٹارگٹ (TP1)": f"${tp1}",
                        "دوسرا ٹارگٹ (TP2)": f"${tp2}",
                        "اسٹاپ لاس (SL)": f"${sl}"
                    })
                elif rsi_c > 65:
                    crypto_sell_list.append({
                        "ٹوکن (Crypto)": f"🪙 {name}",
                        "موجودہ قیمت": f"${c_price:,.2f}",
                        "RSI": f"{rsi_c:.1f}",
                        "ہدایت": "🔴 منافع بک کریں (Take Profit / Sell)"
                    })
        except Exception:
            pass

    # HTML Output Assembly
    html_out = "<h2 style='color:#004D40;'>🏛️ پاکستان اسٹاک ایکسچینج (PSX) و کرپٹو AI الرٹ رپورٹ</h2>"
    
    # PSX SECTION
    html_out += "<h3>🇵🇰 پاکستان اسٹاک ایکسچینج (PSX) - خریدنے والے شیئرز</h3>"
    if psx_buy_list:
        df_pb = pd.DataFrame(psx_buy_list)
        html_out += df_pb.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت PSX میں تمام شیئرز ہولڈ زون میں ہیں۔</p>"
        
    if psx_sell_list:
        html_out += "<h4>🔴 PSX منافع بکنگ / خروج سگنلز</h4>"
        df_ps = pd.DataFrame(psx_sell_list)
        html_out += df_ps.to_html(index=False, classes="table table-striped", border=1)
        
    html_out += "<br><hr>"
    
    # CRYPTO SECTION
    html_out += "<h3>🪙 عالمی کرپٹو مارکیٹ سگنلز (Crypto Buy/Sell)</h3>"
    if crypto_buy_list:
        df_cb = pd.DataFrame(crypto_buy_list)
        html_out += df_cb.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت کرپٹو کرنسیز میں نیا اینٹری سگنل نہیں ہے۔</p>"
        
    return html_out

def send_email_to_user(user_email, user_name, portfolio_data, market_report_html):
    if not SENDER_EMAIL or not SENDER_PASS or not user_email:
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛️ PSX & Crypto Daily AI Report - {user_name}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email
    
    full_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>السلام علیکم {user_name}!</h2>
        <p>پاکستان اسٹاک ایکسچینج اور عالمی کرپٹو مارکیٹ کی آج کی تفصیلی رپورٹ اور خرید و فروخت کے اہداف ذیل میں درج ہیں:</p>
        <hr>{market_report_html}<br>
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
    report_content = generate_separated_market_report()
    
    for user_name, u_info in users_db.items():
        user_email = u_info.get("email", "") if isinstance(u_info, dict) else ("masterjaved@gmail.com" if user_name.lower() == "javed" else "")
        if user_email:
            send_email_to_user(user_email, user_name, ports_db.get(user_name, {}), report_content)
