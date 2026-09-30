import streamlit as st
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="PSX AI Value Investing & Portfolio Portal",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 18px !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    .main { background: linear-gradient(135deg, #0d1b1e 0%, #000000 100%); color: #ffffff; }
    .stMetric {
        background: linear-gradient(135deg, #132a22 0%, #08120e 100%) !important;
        border: 2px solid #00e676 !important;
        border-radius: 12px !important;
        padding: 18px !important;
    }
    .psx-header {
        background: linear-gradient(90deg, #004d40 0%, #05291d 50%, #00251a 100%);
        padding: 25px;
        border-radius: 15px;
        border-bottom: 4px solid #FFD700;
        margin-bottom: 25px;
        text-align: center;
    }
    .psx-header h1 { color: #ffffff; font-size: 2.3rem; margin: 0; font-weight: bold; }
    .psx-header p { color: #FFD700; margin-top: 8px; font-weight: bold; font-size: 1.1rem; }
    .fund-card {
        background-color: #11221c;
        border-left: 5px solid #00e676;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

USERS_DB = "users_db.json"
PORTFOLIO_DB = "portfolios_db.json"

SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

def load_db(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_db(USERS_DB)
if "javed" not in users:
    users["javed"] = {"password": "adminpassword123", "role": "Admin"}
    save_db(USERS_DB, users)

@st.cache_data(ttl=300)
def fetch_fundamental_data(symbol):
    """کمپنی کے بنیادی مالیاتی ڈیٹا اور مستقبل کا تجزیہ حاصل کرنا"""
    ticker = f"{symbol.upper().strip()}.KA"
    info_dict = {}
    try:
        t = yf.Ticker(ticker)
        info = t.info
        info_dict['pe'] = info.get('trailingPE', 'N/A')
        info_dict['eps'] = info.get('trailingEps', 'N/A')
        info_dict['div_yield'] = round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else '0.0%'
        info_dict['high_52'] = info.get('fiftyTwoWeekHigh', 'N/A')
        info_dict['low_52'] = info.get('fiftyTwoWeekLow', 'N/A')
        info_dict['mkt_cap'] = info.get('marketCap', 'N/A')
    except Exception:
        info_dict = {'pe': 'N/A', 'eps': 'N/A', 'div_yield': 'N/A', 'high_52': 'N/A', 'low_52': 'N/A'}
    return info_dict

@st.cache_data(ttl=120)
def fetch_psx_live_data(symbol):
    clean_symbol = symbol.upper().replace(".KA", "").strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_div = soup.find("div", {"class": "quote__close"})
            if price_div:
                price = float(price_div.text.strip().replace("Rs.", "").replace(",", ""))
                return {"symbol": clean_symbol, "price": price, "status": "Success"}
            price_span = soup.find("span", {"class": "quote__price"})
            if price_span:
                price = float(price_span.text.strip().replace(",", ""))
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

def render_advanced_chart_and_fundamentals(symbol):
    ticker = f"{symbol.upper().strip()}.KA"
    try:
        data = yf.download(tickers=ticker, period="6mo", interval="1d", progress=False)
        if not data.empty:
            df = pd.DataFrame({
                'Open': data['Open'].iloc[:, 0] if isinstance(data.columns, pd.MultiIndex) else data['Open'],
                'High': data['High'].iloc[:, 0] if isinstance(data.columns, pd.MultiIndex) else data['High'],
                'Low': data['Low'].iloc[:, 0] if isinstance(data.columns, pd.MultiIndex) else data['Low'],
                'Close': data['Close'].iloc[:, 0] if isinstance(data.columns, pd.MultiIndex) else data['Close'],
                'Volume': data['Volume'].iloc[:, 0] if isinstance(data.columns, pd.MultiIndex) else data['Volume']
            }, index=data.index)

            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])
            
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            latest_rsi = round(df['RSI'].iloc[-1], 2)
            latest_close = df['Close'].iloc[-1]
            latest_macd = df['MACD'].iloc[-1]
            latest_sig = df['Signal'].iloc[-1]

            sharia_txt = "🕌 شریعہ کمپلائنٹ (KMI-30)" if symbol.upper() in SHARIAH_STOCKS else "🏛️ جنرل / KSE-100"
            st.caption(f"اسٹاک کی قسم: **{sharia_txt}**")

            # ۱. بنیادی معلومات (Fundamental Analysis)
            st.markdown("### 🏛️ بنیادی مالیاتی جائزہ و مستقبل کی سمت")
            funds = fetch_fundamental_data(symbol)
            fcol1, fcol2, fcol3, fcol4 = st.columns(4)
            fcol1.metric("P/E Ratio (قیمت بنام آمدن)", str(funds.get('pe', 'N/A')))
            fcol2.metric("EPS (فی شیئر آمدن)", f"Rs. {funds.get('eps', 'N/A')}")
            fcol3.metric("Dividend Yield (منافع شرح)", f"{funds.get('div_yield', 'N/A')}%")
            fcol4.metric("52-ہفتے کی اعلیٰ ترین قیمت", f"Rs. {funds.get('high_52', 'N/A')}")

            # کمپنی کے مثبت و منفی پہلوؤں کا تبصرہ
            with st.expander("📌 کمپنی کے بنیادی مثبت و منفی پہلو (Pros & Cons)", expanded=True):
                col_p, col_c = st.columns(2)
                with col_p:
                    st.success("**مثبت پہلو (Positive Factors):**")
                    if symbol.upper() in SHARIAH_STOCKS:
                        st.write("• اسلامک کے ایم آئی-30 انڈیکس میں شامل ہے (شریعہ کمپلائنٹ)۔")
                    if funds.get('div_yield') and str(funds.get('div_yield')) != '0.0%':
                        st.write(f"• شیئر ہولڈرز کو **{funds.get('div_yield')}%** کا سالانہ ڈیویڈنڈ فراہم کرتا ہے۔")
                    st.write("• مستحکم بنیادی حجم اور کیش فلو کی تاریخ۔")
                with col_c:
                    st.error("**منفی / محتاط پہلو (Risk Factors):**")
                    st.write("• ملک کی مجموعی معاشی صورتحال اور سود کی شرح میں تبدیلی سے متاثر ہو سکتا ہے۔")
                    if latest_rsi >= 65:
                        st.write("• فی الوقت قیمت اپنی اعلیٰ ترین سطح کے قریب ہے (Profit Booking Risk)۔")

            # ۲. تکنیکی الرٹس
            st.markdown("### 📊 تکنیکی الرٹس (Technical Signals)")
            col_a, col_b = st.columns(2)
            with col_a:
                if latest_rsi <= 38:
                    st.success(f"🟢 **RSI خرید کا اشارہ:** سستا زون (RSI: {latest_rsi})")
                elif latest_rsi >= 68:
                    st.error(f"🔴 **RSI فروخت کا اشارہ:** اوور باٹ زون (RSI: {latest_rsi})")
                else:
                    st.info(f"🟡 **RSI متوازن:** نارمل زون (RSI: {latest_rsi})")

            with col_b:
                if latest_macd > latest_sig:
                    st.success("🚀 **MACD تیزی کا اشارہ (Bullish):** قیمت میں مزید اضافے کا امکان")
                else:
                    st.warning("⚠ **MACD مندی کا اشارہ (Bearish):** محتاط رہیں")

            # ۳. چارٹ
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="قیمت"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20 Day MA', line=dict(color='yellow', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='cyan', width=1.5)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal Line', line=dict(color='orange', width=1.5)), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=550, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning("چارٹ لوڈ کرتے وقت مسئلہ پیش آیا۔")

def auth_system():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    if not st.session_state["authenticated"]:
        st.markdown("<div class='psx-header'><h1>🏛️ PSX پرسنل AI ویلیو انویسٹنگ پورٹل</h1></div>", unsafe_allow_html=True)
        users_data = load_db(USERS_DB)
        with st.sidebar.form("login_form"):
            st.subheader("🔑 لاگ ان")
            u_input = st.text_input("صارف کا نام (Username)").lower().strip()
            p_input = st.text_input("پاسورڈ (Password)", type="password")
            if st.form_submit_button("لاگ ان کریں"):
                if u_input in users_data and users_data[u_input]["password"] == p_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = u_input
                    st.rerun()
                else:
                    st.error("❌ غلط لاگ ان معلومات")
        return False
    return True

if auth_system():
    curr_user = st.session_state["username"]
    st.markdown(f"<div class='psx-header'><h1>🏛️ PSX AI انویسٹنگ پورٹل و لائیو اسکینر</h1><p>خوش آمدید <b>{curr_user.upper()}</b></p></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 لاگ آؤٹ"):
        st.session_state["authenticated"] = False
        st.rerun()

    tabs = st.tabs(["📊 لائیو مارکیٹ و بنیادی تجزیہ", "🔍 اٹو مارکیٹ اسکینر ڈیش بورڈ", "📂 پورٹ فولیو مینیجر و الرٹس", "🔔 کلاؤڈ سسٹم Status"])

    with tabs[0]:
        st.subheader("🇵🇰 PSX اسٹاک تجزیہ (تکنیکی و بنیادی)")
        sym = st.text_input("اسٹاک سمبل درج کریں (مثلاً FFC, SYS, MLCF):", value="FFC").upper().strip()
        if sym:
            res = fetch_psx_live_data(sym)
            if res["status"] == "Success":
                st.metric(f"لائیو قیمت ({sym})", f"Rs. {res['price']:,.2f}")
            render_advanced_chart_and_fundamentals(sym)

    with tabs[1]:
        st.subheader("🔍 مارکیٹ اٹو اسکینر (Auto-Scan Dashboard)")
        st.write("ایک کلک پر تمام شریعہ و ایکٹیو اسٹاکس کو اسکین کریں اور خرید و فروخت کے بہترین اشارے دیکھیں:")
        
        if st.button("🚀 اسکین مارکیٹ (Scan PSX Stocks Now)"):
            all_list = [(s, "🕌 شریعہ") for s in SHARIAH_STOCKS] + [(s, "🏛️ جنرل") for s in NON_SHARIAH_STOCKS]
            scan_results = []
            
            progress_bar = st.progress(0)
            for idx, (s_sym, cat) in enumerate(all_list):
                try:
                    df_scan = yf.download(f"{s_sym}.KA", period="1mo", interval="1d", progress=False)
                    if not df_scan.empty:
                        c_price = df_scan['Close'].iloc[-1] if not isinstance(df_scan['Close'], pd.DataFrame) else df_scan['Close'].iloc[-1, 0]
                        c_close = df_scan['Close'].iloc[:, 0] if isinstance(df_scan['Close'], pd.DataFrame) else df_scan['Close']
                        r_val = calculate_rsi(c_close).iloc[-1]
                        
                        sig = "متوازن (Hold)"
                        if r_val <= 38:
                            sig = "🟢 خرید کا موقع (BUY)"
                        elif r_val >= 68:
                            sig = "🔴 منافع بک کریں (SELL)"
                            
                        scan_results.append({
                            "اسٹاک": s_sym,
                            "قسم": cat,
                            "موجودہ قیمت": f"Rs. {c_price:,.2f}",
                            "RSI انڈیکیٹر": round(r_val, 2),
                            "تجویز / الرٹ": sig
                        })
                except Exception:
                    pass
                progress_bar.progress((idx + 1) / len(all_list))
                
            st.dataframe(pd.DataFrame(scan_results), use_container_width=True)

    with tabs[2]:
        st.subheader("📂 ذاتی پورٹ فولیو مینیجر و سیل الرٹس")
        all_ports = load_db(PORTFOLIO_DB)
        user_port = all_ports.get(curr_user, {})

        with st.expander("➕ نیا شیئر پورٹ فولیو میں درج کریں", expanded=True):
            with st.form("add_stock_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_sym = st.text_input("اسٹاک سمبل (مثلاً MLCF)").upper().strip()
                with col2:
                    new_price = st.number_input("خریداری کی قیمت (Buy Price)", min_value=1.0, value=50.0)
                with col3:
                    new_qty = st.number_input("شیئرز کی تعداد (Quantity)", min_value=1, value=100)

                submit_btn = st.form_submit_button("پورٹ فولیو میں محفوظ کریں")
                if submit_btn and new_sym:
                    if curr_user not in all_ports:
                        all_ports[curr_user] = {}
                    all_ports[curr_user][new_sym] = {
                        "Buy Price": new_price,
                        "Quantity": new_qty,
                        "Target Sell": round(new_price * 1.15, 2),
                        "Stop Loss": round(new_price * 0.90, 2)
                    }
                    save_db(PORTFOLIO_DB, all_ports)
                    st.success(f"✅ {new_sym} پورٹ فولیو میں شامل کر دیا گیا ہے!")
                    st.rerun()

        st.subheader("📋 آپ کے شیئرز اور بیچنے کے لائیو الرٹس:")
        if user_port:
            port_table = []
            for s_name, s_data in user_port.items():
                p_res = fetch_psx_live_data(s_name)
                curr_p = p_res['price'] if p_res['status'] == "Success" else s_data['Buy Price']
                b_p = s_data['Buy Price']
                qty = s_data['Quantity']
                t_sell = s_data['Target Sell']
                
                pnl = (curr_p - b_p) * qty
                
                alert_status = "ہولڈ رکھیں (Hold)"
                if curr_p >= t_sell:
                    alert_status = "🎯 ٹارگٹ پورا! بیچ دیں (SELL)"
                elif curr_p <= s_data['Stop Loss']:
                    alert_status = "⚠️ اسٹاپ لاس الرٹ"
                    
                port_table.append({
                    "اسٹاک": s_name,
                    "خرید قیمت": f"Rs. {b_p:,.2f}",
                    "لائیو قیمت": f"Rs. {curr_p:,.2f}",
                    "تعداد": qty,
                    "نفع / نقصان": f"Rs. {pnl:+,.2f}",
                    "بیچنے کی تجویز": alert_status
                })
            st.dataframe(pd.DataFrame(port_table), use_container_width=True)
        else:
            st.info("آپ کے پورٹ فولیو میں کوئی شیئر موجود نہیں ہے۔ اوپر فارم سے شامل کریں۔")

    with tabs[3]:
        st.subheader("🔔 کلاؤڈ آٹومیشن الرٹس")
        st.success("سسٹم روزانہ صبح 9:00 AM اور شام 4:20 PM PKT پر کلاؤڈ سرور سے لائیو رپورٹس ای میل بھیجتا ہے۔")
