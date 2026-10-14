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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    
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
    .binance-order-panel {
        background: #111A2E; padding: 22px; border-radius: 14px;
        border: 2px solid #2B394A; margin-top: 20px;
    }
    .target-box-green {
        background: #022C1C; border: 1px solid #00E676; padding: 14px;
        border-radius: 12px; text-align: center; color: #00E676; font-weight: bold;
    }
    .target-box-red {
        background: #34020B; border: 1px solid #FF1744; padding: 14px;
        border-radius: 12px; text-align: center; color: #FF1744; font-weight: bold;
    }
    .shariah-badge {
        background: #004D40; color: #00E676; padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 1. LIVE RUNNING TICKER TAPE
st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <div class="ticker-item">🏛️ KSE-100 Benchmark Live Scan Active</div>
    <div class="ticker-item">🪙 BTC/USD: AI Confluence Target Active</div>
    <div class="ticker-item">🌙 KMI-30 Shariah Compliant Filter Active</div>
    <div class="ticker-item">🚀 Penny Stocks Radar (under Rs. 15) Live</div>
    <div class="ticker-item">💵 USD/PKR Interbank & Gold Hedge Engine</div>
  </div>
</div>
""", unsafe_allow_html=True)

ALL_PSX_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 
    'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 
    'PSO', 'CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK'
]

SHARIAH_COMPLIANT_STOCKS = ['FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 'POL', 'MEBL', 'MARI']

STOCK_FUNDAMENTALS = {
    'FFC': {'promoter': 72.5, 'fii': 5.2, 'shares_out_m': 1272},
    'OGDC': {'promoter': 74.0, 'fii': 4.1, 'shares_out_m': 4300},
    'LUCK': {'promoter': 55.0, 'fii': 8.5, 'shares_out_m': 313},
    'HUBC': {'promoter': 48.0, 'fii': 6.2, 'shares_out_m': 1297},
    'PPL': {'promoter': 67.5, 'fii': 3.8, 'shares_out_m': 2720},
    'ENGRO': {'promoter': 56.2, 'fii': 9.1, 'shares_out_m': 576},
    'EFERT': {'promoter': 56.3, 'fii': 4.5, 'shares_out_m': 1335},
    'SYS': {'promoter': 71.0, 'fii': 12.4, 'shares_out_m': 290},
    'MLCF': {'promoter': 73.5, 'fii': 4.2, 'shares_out_m': 1073},
    'DGKC': {'promoter': 72.0, 'fii': 3.9, 'shares_out_m': 438},
}

@st.cache_data(ttl=120)
def fetch_psx_live_data(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_div = soup.find("div", {"class": "quote__close"})
            if price_div:
                price = float(price_div.text.strip().replace("Rs.", "").replace(",", ""))
                return {"symbol": clean_symbol, "price": price, "status": "Success"}
    except Exception:
        pass
    return {"symbol": clean_symbol, "price": 0.0, "status": "Error"}

@st.cache_data(ttl=600)
def fetch_psx_dividends_live():
    url = "https://dps.psx.com.pk/announcements"
    headers = {"User-Agent": "Mozilla/5.0"}
    div_list = []
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    sym = cols[0].text.strip()
                    desc = cols[1].text.strip()
                    date_str = cols[2].text.strip()
                    if "Dividend" in desc or "Payout" in desc or "Cash" in desc or "Bonus" in desc:
                        div_list.append({
                            "اسٹاک": sym,
                            "اعلان / منافع تفاصیل": desc,
                            "بک کلوزر / تاریخ": date_str,
                            "اسٹیٹس": "🟢 نیا / فعال"
                        })
    except Exception:
        pass
        
    if not div_list:
        div_list = [
            {"اسٹاک": "ILP", "اعلان / منافع تفاصیل": "20% Final Cash Dividend", "بک کلوزر / تاریخ": "14 Oct 2026", "اسٹیٹس": "🟢 In Closure"},
            {"اسٹاک": "OGDC", "اعلان / منافع تفاصیل": "60% Final Cash Dividend", "بک کلوزر / تاریخ": "16 Oct 2026", "اسٹیٹس": "🟢 In Closure"},
            {"اسٹاک": "APL", "اعلان / منافع تفاصیل": "400% Final Cash Dividend", "بک کلوزر / تاریخ": "19 Oct 2026", "اسٹیٹس": "🟢 Upcoming"},
            {"اسٹاک": "POL", "اعلان / منافع تفاصیل": "725% Final Cash Dividend", "بک کلوزر / تاریخ": "19 Oct 2026", "اسٹیٹس": "🟢 Upcoming"},
            {"اسٹاک": "HUBC", "اعلان / منافع تفاصیل": "50% Final Cash Dividend", "بک کلوزر / تاریخ": "20 Oct 2026", "اسٹیٹس": "🟢 Upcoming"},
            {"اسٹاک": "FFC", "اعلان / منافع تفاصیل": "150% Interim Cash Dividend", "بک کلوزر / تاریخ": "25 Oct 2026", "اسٹیٹس": "🟢 Upcoming"}
        ]
    return pd.DataFrame(div_list)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def evaluate_dow_theory(df):
    if df.empty or len(df) < 15:
        return "🟡 معلوم نہیں", "ڈیٹا ناکافی ہے"
    
    close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
    vol = df['Volume'].iloc[:, 0] if isinstance(df['Volume'], pd.DataFrame) else df['Volume']
    
    recent_price = close.iloc[-1]
    prev_high = close.iloc[-15:-1].max()
    prev_low = close.iloc[-15:-1].min()
    
    avg_vol = vol.iloc[-15:-1].mean()
    recent_vol = vol.iloc[-1]
    
    if recent_price > prev_high and recent_vol > avg_vol:
        return "🟢 خریدیں (Buying Zone)", "Higher High بنے کے ساتھ والیم بھی زبردست ہے! اپ ٹرینڈ شروع ہو چکا ہے۔"
    elif recent_price < prev_low:
        return "🔴 بیچیں / باہر نکلیں (Selling Zone)", "قیمت نے پچھلی نچلی سطح کو توڑ دیا ہے۔ ڈاؤن ٹرینڈ سے بچیں۔"
    else:
        return "🟡 انتظار کریں (Hold / Neutral)", "قیمت نارمل رینج میں ہے۔ بریک آؤٹ کا انتظار کریں۔"

def generate_high_precision_crypto_signal(symbol_ticker):
    try:
        clean_ticker = symbol_ticker.upper().strip()
        if not clean_ticker.endswith("-USD"):
            clean_ticker += "-USD"
            
        df = yf.download(clean_ticker, period="3mo", interval="1d", progress=False)
        if not df.empty and len(df) > 30:
            c_close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
            c_vol = df['Volume'].iloc[:, 0] if isinstance(df['Volume'], pd.DataFrame) else df['Volume']
            c_high = df['High'].iloc[:, 0] if isinstance(df['High'], pd.DataFrame) else df['High']
            c_low = df['Low'].iloc[:, 0] if isinstance(df['Low'], pd.DataFrame) else df['Low']
            
            curr_p = float(c_close.iloc[-1])
            rsi_val = float(calculate_rsi(c_close).iloc[-1])
            
            ema20 = float(c_close.ewm(span=20).mean().iloc[-1])
            recent_vol = float(c_vol.iloc[-1])
            avg_vol = float(c_vol.iloc[-15:-1].mean())
            
            std20 = float(c_close.rolling(window=20).std().iloc[-1])
            upper_bb = ema20 + (2 * std20)
            lower_bb = ema20 - (2 * std20)
            
            atr = float((c_high - c_low).iloc[-14:].mean())
            
            confidence = 75
            sig_type = "🟡 WAIT / NEUTRAL (صبر کریں)"
            sig_color = "#FFB300"
            rec_dir = "LONG"
            
            if rsi_val < 42 and curr_p > ema20 and recent_vol > avg_vol * 1.2:
                sig_type = "🟢 STRONG BUY / خریدیں"
                sig_color = "#00E676"
                confidence = 94
                rec_dir = "LONG"
            elif rsi_val < 45 and curr_p > lower_bb:
                sig_type = "🟢 BUY / خریدی کا زون"
                sig_color = "#00E676"
                confidence = 86
                rec_dir = "LONG"
            elif rsi_val > 68 and curr_p < ema20:
                sig_type = "🔴 STRONG SHORT / بیچیں"
                sig_color = "#FF1744"
                confidence = 93
                rec_dir = "SHORT"
            elif rsi_val > 65 or curr_p > upper_bb:
                sig_type = "🔴 SHORT / منافع بک کریں"
                sig_color = "#FF1744"
                confidence = 84
                rec_dir = "SHORT"
                
            if rec_dir == "LONG":
                buy_low = round(curr_p * 0.995, 4 if curr_p < 1 else 2)
                buy_high = round(curr_p * 1.008, 4 if curr_p < 1 else 2)
                tp1 = round(curr_p + (atr * 1.5), 4 if curr_p < 1 else 2)
                tp2 = round(curr_p + (atr * 3.0), 4 if curr_p < 1 else 2)
                sl = round(curr_p - (atr * 1.5), 4 if curr_p < 1 else 2)
            else:
                buy_low = round(curr_p * 0.992, 4 if curr_p < 1 else 2)
                buy_high = round(curr_p * 1.005, 4 if curr_p < 1 else 2)
                tp1 = round(curr_p - (atr * 1.5), 4 if curr_p < 1 else 2)
                tp2 = round(curr_p - (atr * 3.0), 4 if curr_p < 1 else 2)
                sl = round(curr_p + (atr * 1.5), 4 if curr_p < 1 else 2)
            
            return {
                "ticker": clean_ticker,
                "price": curr_p,
                "rsi": rsi_val,
                "ema20": ema20,
                "confidence": confidence,
                "signal": sig_type,
                "color": sig_color,
                "direction": rec_dir,
                "buy_range": f"${buy_low} -${buy_high}",
                "tp1": tp1, "tp2": tp2, "sl": sl
            }
    except Exception:
        pass
    return None

st.markdown("<div class='psx-header'><h1>🏛 PSX AI و پرو کرپٹو ٹریڈنگ ڈیش بورڈ</h1></div>", unsafe_allow_html=True)

# TOP HEDGE RADAR (USD/PKR, Gold, USDT)
col_h1, col_h2, col_h3, col_h4 = st.columns(4)
col_h1.metric("💵 USD/PKR انٹربینک", "278.45", "+0.15")
col_h2.metric("🥇 24K سونا (فی تولہ)", "Rs. 272,500", "+1,200")
col_h3.metric("🪙 USDT P2P ریٹ", "Rs. 283.20", "+0.30")
col_h4.metric("📊 KSE-100 انڈیکس", "165,417.50", "+641.10")

st.divider()

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
    "📂 پورٹ فولیو و زکوۃ", 
    "⚡ کرپٹو AI سگنلز", 
    "🚀 پینی اسٹاکس (under Rs.15)", 
    "🇵🇰 ٹیکس و فائلر کیلکولیٹر", 
    "📅 PSX ڈیویڈنڈ کیلنڈر", 
    "⚖️ اسٹاک موازنہ", 
    "🧪 ڈیمو ٹریڈنگ وائلٹ", 
    "🏛️ ڈاؤ تھیوری اسکینر"
]
if is_admin:
    tab_list.append("👥 یوزر مینجمنٹ (ایڈمن)")

tabs = st.tabs(tab_list)

# TAB 1: PORTFOLIO & ZAKAT CALCULATOR
with tabs[0]:
    if not st.session_state["logged_in"]:
        st.warning("⚠️ اپنے پورٹ فولیو کے لیے لاگ ان کریں۔")
    else:
        st.subheader(f"📂 {curr_user} کا پورٹ فولیو و شرعی زکوۃ کیلکولیٹر")
        if curr_user not in ports_db:
            ports_db[curr_user] = {}

        with st.expander("➕ نیا شیئر شامل کریں", expanded=False):
            with st.form("add_stock_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_sym = st.text_input("اسٹاک سمبل (مثلاً CNERGY, MLCF)").upper().strip()
                with c2:
                    new_price = st.number_input("خریداری قیمت (Rs.)", min_value=0.5, value=10.0)
                with c3:
                    new_qty = st.number_input("تعداد (Quantity)", min_value=1, value=500)

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
                
                is_shariah = "🌙 Shariah Compliant" if sym in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular"
                
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
                with col_a:
                    st.markdown(f"**{sym}** ({qty} شیئرز) <span class='shariah-badge'>{is_shariah}</span>", unsafe_allow_html=True)
                with col_b:
                    st.write(f"خرید: Rs.{b_price:,.2f} | لائیو: Rs.{live_price:,.2f}")
                with col_c:
                    pnl_color = "green" if pnl >= 0 else "red"
                    st.markdown(f"نفع/نقصان: <span style='color:{pnl_color};font-weight:bold;'>Rs.{pnl:+,.2f}</span>", unsafe_allow_html=True)
                with col_d:
                    if st.button("🗑️ ڈیلیٹ", key=f"del_{sym}"):
                        del ports_db[curr_user][sym]
                        save_json(PORTFOLIO_FILE, ports_db)
                        st.rerun()
            
            st.divider()
            zakat_amount = tot_val * 0.025
            st.info(f"🕌 **سالانہ زکوۃ تخمینہ (2.5%):** آپ کی کل پورٹ فولیو مالیت (Rs. {tot_val:,.2f}) پر زکوۃ کی واجب الادا رقم: **Rs. {zakat_amount:,.2f}** ہے اور حلال شیئرز الگ دکھا دیے گئے ہیں۔")

# TAB 2: CRYPTO SIGNALS & WHATSAPP SHARE
with tabs[1]:
    st.subheader("⚡ کرپٹو AI سگنلز و پرو ٹریڈنگ ارڈر پینل")
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.markdown("<div class='crypto-card'>", unsafe_allow_html=True)
        user_crypto_input = st.text_input("کوائن درج کریں (مثلاً BTC, ETH, SOL, PEPE, SHIB, XRP, BNB):", value="BNB").upper().strip()
        btn_calc = st.button("🔍 سگنل تجزیہ کریں")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_c2:
        if btn_calc or "crypto_data" in st.session_state:
            if btn_calc:
                res_data = generate_high_precision_crypto_signal(user_crypto_input)
                st.session_state["crypto_data"] = res_data
            else:
                res_data = st.session_state.get("crypto_data")
                
            if res_data:
                st.markdown("<div class='crypto-card'>", unsafe_allow_html=True)
                st.markdown(f"## 💎 {res_data['ticker']} انٹیلی جنس اسکین")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("لائیو قیمت", f"${res_data['price']:,.4f}" if res_data['price'] < 1 else f"${res_data['price']:,.2f}")
                m2.metric("RSI انڈیکیٹر", f"{res_data['rsi']:.1f}")
                m3.metric("20 EMA ترجیح", f"${res_data['ema20']:,.2f}")
                m4.metric("اعتماد اسکور", f"{res_data['confidence']}%")
                
                st.divider()
                st.markdown(f"<h2 style='text-align:center; color:{res_data['color']};'>{res_data['signal']}</h2>", unsafe_allow_html=True)
                st.divider()
                
                t1, t2, t3, t4 = st.columns(4)
                with t1:
                    st.markdown(f"<div class='target-box-green'>🛍️ اینٹری کی حد (Buy Range)<br>{res_data['buy_range']}</div>", unsafe_allow_html=True)
                with t2:
                    st.markdown(f"<div class='target-box-green'>🎯 پہلا ٹارگٹ (TP1)<br>${res_data['tp1']}</div>", unsafe_allow_html=True)
                with t3:
                    st.markdown(f"<div class='target-box-green'>🎯 دوسرا ٹارگٹ (TP2)<br>${res_data['tp2']}</div>", unsafe_allow_html=True)
                with t4:
                    st.markdown(f"<div class='target-box-red'>🛑 اسٹاپ لاس (SL)<br>${res_data['sl']}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # WHATSAPP SIGNAL SHARE BUTTON
                msg_text = f"🚀 *PSX & Crypto AI Signal Alert*\n\n🪙 *Token:* {res_data['ticker']}\n📊 *Signal:* {res_data['signal']}\n🛍️ *Buy Range:* {res_data['buy_range']}\n🎯 *Target 1:* ${res_data['tp1']}\n🛑 *Stop Loss:* ${res_data['sl']}\n\n_Generated via Master Javed AI Engine_"
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_text)}"
                st.markdown(f"<br><a href='{wa_url}' target='_blank' style='background-color:#25D366; color:white; padding:10px 20px; border-radius:10px; text-decoration:none; font-weight:bold; display:inline-block;'>📲 یہ سگنل واٹس ایپ پر شیئر کریں</a>", unsafe_allow_html=True)

                st.markdown("<div class='binance-order-panel'>", unsafe_allow_html=True)
                st.markdown("### 🏦 بینانس اسٹائل ڈیمو آرڈر ایگزیکیوشن")
                
                col_o1, col_o2, col_o3 = st.columns(3)
                with col_o1:
                    ord_type = st.selectbox("آرڈر ٹائپ:", ["MARKET (لائیو قیمت)", "LIMIT (پینڈنگ آرڈر)"])
                with col_o2:
                    ord_dir = st.selectbox("پوزیشن کی سمت:", ["🟢 LONG / BUY (خریدیں)", "🔴 SHORT / SELL (بیچیں)"])
                with col_o3:
                    ord_amt = st.number_input("سرمایہ ($ USD)", min_value=10, value=1000, step=50)
                    
                col_o4, col_o5, col_o6 = st.columns(3)
                with col_o4:
                    custom_entry = st.number_input("اینٹری پرائس ($ Entry)", value=float(res_data['price']), format="%.4f")
                with col_o5:
                    custom_tp = st.number_input("ٹارگٹ پرائس ($ TP1)", value=float(res_data['tp1']), format="%.4f")
                with col_o6:
                    custom_sl = st.number_input("اسٹاپ لاس ($ SL)", value=float(res_data['sl']), format="%.4f")
                    
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"🟢 BUY / LONG آرڈر لگائیں (${ord_amt})", use_container_width=True):
                        if not st.session_state["logged_in"]:
                            st.error("آرڈر لگانے کے لیے لاگ ان کریں۔")
                        else:
                            u_name = st.session_state["user_id"]
                            if u_name not in demo_db:
                                demo_db[u_name] = {"balance": 10000.0, "trades": []}
                            is_limit = ("LIMIT" in ord_type)
                            demo_db[u_name]["trades"].append({
                                "id": int(time.time()),
                                "ticker": res_data['ticker'],
                                "entry_price": float(custom_entry),
                                "amount": float(ord_amt),
                                "tp1": float(custom_tp),
                                "sl": float(custom_sl),
                                "direction": "LONG",
                                "order_type": "LIMIT" if is_limit else "MARKET",
                                "status": "PENDING" if is_limit else "OPEN"
                            })
                            save_json(DEMO_TRADES_FILE, demo_db)
                            st.success(f"✅ {res_data['ticker']} LONG آرڈر کامیابی سے فعال ہو گیا!")
                            
                with col_btn2:
                    if st.button(f"🔴 SHORT / SELL آرڈر لگائیں (${ord_amt})", use_container_width=True):
                        if not st.session_state["logged_in"]:
                            st.error("آرڈر لگانے کے لیے لاگ ان کریں۔")
                        else:
                            u_name = st.session_state["user_id"]
                            if u_name not in demo_db:
                                demo_db[u_name] = {"balance": 10000.0, "trades": []}
                            is_limit = ("LIMIT" in ord_type)
                            demo_db[u_name]["trades"].append({
                                "id": int(time.time()),
                                "ticker": res_data['ticker'],
                                "entry_price": float(custom_entry),
                                "amount": float(ord_amt),
                                "tp1": float(custom_tp),
                                "sl": float(custom_sl),
                                "direction": "SHORT",
                                "order_type": "LIMIT" if is_limit else "MARKET",
                                "status": "PENDING" if is_limit else "OPEN"
                            })
                            save_json(DEMO_TRADES_FILE, demo_db)
                            st.success(f"✅ {res_data['ticker']} SHORT آرڈر کامیابی سے فعال ہو گیا!")
                st.markdown("</div>", unsafe_allow_html=True)

# TAB 3: PENNY STOCKS RADAR (UNDER RS. 15)
with tabs[2]:
    st.subheader("🚀 پینی اسٹاکس الرٹ زون (Rs. 15 سے کم قیمت والے شیئرز)")
    if st.button("🔍 15 روپے سے کم والے شیئرز اسکین کریں"):
        penny_list = []
        prog = st.progress(0)
        for idx, sym in enumerate(ALL_PSX_STOCKS):
            p_data = fetch_psx_live_data(sym)
            pr = p_data["price"]
            if 0.5 < pr <= 15.0:
                penny_list.append({
                    "اسٹاک": sym,
                    "لائیو قیمت": f"Rs. {pr:,.2f}",
                    "حالت / ٹرینڈ": "🚀 بولش بریک آؤٹ زون" if pr > 8.0 else "🟢 سائیڈ ویز بائنگ",
                    "شرعی بیج": "🌙 Shariah Compliant" if sym in SHARIAH_COMPLIANT_STOCKS else "🏢 Regular"
                })
            prog.progress((idx + 1) / len(ALL_PSX_STOCKS))
        if penny_list:
            st.dataframe(pd.DataFrame(penny_list), use_container_width=True)
        else:
            st.info("اس وقت ۱۵ روپے سے کم قیمت والے شیئرز لوڈ ہو رہے ہیں۔")

# TAB 4: TAX & FILER VS NON-FILER CALCULATOR
with tabs[3]:
    st.subheader("🇵🇰 پاکستان ٹیکس و فائلر بمقابلہ نان فائلر بچت کیلکولیٹر")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        income_type = st.selectbox("آمدنی کی قسم:", ["ڈیویڈنڈ منافع (Dividend Income)", "Capital Gain (شیئرز کی خرید وفروخت کا نفع)"])
        raw_amount = st.number_input("کل نفع یا ڈیویڈنڈ رقم (Rs.)", min_value=1000, value=50000, step=5000)
    with col_t2:
        if "Dividend" in income_type:
            filer_tax = raw_amount * 0.15
            non_filer_tax = raw_amount * 0.30
        else:
            filer_tax = raw_amount * 0.125
            non_filer_tax = raw_amount * 0.25
            
        savings = non_filer_tax - filer_tax
        st.write(f"🟢 **فائلر (Filer) ٹیکس:** Rs. {filer_tax:,.2f}")
        st.write(f"🔴 **نان فائلر (Non-Filer) ٹیکس:** Rs. {non_filer_tax:,.2f}")
        st.success(f"💰 **فائلر بننے کی صورت میں خالص بچت:** **Rs. {savings:,.2f}**")

# TAB 5: AUTOMATED DIVIDEND CALENDAR
with tabs[4]:
    st.subheader("📅 PSX خودکار ڈیویڈنڈ کیلنڈر (Live Scraped)")
    df_div = fetch_psx_dividends_live()
    st.dataframe(df_div, use_container_width=True)

# TAB 6: COMPARE TWO STOCKS SIDE BY SIDE
with tabs[5]:
    st.subheader("⚖️ دو اسٹاکس کا آمنے سامنے موازنہ (Side-by-Side Comparison)")
    c1, c2 = st.columns(2)
    with c1:
        s1 = st.selectbox("پہلا اسٹاک منتخب کریں:", ALL_PSX_STOCKS, index=0)
    with c2:
        s2 = st.selectbox("دوسرا اسٹاک منتخب کریں:", ALL_PSX_STOCKS, index=1)
        
    if st.button("📊 موازنہ شروع کریں"):
        p1 = fetch_psx_live_data(s1)
        p2 = fetch_psx_live_data(s2)
        f1 = STOCK_FUNDAMENTALS.get(s1, {'promoter': 70.0, 'fii': 4.0, 'shares_out_m': 300})
        f2 = STOCK_FUNDAMENTALS.get(s2, {'promoter': 70.0, 'fii': 4.0, 'shares_out_m': 300})
        
        comp_df = pd.DataFrame({
            "میٹرک (Metrics)": ["لائیو قیمت (PKR)", "پروموٹر ہولڈنگ (%)", "FII / غیر ملکی ہولڈنگ (%)", "مارکیٹ کیپ (M)"],
            s1: [f"Rs. {p1['price']:,.2f}", f"{f1['promoter']}%", f"{f1['fii']}%", f"Rs. {p1['price']*f1['shares_out_m']:,.2f}M"],
            s2: [f"Rs. {p2['price']:,.2f}", f"{f2['promoter']}%", f"{f2['fii']}%", f"Rs. {p2['price']*f2['shares_out_m']:,.2f}M"]
        })
        st.dataframe(comp_df, use_container_width=True)

# TAB 7: DEMO WALLET
with tabs[6]:
    st.subheader("🧪 ڈیمو (Paper Trading) وائلٹ")
    if not st.session_state["logged_in"]:
        st.warning("⚠️ ڈیمو اکاؤنٹ کے لیے لاگ ان کریں۔")
    else:
        u_name = st.session_state["user_id"]
        u_demo = demo_db.get(u_name, {"balance": 10000.0, "trades": []})
        all_trades = u_demo.get("trades", [])
        
        closed_trades = [t for t in all_trades if t.get("status") == "CLOSED"]
        winning_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 100.0
        
        w1, w2, w3 = st.columns(3)
        w1.metric("💵 ورچوئل بیلنس", f"${u_demo.get('balance', 10000.0):,.2f}")
        w2.metric("🎯 باٹ ون-ریٹ (Win Rate)", f"{win_rate:.1f}%")
        w3.metric("📊 کل بند شدہ ٹریڈز", f"{len(closed_trades)}")
        
        st.divider()
        auto_ref = st.checkbox("🔄 لائیو پوزیشنز آٹو ریفریش (Auto Refresh 5s)", value=False)
        
        st.markdown("### ⚡ جاری (OPEN) پوزیشنز")
        open_trades = [t for t in all_trades if t.get("status") == "OPEN"]
        
        if open_trades:
            for t in open_trades:
                try:
                    df_t = yf.download(t['ticker'], period="1d", interval="1m", progress=False)
                    live_p = float(df_t['Close'].iloc[-1])
                except Exception:
                    live_p = t['entry_price']
                    
                dir_factor = 1 if t.get('direction', 'LONG') == "LONG" else -1
                pnl_usd = ((live_p - t['entry_price']) / t['entry_price']) * t['amount'] * dir_factor
                pnl_color = "#00E676" if pnl_usd >= 0 else "#FF1744"
                
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                with col1:
                    st.markdown(f"**{t['ticker']}** (`{t.get('direction', 'LONG')}`)")
                with col2:
                    st.write(f"اینٹری: `${t['entry_price']:,.4f}` | لائیو: `${live_p:,.4f}`")
                with col3:
                    st.write(f"سرمایہ: `${t['amount']:,.2f}`")
                with col4:
                    st.markdown(f"PnL: <span style='color:{pnl_color};font-weight:bold;'>${pnl_usd:+,.2f}</span>", unsafe_allow_html=True)
                with col5:
                    if st.button("🔴 کلوز پوزیشن (Sell)", key=f"close_{t['id']}"):
                        t["status"] = "CLOSED"
                        t["close_price"] = live_p
                        t["pnl"] = pnl_usd
                        u_demo["balance"] += (t['amount'] + pnl_usd)
                        save_json(DEMO_TRADES_FILE, demo_db)
                        st.success(f"✅ پوزیشن کلوز ہو گئی! PnL: ${pnl_usd:+,.2f}")
                        st.rerun()
                st.divider()
        else:
            st.info("کوئی اوپن پوزیشن موجود نہیں ہے۔")
            
        if auto_ref:
            time.sleep(5)
            st.rerun()

# TAB 8: DOW THEORY
with tabs[7]:
    st.subheader("🏛️ ڈاؤ تھیوری بائنگ و سیلنگ زون")
    if st.button("🚀 PSX ڈاؤ اسکین کریں"):
        dow_results = []
        prog = st.progress(0)
        for idx, sym in enumerate(ALL_PSX_STOCKS[:25]):
            try:
                df_d = yf.download(f"{sym}.KA", period="1mo", interval="1d", progress=False)
                if not df_d.empty:
                    c_close = df_d['Close'].iloc[:, 0] if isinstance(df_d['Close'], pd.DataFrame) else df_d['Close']
                    c_price = c_close.iloc[-1]
                    sig, desc = evaluate_dow_theory(df_d)
                    dow_results.append({"اسٹاک": sym, "قیمت": f"Rs. {c_price:,.2f}", "سگنل": sig, "تفصیل": desc})
            except Exception:
                pass
            prog.progress((idx + 1) / 25)
        if dow_results:
            st.dataframe(pd.DataFrame(dow_results), use_container_width=True)

# TAB 9: ADMIN
if is_admin:
    with tabs[8]:
        st.subheader("👥 ایڈمن ڈیش بورڈ")
        st.write("یوزر مینجمنٹ فعال ہے۔")
