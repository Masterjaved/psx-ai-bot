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

def generate_separated_market_report():
    buy_list = []
    sell_list = []
    
    # 1. Crypto Scanning
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
                
                if rsi_c < 45:
                    buy_low = round(c_price * 0.995, 2)
                    buy_high = round(c_price * 1.008, 2)
                    tp1 = round(c_price + (atr * 1.5), 2)
                    tp2 = round(c_price + (atr * 3.0), 2)
                    sl = round(c_price - (atr * 1.5), 2)
                    
                    buy_list.append({
                        "ٹوکن / شیئر": f"🪙 {name}",
                        "موجودہ قیمت": f"${c_price:,.2f}",
                        "خریداری کی حد (Buy Range)": f"${buy_low} - ${buy_high}",
                        "پہلا ٹارگٹ (TP1)": f"${tp1}",
                        "دوسرا ٹارگٹ (TP2)": f"${tp2}",
                        "اسٹاپ لاس (SL)": f"${sl}"
                    })
                elif rsi_c > 65:
                    sell_list.append({
                        "ٹوکن / شیئر": f"🪙 {name}",
                        "موجودہ قیمت": f"${c_price:,.2f}",
                        "RSI": f"{rsi_c:.1f}",
                        "ہدایت": "🔴 منافع بک کریں / پوزیشن ختم کریں (Take Profit / Sell)"
                    })
        except Exception:
            pass

    # HTML Output Assembly
    html_out = "<h2>📊 روزانہ AI ٹریڈنگ الرٹس خلاصہ</h2>"
    
    html_out += "<h3>🟢 خریدنے والی کرنسیز و شیئرز (BUY Recommendations)</h3>"
    if buy_list:
        df_buy = pd.DataFrame(buy_list)
        html_out += df_buy.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت خریداری کے لیے کوئی نیا سگنل میچ نہیں ہوا۔</p>"
        
    html_out += "<br><hr><h3>🔴 بیچنے / منافع بک کرنے والے سگنلز (SELL / Exit Recommendations)</h3>"
    if sell_list:
        df_sell = pd.DataFrame(sell_list)
        html_out += df_sell.to_html(index=False, classes="table table-striped", border=1)
    else:
        html_out += "<p>اس وقت خروج یا سیلنگ کے لیے کوئی ایمرجنسی سگنل نہیں ہے۔</p>"
        
    return html_out

def send_email_to_user(user_email, user_name, portfolio_data, market_report_html):
    if not SENDER_EMAIL or not SENDER_PASS or not user_email:
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛️ PSX & Crypto AI بائے/سیل آٹو رپورٹ - {user_name}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email
    
    full_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>السلام علیکم {user_name}!</h2>
        <p>پاکستان اسٹاک ایکسچینج اور کرپٹو مارکیٹ کی آج کی خریدی و فروخت کی واضح ہدایات ذیل میں درج ہیں:</p>
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
