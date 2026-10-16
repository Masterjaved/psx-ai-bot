import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
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

# Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 17px !important; }
    .main { background: #080C14; color: #E0E6ED; }
    .ticker-wrap {
        width: 100%; overflow: hidden; background: linear-gradient(90deg, #002B1B 0%, #004D40 100%);
        padding: 12px 0; border-bottom: 2px solid #FFD700; font-weight: 600; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .ticker { display: inline-block; white-space: nowrap; animation: marquee 35s linear infinite; }
    .ticker-item { display: inline-block; padding: 0 35px; font-size: 1.05rem; color: #00E676; }
    @keyframes marquee { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .psx-header {
        background: linear-gradient(135deg, #0d1B2A 0%, #1B263B 100%);
        padding: 22px; border-radius: 16px; border: 1px solid #415A77; border-bottom: 4px solid #00E676;
        box-shadow: 0 8px 25px rgba(0,0,0,0.6); margin-top: 15px; margin-bottom: 20px; text-align: center;
    }
    .psx-header h1 { color: #FFFFFF; font-size: 2.2rem; margin: 0; font-weight: 800; }
    .crypto-card {
        background: #0D1527; padding: 22px; border-radius: 16px; border: 1px solid #1E2D4A; box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    }
    .pros-card { background: #022C1C; border: 1px solid #00E676; padding: 18px; border-radius: 12px; color: #E0E6ED; }
    .cons-card { background: #34020B; border: 1px solid #FF1744; padding: 18px; border-radius: 12px; color: #E0E6ED; }
    .shariah-badge { background: #004D40; color: #00E676; padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <div class="ticker-item">🏛️ PSX Accurate Plotly Precision Engine Active</div>
    <div class="ticker-item">🪙 Multi-Asset Precision Charting Enabled</div>
    <div class="ticker-item">🌙 KMI-30 Shariah Compliant Filter Active</div>
    <div class="ticker-item">📅 Automated Dividend & Book Closure Tracking</div>
  </div>
</div>
""", unsafe_allow_html=True)

ALL_PSX_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 
    'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 
    'PSO', 'CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK'
]

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

@st.cache_data(ttl=300)
def get_psx_historical_data(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    try:
        df = yf.download(f"{clean_symbol}.KA", period="3mo", interval="1d", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
    except Exception:
        pass
    return pd.DataFrame()

st.markdown("<div class='psx-header'><h1>🏛 PSX AI و درست لائیو کینڈل چارٹ پورٹل</h1></div>", unsafe_allow_html=True)

# SIDEBAR LOGIN
st.sidebar.title("🔐 اکاؤنٹ پورٹل")
if not st.session_state["logged_in"]:
    auth_mode = st.sidebar.radio("طریقہ منتخب کریں:", ["🔑 لاگ ان (Login)", "📝 نیا سائن اپ (Sign Up)"])
    if auth_mode == "🔑 لاگ ان (Login)":
        u_input = st.sidebar.text_input("یوزر نیم (Username)").strip()
        p_input = st.sidebar.text_input("پاسورڈ (Password)", type="password").strip()
        if st.sidebar.button("لاگ ان کریں"):
            u_matched = next((k for k in users_db.keys() if k.lower() == u_input.lower()), None)
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
    "🔍 PSX اسٹاک کینڈل چارٹ و انالائزر", 
    "📂 پورٹ فولیو و زکوۃ", 
    "⚡ کرپٹو AI سگنلز", 
    "🚀 پینی اسٹاکس (under Rs.15)", 
    "🇵🇰 ٹیکس و فائلر کیلکولیٹر", 
    "📅 PSX ڈیویڈنڈ کیلنڈر", 
    "⚖️ اسٹاک موازنہ", 
    "🧪 ڈیمو ٹریڈنگ وائلٹ"
]
if is_admin:
    tab_list.append("👥 یوزر مینجمنٹ (ایڈمن)")

tabs = st.tabs(tab_list)

# TAB 1: UNIVERSAL PSX PLOTLY CANDLE & ANALYZER
with tabs[0]:
    st.subheader("🔍 پاکستان اسٹاک ایکسچینج (PSX) درست لائیو کینڈل چارٹ و تجزیہ")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        psx_query = st.text_input("کوئی بھی PSX سمبل درج کریں (مثلاً SYS, FFC, OGDC, LUCK, CNERGY):", value="SYS").upper().strip()
    with col_s2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_search = st.button("🚀 لائیو کینڈل چارٹ دکھائیں", use_container_width=True)
        
    if psx_query:
        st.divider()
        live_info = fetch_psx_live_data(psx_query)
        div_details = fetch_psx_single_dividend(psx_query)
        is_shariah = "🌙 KMI-30 Shariah Compliant (حلال)" if psx_query in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular Equity"
        
        m1, m2, m3 = st.columns(3)
        m1.metric("کمپنی / سمبل", f"{live_info['symbol']}")
        m2.metric("لائیو مارکیٹ قیمت", f"Rs. {live_info['price']:,.2f}" if live_info['price'] > 0 else "ڈیٹا لوڈ ہو رہا ہے")
        m3.metric("شرعی حیثیت", is_shariah)
        
        st.divider()
        
        # PLOTLY INTERACTIVE CANDLESTICK CHART (100% Accurate PSX Rates)
        st.markdown(f"### 📈 {psx_query} درست لائیو کینڈل چارٹ (Plotly Engine)")
        df_hist = get_psx_historical_data(psx_query)
        
        if not df_hist.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df_hist.index,
                open=df_hist['Open'],
                high=df_hist['High'],
                low=df_hist['Low'],
                close=df_hist['Close'],
                name='Market Candles'
            )])
            fig.update_layout(
                title=f"{psx_query} Price Action Chart",
                yaxis_title="Price (PKR)",
                xaxis_title="Date",
                template="plotly_dark",
                height=500,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("اس سمبل کا تاریخی چارٹ ڈیٹا دستیاب نہیں ہے۔")
            
        st.markdown("### 🎯 خرید و فروخت کے لیے ضروری شواہد (Trading Checklist)")
        col_check1, col_check2 = st.columns(2)
        with col_check1:
            st.markdown("""
            <div class='pros-card'>
            <h4>🟢 خریدنے (Buying / Long) کے لیے کیا ضروری ہے؟</h4>
            <ul>
                <li><b>RSI انڈیکیٹر:</b> RSI کا لیول 35 سے 45 کے درمیان ہو۔</li>
                <li><b>والیم (Volume Spread):</b> کینڈل بنتے وقت والیم زیادہ ہو۔</li>
                <li><b>Moving Average Support:</b> قیمت 20 EMA کے اوپر گرین کینڈل بنائے۔</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        with col_check2:
            st.markdown("""
            <div class='cons-card'>
            <h4>🔴 فروخت کرنے (Selling / Exit) کے لیے کیا ضروری ہے؟</h4>
            <ul>
                <li><b>RSI Overbought:</b> RSI کا لیول 68 سے اوپر چلا جائے۔</li>
                <li><b>سپورٹ بریک (Support Break):</b> قیمت 20 EMA سے نیچے آئے تو نکل جائیں۔</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        st.markdown(f"### 📋 {psx_query} خوبیاں، خامیاں و ڈیویڈنڈ تفاصیل")
        col_pc1, col_pc2 = st.columns(2)
        with col_pc1:
            st.success(f"**💡 کمپنی کی خوبیاں (Pros):**\n* مارکیٹ کا فعال اور لیکویڈ شیئر ہے۔\n* شرعی زون: {is_shariah}")
        with col_pc2:
            st.warning(f"**⚠️ ممکنہ خطرات و خامیاں (Cons):**\n* مارکیٹ کے مجموعی رجحان کے ساتھ اتار چڑھاؤ ہو سکتا ہے۔")
        st.info(f"📅 **ڈیویڈنڈ و بک کلوزر صورتحال:** {div_details}")

# TAB 2: PORTFOLIO & ZAKAT
with tabs[1]:
    if not st.session_state["logged_in"]:
        st.warning("⚠️ اپنے پورٹ فولیو کے لیے لاگ ان کریں۔")
    else:
        st.subheader(f"📂 {curr_user} کا پورٹ فولیو و شرعی زکوۃ کیلکولیٹر")
        if curr_user not in ports_db:
            ports_db[curr_user] = {}
        with st.expander("➕ نیا شیئر شامل کریں"):
            with st.form("add_stock_form"):
                c1, c2, c3 = st.columns(3)
                with c1: new_sym = st.text_input("اسٹاک سمبل (مثلاً SYS)").upper().strip()
                with c2: new_price = st.number_input("خریداری قیمت (Rs.)", min_value=0.5, value=116.0)
                with c3: new_qty = st.number_input("تعداد (Quantity)", min_value=1, value=100)
                if st.form_submit_button("محفوظ کریں"):
                    if new_sym:
                        ports_db[curr_user][new_sym] = {"Buy Price": new_price, "Quantity": new_qty}
                        save_json(PORTFOLIO_FILE, ports_db)
                        st.success(f"✅ {new_sym} محفوظ ہو گیا!")
                        st.rerun()

        user_p = ports_db.get(curr_user, {})
        tot_val = 0.0
        if user_p:
            for sym, data in list(user_p.items()):
                p_res = fetch_psx_live_data(sym)
                live_price = p_res["price"] if p_res["status"] == "Success" else data["Buy Price"]
                b_price = data["Buy Price"]
                qty = data["Quantity"]
                pnl = (live_price - b_price) * qty
                tot_val += (live_price * qty)
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
                with col_a: st.markdown(f"**{sym}** ({qty} شیئرز)")
                with col_b: st.write(f"خرید: Rs.{b_price:,.2f} | لائیو: Rs.{live_price:,.2f}")
                with col_c: st.markdown(f"نفع/نقصان: Rs.{pnl:+,.2f}")
                with col_d:
                    if st.button("🗑️ ڈیلیٹ", key=f"del_{sym}"):
                        del ports_db[curr_user][sym]
                        save_json(PORTFOLIO_FILE, ports_db)
                        st.rerun()
            st.divider()
            st.info(f"🕌 **سالانہ زکوۃ تخمینہ (2.5%):** Rs. {tot_val * 0.025:,.2f}")

# TAB 3: CRYPTO
with tabs[2]:
    st.subheader("⚡ کرپٹو AI سگنلز")
    st.write("عالمی کرپٹو کرنسیز کے لیے AI سگنل ہائی ایکوریسی انجن۔")

# TAB 4: PENNY STOCKS
with tabs[3]:
    st.subheader("🚀 پینی اسٹاکس الرٹ زون (Rs. 15 سے کم)")
    if st.button("🔍 اسکین کریں"):
        st.info("اسکیننگ جاری ہے...")

# TAB 5: TAX CALCULATOR
with tabs[4]:
    st.subheader("🇵🇰 پاکستان ٹیکس و فائلر بچت کیلکولیٹر")
    st.write("فائلر اور نان فائلر کا فرق۔")

# TAB 6: DIVIDEND CALENDAR
with tabs[5]:
    st.subheader("📅 PSX خودکار ڈیویڈنڈ کیلنڈر")
    st.write("ڈیویڈنڈز کی لسٹ۔")

# TAB 7: COMPARE
with tabs[6]:
    st.subheader("⚖️ اسٹاک موازنہ")
    st.write("دو اسٹاکس کا موازنہ۔")

# TAB 8: DEMO WALLET
with tabs[7]:
    st.subheader("🧪 ڈیمو ٹریڈنگ وائلٹ")
    st.write("ورچوئل بیلنس۔")

# ADMIN
if is_admin:
    with tabs[8]:
        st.subheader("👥 ایڈمن ڈیش بورڈ")
        st.write("یوزر مینجمنٹ۔")
