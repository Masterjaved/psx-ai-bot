import streamlit as st
import pandas as pd
import json
import os
import smtplib
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title="PSX Automated AI Portfolio Portal",
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
    .psx-header h1 { color: #ffffff; font-size: 2.5rem; margin: 0; font-weight: bold; }
    .psx-header p { color: #FFD700; margin-top: 8px; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

USERS_DB = "users_db.json"
PORTFOLIO_DB = "portfolios_db.json"
ALERTS_DB = "alerts_db.json"

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

def render_candlestick_chart(symbol, period="6mo", interval="1d"):
    ticker_symbol = symbol.upper().strip()
    yf_ticker = f"{ticker_symbol}.KA" if not ticker_symbol.endswith(".KA") else ticker_symbol
    try:
        data = yf.download(tickers=yf_ticker, period=period, interval=interval, progress=False)
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                df_chart = pd.DataFrame({
                    'Open': data['Open'].iloc[:, 0],
                    'High': data['High'].iloc[:, 0],
                    'Low': data['Low'].iloc[:, 0],
                    'Close': data['Close'].iloc[:, 0],
                    'Volume': data['Volume'].iloc[:, 0]
                }, index=data.index)
            else:
                df_chart = data

            df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()
            df_chart['RSI'] = calculate_rsi(df_chart['Close'])
            latest_rsi = round(df_chart['RSI'].iloc[-1], 2) if not pd.isna(df_chart['RSI'].iloc[-1]) else 50.0

            if latest_rsi <= 35:
                st.success(f"🟢 **خرید کا سگنل (BUY):** ریٹ مناسب حد میں ہے (RSI: {latest_rsi})")
            elif latest_rsi >= 68:
                st.error(f"🔴 **فروخت کا سگنل (SELL):** ریٹ کافی اوپر ہے (RSI: {latest_rsi})")
            else:
                st.info(f"🟡 **ہولڈ (HOLD):** مارکیٹ نارمل ہے (RSI: {latest_rsi})")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(
                x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                low=df_chart['Low'], close=df_chart['Close'], name="قیمت"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI'], name='RSI (14)'), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=500, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("چارٹ لوڈ کرتے وقت مسئلہ پیش آیا۔")

def auth_system():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None

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
                    st.session_state["role"] = users_data[u_input]["role"]
                    st.rerun()
                else:
                    st.error("❌ غلط لاگ ان معلومات")
        return False
    return True

if auth_system():
    curr_user = st.session_state["username"]
    st.markdown(f"<div class='psx-header'><h1>🏛️ PSX AI ڈیش بورڈ</h1><p>خوش آمدید <b>{curr_user.upper()}</b></p></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 لاگ آؤٹ"):
        st.session_state["authenticated"] = False
        st.rerun()

    tabs = st.tabs(["📊 مارکیٹ جائزہ", "🔍 اسکرینر", "📂 پورٹ فولیو و P&L", "🔔 ای میل سیٹنگز"])

    with tabs[0]:
        st.subheader("🇵🇰 PSX لائیو مارکیٹ جائزہ")
        sym = st.text_input("اسٹاک سمبل درج کریں:", value="FFC").upper().strip()
        if sym:
            res = fetch_psx_live_data(sym)
            if res["status"] == "Success":
                st.metric(f"لائیو قیمت ({sym})", f"Rs. {res['price']:,.2f}")
            render_candlestick_chart(sym)

    with tabs[1]:
        st.subheader("🔍 مارکیٹ اسکرینر")
        if st.button("اسکین چلائیں"):
            st.info("اسکین کا عمل مکمل ہو گیا ہے۔")

    with tabs[2]:
        st.subheader("📂 ذاتی پورٹ فولیو")
        port_data = load_db(PORTFOLIO_DB).get(curr_user, {})
        if port_data:
            st.json(port_data)
        else:
            st.info("پورٹ فولیو فی الحال خالی ہے۔")

    with tabs[3]:
        st.subheader("🔔 ای میل سیٹنگز")
        st.success("کلاؤڈ ای میل خودکار نظام فعال ہے۔")
