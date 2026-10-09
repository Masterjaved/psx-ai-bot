import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import yfinance as yf
import streamlit.components.v1 as components

st.set_page_config(
    page_title="PSX & Crypto Precision Engine",
    page_icon="🏛️",
    layout="wide"
)

# Secrets & File Paths
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
REPO_NAME = st.secrets.get("REPO_NAME", "Masterjaved/psx-ai-bot")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", os.environ.get("SENDER_EMAIL", ""))
SENDER_PASS = st.secrets.get("SENDER_PASS", os.environ.get("SENDER_PASS", ""))
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

# Premium Dark Styling
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .main { background: #0A0E17; color: #ffffff; }
    .psx-header {
        background: linear-gradient(135deg, #004d40 0%, #00251a 100%);
        padding: 22px; border-radius: 15px; border-bottom: 4px solid #FFD700;
        box-shadow: 0 4px 15px rgba(0,77,64,0.4);
        margin-bottom: 25px; text-align: center;
    }
    .psx-header h1 { color: #ffffff; font-size: 2.2rem; margin: 0; font-weight: 800; }
    .crypto-card {
        background: #131B2E; padding: 25px; border-radius: 15px;
        border: 1px solid #1E2D4A; box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    }
    .target-box-green {
        background: #002B1B; border: 1px solid #00E676; padding: 12px;
        border-radius: 10px; text-align: center; color: #00E676; font-weight: bold;
    }
    .target-box-red {
        background: #2B0008; border: 1px solid #FF1744; padding: 12px;
        border-radius: 10px; text-align: center; color: #FF1744; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

ALL_PSX_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 
    'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 
    'PSO', 'CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK'
]

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

# High Precision Crypto Signal Generator
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
            ema50 = float(c_close.ewm(span=50).mean().iloc[-1])
            
            recent_vol = float(c_vol.iloc[-1])
            avg_vol = float(c_vol.iloc[-15:-1].mean())
            
            atr = float((c_high - c_low).iloc[-14:].mean())
            
            confidence = 75
            sig_type = "🟡 WAIT / NEUTRAL (صبر کریں)"
            sig_color = "#FFB300"
            
            if rsi_val < 42 and curr_p > ema20 and recent_vol > avg_vol * 1.2:
                sig_type = "🟢 STRONG BUY (باقاعدہ سٹرونگ خریدی)"
                sig_color = "#00E676"
                confidence = 93
            elif rsi_val < 45 and curr_p > ema50:
                sig_type = "🟢 BUY (خریداری کا زون)"
                sig_color = "#00E676"
                confidence = 85
            elif rsi_val > 68 and curr_p < ema20:
                sig_type = "🔴 STRONG SELL (مکمل فروخت)"
                sig_color = "#FF1744"
                confidence = 92
            elif rsi_val > 65:
                sig_type = "🔴 SELL (پرافٹ ٹیکنگ)"
                sig_color = "#FF1744"
                confidence = 82
                
            tp1 = round(curr_p + (atr * 1.2), 4 if curr_p < 1 else 2)
            tp2 = round(curr_p + (atr * 2.5), 4 if curr_p < 1 else 2)
            tp3 = round(curr_p + (atr * 4.0), 4 if curr_p < 1 else 2)
            sl = round(curr_p - (atr * 1.5), 4 if curr_p < 1 else 2)
            
            return {
                "ticker": clean_ticker,
                "price": curr_p,
                "rsi": rsi_val,
                "ema20": ema20,
                "confidence": confidence,
                "signal": sig_type,
                "color": sig_color,
                "tp1": tp1, "tp2": tp2, "tp3": tp3, "sl": sl
            }
    except Exception:
        pass
    return None

st.markdown("<div class='psx-header'><h1>🏛 PSX AI و ہائی ایکوریسی کرپٹو پورٹل</h1></div>", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

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
        st.rerun()

curr_user = st.session_state["user_id"]
is_admin = (curr_user.lower() == "javed")

tab_list = ["📂 پورٹ فولیو مینیجر", "⚡ کرپٹو AI سگنلز", "🧪 ڈیمو ٹریڈنگ وائلٹ", "🏛️ ڈاؤ تھیوری بائے/سیل زون", "🎯 پرو فلٹر اسکینر", "🤖 AI اسٹاک تجزیہ"]
if is_admin:
    tab_list.append("👥 یوزر مینجمنٹ (ایڈمن)")

tabs = st.tabs(tab_list)

# TAB 1: PORTFOLIO
with tabs[0]:
    if not st.session_state["logged_in"]:
        st.warning("⚠️ اپنے پورٹ فولیو کے لیے لاگ ان کریں۔")
    else:
        st.subheader(f"📂 {curr_user} کا پورٹ فولیو")
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
        if user_p:
            for sym, data in list(user_p.items()):
                p_res = fetch_psx_live_data(sym)
                live_price = p_res["price"] if p_res["status"] == "Success" else data["Buy Price"]
                b_price = data["Buy Price"]
                qty = data["Quantity"]
                pnl = (live_price - b_price) * qty
                
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
                with col_a:
                    st.markdown(f"**{sym}** ({qty} شیئرز)")
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

# TAB 2: CRYPTO SIGNALS + TRADINGVIEW CHART
with tabs[1]:
    st.subheader("⚡ کرپٹو AI ہائی ایکوریسی سگنلز و لائیو چارٹ")
    st.markdown("دنیا کی کسی بھی کرپٹو کرنسی کا سمبل لکھ کر سرچ کریں اور لائیو TradingView چارٹ کے ساتھ سگنلز حاصل کریں:")
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.markdown("<div class='crypto-card'>", unsafe_allow_html=True)
        user_crypto_input = st.text_input("کوائن درج کریں (مثلاً BTC, ETH, SOL, PEPE, SHIB, XRP):", value="BTC").upper().strip()
        btn_calc = st.button("🔍 سگنل جنریٹ کریں")
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
                    st.markdown(f"<div class='target-box-green'>🎯 Target 1<br>${res_data['tp1']}</div>", unsafe_allow_html=True)
                with t2:
                    st.markdown(f"<div class='target-box-green'>🎯 Target 2<br>${res_data['tp2']}</div>", unsafe_allow_html=True)
                with t3:
                    st.markdown(f"<div class='target-box-green'>🎯 Target 3<br>${res_data['tp3']}</div>", unsafe_allow_html=True)
                with t4:
                    st.markdown(f"<div class='target-box-red'>🛑 Stop Loss<br>${res_data['sl']}</div>", unsafe_allow_html=True)
                
                # Demo Trade Execute Button
                st.divider()
                if st.button(f"🧪 {res_data['ticker']} پر $1,000 کی ڈیمو ٹریڈ لگائیں"):
                    if not st.session_state["logged_in"]:
                        st.error("ڈیمو ٹریڈ لگانے کے لیے لاگ ان کریں۔")
                    else:
                        u_name = st.session_state["user_id"]
                        if u_name not in demo_db:
                            demo_db[u_name] = {"balance": 10000.0, "trades": []}
                        
                        demo_db[u_name]["trades"].append({
                            "ticker": res_data['ticker'],
                            "entry_price": res_data['price'],
                            "amount": 1000.0,
                            "tp1": res_data['tp1'],
                            "sl": res_data['sl'],
                            "type": res_data['signal']
                        })
                        save_json(DEMO_TRADES_FILE, demo_db)
                        st.success(f"✅ {res_data['ticker']} پر $1,000 کی ڈیمو ٹریڈ کامیابی سے لگ گئی!")
                        
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Embed TradingView Live Chart
                st.markdown("### 📈 لائیو TradingView چارٹ")
                clean_tv_ticker = res_data['ticker'].replace("-USD", "USD")
                tv_html = f"""
                <div class="tradingview-widget-container">
                  <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_1&symbol={clean_tv_ticker}&interval=D&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC" width="100%" height="450" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
                </div>
                """
                components.html(tv_html, height=470)

# TAB 3: DEMO TRADING WALLET
with tabs[2]:
    st.subheader("🧪 ڈیمو (Paper Trading) وائلٹ")
    if not st.session_state["logged_in"]:
        st.warning("⚠️ اپنے ڈیمو وائلٹ کی کارکردگی اور بیلنس دیکھنے کے لیے لاگ ان کریں۔")
    else:
        u_name = st.session_state["user_id"]
        u_demo = demo_db.get(u_name, {"balance": 10000.0, "trades": []})
        
        st.metric("💵 ڈیمو اکاؤنٹ کا ورچوئل بیلنس", f"${u_demo.get('balance', 10000.0):,.2f}")
        st.markdown("### 📋 جاری ڈیمو ٹریڈز اور لائیو کارکردگی")
        
        trades_list = u_demo.get("trades", [])
        if trades_list:
            demo_report = []
            for t in trades_list:
                # Live Price Check for Demo Trade
                try:
                    df_t = yf.download(t['ticker'], period="1d", interval="1m", progress=False)
                    live_p = float(df_t['Close'].iloc[-1])
                except Exception:
                    live_p = t['entry_price']
                    
                pnl_usd = ((live_p - t['entry_price']) / t['entry_price']) * t['amount']
                demo_report.append({
                    "کوائن": t['ticker'],
                    "اینٹری پرائس": f"${t['entry_price']:,.4f}",
                    "لائیو پرائس": f"${live_p:,.4f}",
                    "سرمایہ": f"${t['amount']:,.2f}",
                    "نفع / نقصان ($)": f"${pnl_usd:+,.2f}",
                    "ٹارگٹ (TP1)": f"${t['tp1']}",
                    "اسٹاپ لاس (SL)": f"${t['sl']}"
                })
            st.dataframe(pd.DataFrame(demo_report), use_container_width=True)
        else:
            st.info("آپ نے ابھی تک کوئی ڈیمو ٹریڈ نہیں لگائی۔ کرپٹو سگنل والے ٹیب سے ٹریڈ لگائیں۔")

# TAB 4: DOW THEORY
with tabs[3]:
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

# TAB 5: PRO FILTER
with tabs[4]:
    st.subheader("🎯 پرو فلٹر اسکینر")
    if st.button("🔍 پرو اسکین کریں"):
        pro_results = []
        prog = st.progress(0)
        for idx, sym in enumerate(ALL_PSX_STOCKS):
            fdata = STOCK_FUNDAMENTALS.get(sym, {'promoter': 71.5, 'fii': 3.8, 'shares_out_m': 300})
            p_info = fetch_psx_live_data(sym)
            price = p_info["price"]
            if price > 0:
                mcap_m = price * fdata['shares_out_m']
                if fdata['promoter'] > 70.0 and fdata['fii'] > 3.5 and mcap_m < 10000.0:
                    pro_results.append({
                        "اسٹاک": sym, "قیمت (Rs.)": f"{price:,.2f}",
                        "پروموٹر": f"{fdata['promoter']}%", "FII": f"{fdata['fii']}%", "MCap": f"{mcap_m:,.2f}M"
                    })
            prog.progress((idx + 1) / len(ALL_PSX_STOCKS))
        if pro_results:
            st.dataframe(pd.DataFrame(pro_results), use_container_width=True)

# TAB 6: AI STOCK ANALYSIS
with tabs[5]:
    st.subheader("🤖 AI اسٹاک تجزیہ")
    target_stock = st.text_input("اسٹاک سمبل درج کریں:", value="MLCF").upper().strip()
    if st.button("📊 تجزیہ کریں") and target_stock:
        p_info = fetch_psx_live_data(target_stock)
        st.write(f"لائیو قیمت: Rs. {p_info['price']:,.2f}")

# TAB 7: ADMIN
if is_admin:
    with tabs[6]:
        st.subheader("👥 ایڈمن ڈیش بورڈ")
        st.write("یوزر مینجمنٹ فعال ہے۔")
