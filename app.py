import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
from bs4 import BeautifulSoup
import yfinance as yf
import streamlit.components.v1 as components
import time
import urllib.parse

st.set_page_config(
    page_title="PSX & Crypto Institutional Precision Engine",
    page_icon="🏛️",
    layout="wide"
)

# Secrets & File Paths
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
REPO_NAME = st.secrets.get("REPO_NAME", "Masterjaved/psx-ai-bot")
PORTFOLIO_FILE = "portfolios_db.json"
USERS_FILE = "users_db.json"
DEMO_TRADES_FILE = "demo_trades_db.json"

def sync_file_to_github(file_path, data):
    if not GITHUB_TOKEN:
        return False
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha", "") if res.status_code == 200 else ""
        content_str = json.dumps(data, indent=4, ensure_ascii=False)
        encoded_content = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        payload = {
            "message": f"Auto-sync {file_path}",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def load_json(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                res = json.load(f)
                return res if res else default_data
        except Exception:
            return default_data
    return default_data

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    sync_file_to_github(file_path, data)

users_db = load_json(USERS_FILE, {})
if "javed" not in users_db:
    users_db["javed"] = {"pass": "javed123", "email": "masterjaved@gmail.com"}

ports_db = load_json(PORTFOLIO_FILE, {})
demo_db = load_json(DEMO_TRADES_FILE, {})

query_params = st.query_params
saved_user = query_params.get("user", "")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

if saved_user and saved_user in users_db and not st.session_state["logged_in"]:
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = saved_user

# Ultra-Professional Dark Fintech Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 17px !important; }
    .main { background: #080C14; color: #E0E6ED; }
    
    .ticker-wrap {
        width: 100%; overflow: hidden; background: linear-gradient(90deg, #002B1B 0%, #004D40 100%);
        padding: 12px 0; border-bottom: 2px solid #FFD700; font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .ticker { display: inline-block; white-space: nowrap; animation: marquee 35s linear infinite; }
    .ticker-item { display: inline-block; padding: 0 35px; font-size: 1.05rem; color: #00E676; }
    @keyframes marquee { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    
    .psx-header {
        background: linear-gradient(135deg, #0d1B2A 0%, #1B263B 100%);
        padding: 25px; border-radius: 16px; border: 1px solid #415A77;
        border-bottom: 4px solid #00E676;
        box-shadow: 0 8px 25px rgba(0,0,0,0.6); margin-top: 15px; margin-bottom: 25px; text-align: center;
    }
    .psx-header h1 { color: #FFFFFF; font-size: 2.3rem; margin: 0; font-weight: 800; letter-spacing: 0.5px; }
    
    .crypto-card {
        background: #0D1527; padding: 25px; border-radius: 16px;
        border: 1px solid #1E2D4A; box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    }
    .pros-card {
        background: #022C1C; border: 1px solid #00E676; padding: 18px; border-radius: 12px; color: #E0E6ED;
    }
    .cons-card {
        background: #34020B; border: 1px solid #FF1744; padding: 18px; border-radius: 12px; color: #E0E6ED;
    }
    .shariah-badge {
        background: #004D40; color: #00E676; padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# LIVE RUNNING TICKER TAPE
st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <div class="ticker-item">🏛️ PSX Dynamic Candle Engine & Universal Search Active</div>
    <div class="ticker-item">🪙 Multi-Asset Precision Charting Enabled</div>
    <div class="ticker-item">🌙 KMI-30 Shariah Compliant Filter Active</div>
    <div class="ticker-item">📅 Automated Dividend & Book Closure Tracking</div>
  </div>
</div>
""", unsafe_allow_html=True)

SHARIAH_COMPLIANT_STOCKS = ['FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 'POL', 'MEBL', 'MARI']

@st.cache_data(ttl=120)
def fetch_psx_live_data(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_div = soup.find("div", {"class": "quote__close"})
            name_div = soup.find("div", {"class": "quote__name"})
            comp_name = name_div.text.strip() if name_div else clean_symbol
            if price_div:
                price = float(price_div.text.strip().replace("Rs.", "").replace(",", ""))
                return {"symbol": clean_symbol, "name": comp_name, "price": price, "status": "Success"}
    except Exception:
        pass
    return {"symbol": clean_symbol, "name": clean_symbol, "price": 0.0, "status": "Error"}

@st.cache_data(ttl=300)
def fetch_psx_single_dividend(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    div_info = "فی الوقت کوئی نیا بک کلوزر یا ڈیویڈنڈ کی خبر نہیں ہے۔"
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tables = soup.find_all("table")
            for tbl in tables:
                if "Payout" in tbl.text or "Dividend" in tbl.text or "Closure" in tbl.text:
                    rows = tbl.find_all("tr")
                    if len(rows) > 1:
                        div_info = rows[1].text.strip().replace("\n", " - ")
                        break
    except Exception:
        pass
    return div_info

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

st.markdown("<div class='psx-header'><h1>🏛 PSX AI و عالمی مارکیٹ کینڈل تجزیہ پورٹل</h1></div>", unsafe_allow_html=True)

st.sidebar.title("🔐 اکاؤنٹ پورٹل")

if not st.session_state["logged_in"]:
    auth_mode = st.sidebar.radio("طریقہ منتخب کریں:", ["🔑 لاگ ان (Login)", "📝 نیا سائن اپ (Sign Up)"])
    if auth_mode == "🔑 لاگ ان (Login)":
        u_input = st.sidebar.text_input("یوزر نیم (Username)").strip()
        p_input = st.sidebar.text_input("پاسورڈ (Password)", type="password").strip()
        if st.sidebar.button("لاگ ان کریں"):
            u_matched = None
            for key in users_db.keys():
                if key.lower() == u_input.lower():
                    u_matched = key
                    break
            if u_matched and users_db[u_matched].get("pass") == p_input:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = u_matched
                st.query_params["user"] = u_matched
                st.sidebar.success(f"خوش آمدید {u_matched}!")
                st.rerun()
            else:
                st.sidebar.error("غلط یوزر نیم یا پاسورڈ!")
    else:
        new_u = st.sidebar.text_input("نیا یوزر نیم").strip()
        new_e = st.sidebar.text_input("ای میل ایڈریس").strip()
        new_p = st.sidebar.text_input("نیا پاسورڈ", type="password").strip()
        if st.sidebar.button("رجسٹر کریں"):
            users_db[new_u] = {"pass": new_p, "email": new_e}
            save_json(USERS_FILE, users_db)
            st.sidebar.success("✅ رجسٹریشن کامیاب!")
else:
    st.sidebar.success(f"لاگ ان بطور: **{st.session_state['user_id']}**")
    if st.sidebar.button("لاگ آؤٹ"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.query_params.clear()
        st.rerun()

curr_user = st.session_state["user_id"]
is_admin = (curr_user.lower() == "javed")

tab_list = [
    "🔍 PSX اسٹاک کینڈل و انالائزر", 
    "⚖️ کسی بھی دو اسٹاکس کا موازنہ", 
    "⚡ کرپٹو AI سگنلز", 
    "📂 پورٹ فولیو و زکوۃ", 
    "🇵🇰 ٹیکس و فائلر کیلکولیٹر", 
    "📅 PSX ڈیویڈنڈ کیلنڈر", 
    "🧪 ڈیمو ٹریڈنگ وائلٹ"
]
if is_admin:
    tab_list.append("👥 یوزر مینجمنٹ (ایڈمن)")

tabs = st.tabs(tab_list)

# TAB 1: UNIVERSAL PSX CANDLE & COMPREHENSIVE STOCK ANALYZER
with tabs[0]:
    st.subheader("🔍 پاکستان اسٹاک ایکسچینج (PSX) عالمگیر کینڈل سرچ و تجزیہ پورٹل")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        psx_query = st.text_input("پاکستان اسٹاک ایکسچینج کا کوئی بھی سمبل درج کریں (مثلاً CNERGY, FFC, OGDC, AIRLINK, TELE, LUCK, PPL):", value="OGDC").upper().strip()
    with col_s2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_search = st.button("🚀 لائیو کینڈل چارٹ و تجزیہ دکھائیں", use_container_width=True)
        
    if psx_query:
        st.divider()
        live_info = fetch_psx_live_data(psx_query)
        div_details = fetch_psx_single_dividend(psx_query)
        is_shariah = "🌙 KMI-30 Shariah Compliant (حلال)" if psx_query in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular Equity"
        
        # Header Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("کمپنی / سمبل", f"{live_info['symbol']}")
        m2.metric("لائیو مارکیٹ قیمت", f"Rs. {live_info['price']:,.2f}" if live_info['price'] > 0 else "ڈیٹا لوڈ ہو رہا ہے")
        m3.metric("شرعی حیثیت", is_shariah)
        
        st.divider()
        
        # 1. LIVE TRADINGVIEW CANDLESTICK CHART
        st.markdown(f"### 📈 {psx_query} لائیو کینڈل چارٹ (TradingView Integration)")
        tv_psx_symbol = f"PSX:{psx_query}"
        tv_html = f"""
        <div class="tradingview-widget-container">
          <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_psx&symbol={tv_psx_symbol}&interval=D&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=['RSI@tv-basicstudies','MASimple@tv-basicstudies']&theme=dark&style=1&timezone=Asia%2FKarachi" width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
        </div>
        """
        components.html(tv_html, height=520)
        
        # 2. BUYING & SELLING CONFLUENCE CHECKLIST
        st.markdown("### 🎯 خرید و فروخت کے لیے ضروری شواہد (Trading Checklist)")
        col_check1, col_check2 = st.columns(2)
        
        with col_check1:
            st.markdown("""
            <div class='pros-card'>
            <h4>🟢 خریدنے (Buying / Long) کے لیے کیا ضروری ہے؟</h4>
            <ul>
                <li><b>RSI انڈیکیٹر:</b> RSI کا لیول 35 سے 45 کے درمیان ہو (Oversold Zone)۔</li>
                <li><b>والیم (Volume Spread):</b> کینڈل بنتے وقت والیم پچھلے 10 دنوں کی اوسط سے زیادہ ہونا چاہیے۔</li>
                <li><b>Moving Average Support:</b> قیمت 20 EMA یا 50 EMA کے اوپر گرین کینڈل بنائے۔</li>
                <li><b>بریک آؤٹ:</b> پچھلے ریزسٹنس (Resistance Level) کو والیم کے ساتھ توڑے۔</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col_check2:
            st.markdown("""
            <div class='cons-card'>
            <h4>🔴 فروخت کرنے (Selling / Exit) کے لیے کیا ضروری ہے؟</h4>
            <ul>
                <li><b>RSI Overbought:</b> RSI کا لیول 68 یا 70 سے اوپر چلا جائے (منافع بک کریں)۔</li>
                <li><b>سپورٹ بریک (Support Break):</b> اگر قیمت 20 EMA سے نیچے لال کینڈل بند کرے۔</li>
                <li><b>والیوم ڈراپ:</b> قیمت تو بڑھے لیکن والیم مسلسل کم ہو رہا ہو (فیک ریلی)۔</li>
                <li><b>اسٹاپ لاس (SL):</b> نقصان سے بچاؤ کے لیے اپنے خریدی ریٹ سے 3% نیچے پر لازمی نکلیں۔</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        # 3. PROS & CONS + DIVIDEND DETAILS
        st.markdown(f"### 📋 {psx_query} فائنینشل خوبیاں، خامیاں و ڈیویڈنڈ تفاصیل")
        col_pc1, col_pc2 = st.columns(2)
        
        with col_pc1:
            st.success(f"**💡 کمپنی کی خوبیاں (Pros):**\n* مارکیٹ کا اہم اور لیکویڈ شیئر ہے۔\n* انسٹٹیوشنل بائنگ اور باقاعدہ ٹریڈنگ والیم موجود ہے۔\n* شرعی لحاظ سے تصدیق شدہ زون: {is_shariah}")
            
        with col_pc2:
            st.warning(f"**⚠️ ممکنہ خطرات و خامیاں (Cons):**\n* مارکیٹ اور KSE-100 انڈیکس کے پریشر کے ساتھ نیچے جا سکتا ہے۔\n* ٹیکس اور ریگولیٹری پالیسیوں کا براہِ راست اثر ہوتا ہے۔")
            
        st.info(f"📅 **ڈیویڈنڈ و بک کلوزر صورتحال (Dividend Status):** {div_details}")

# TAB 2: COMPARE ANY TWO PSX STOCKS
with tabs[1]:
    st.subheader("⚖️ پاکستان اسٹاک ایکسچینج کی کسی بھی دو کمپنیوں کا موازنہ")
    c1, c2 = st.columns(2)
    with c1:
        comp_s1 = st.text_input("پہلا اسٹاک سمبل درج کریں:", value="FFC").upper().strip()
    with c2:
        comp_s2 = st.text_input("دوسرا اسٹاک سمبل درج کریں:", value="EFERT").upper().strip()
        
    if st.button("📊 موازنہ شروع کریں"):
        d1 = fetch_psx_live_data(comp_s1)
        d2 = fetch_psx_live_data(comp_s2)
        
        comp_df = pd.DataFrame({
            "میٹرک (Metrics)": ["اسٹاک سمبل", "لائیو قیمت (PKR)", "شرعی حیثیت (Shariah)", "ڈیویڈنڈ اسٹیٹس"],
            comp_s1: [d1['symbol'], f"Rs. {d1['price']:,.2f}", "🌙 Shariah" if comp_s1 in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular", fetch_psx_single_dividend(comp_s1)],
            comp_s2: [d2['symbol'], f"Rs. {d2['price']:,.2f}", "🌙 Shariah" if comp_s2 in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular", fetch_psx_single_dividend(comp_s2)]
        })
        st.dataframe(comp_df, use_container_width=True)

# TAB 3: CRYPTO SIGNALS
with tabs[2]:
    st.subheader("⚡ کرپٹو AI سگنلز")
    st.write("عالمی کرپٹو کرنسیز کے لیے AI سگنل ہائی ایکوریسی انجن۔")

# TAB 4: PORTFOLIO & ZAKAT
with tabs[3]:
    st.subheader("📂 پورٹ فولیو مینیجر و زکوۃ کیلکولیٹر")
    st.write("آپ کا ذاتی پورٹ فولیو اور خودکار زکوۃ کا حساب۔")

# TAB 5: TAX & FILER
with tabs[4]:
    st.subheader("🇵🇰 پاکستان ٹیکس و فائلر بچت کیلکولیٹر")
    st.write("فائلر اور نان فائلر کے ٹیکس کا فرق اور خالص بچت۔")

# TAB 6: DIVIDEND CALENDAR
with tabs[5]:
    st.subheader("📅 PSX خودکار ڈیویڈنڈ کیلنڈر")
    st.write("تمام کمپنیوں کے آنے والے ڈیویڈنڈز کی مکمل لسٹ۔")

# TAB 7: DEMO WALLET
with tabs[6]:
    st.subheader("🧪 ڈیمو (Paper Trading) وائلٹ")
    st.write("ورچوئل بیلنس اور ون-ریٹ اینالیٹکس۔")

# ADMIN
if is_admin:
    with tabs[7]:
        st.subheader("👥 ایڈمن ڈیش بورڈ")
        st.write("یوزر مینجمنٹ پورٹل۔")
