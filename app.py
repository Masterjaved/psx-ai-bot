import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="PSX AI Value Investing & Portfolio Portal",
    page_icon="🏛️",
    layout="wide"
)

# Configuration & Secrets
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
REPO_NAME = st.secrets.get("REPO_NAME", "Masterjaved/psx-ai-bot")
FILE_PATH = "portfolios_db.json"
USERS_DB = "users_db.json"

def sync_portfolio_to_github(data):
    """پورٹ فولیو کے ڈیٹا کو خودکار گٹ ہب پر بھیجنا"""
    if not GITHUB_TOKEN:
        return False
    
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
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
            "message": "Auto-sync portfolios_db.json from Streamlit Dashboard",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=payload)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

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
    sync_portfolio_to_github(data)

# Styling
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .main { background: linear-gradient(135deg, #0d1b1e 0%, #000000 100%); color: #ffffff; }
    .psx-header {
        background: linear-gradient(90deg, #004d40 0%, #05291d 50%, #00251a 100%);
        padding: 25px; border-radius: 15px; border-bottom: 4px solid #FFD700;
        margin-bottom: 25px; text-align: center;
    }
    .psx-header h1 { color: #ffffff; font-size: 2.2rem; margin: 0; font-weight: bold; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

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

# Main Portal Interface
st.markdown("<div class='psx-header'><h1>🏛️ PSX AI انویسٹنگ پورٹل و پورٹ فولیو مینیجر</h1></div>", unsafe_allow_html=True)

curr_user = "javed"
all_ports = load_db(FILE_PATH)
if curr_user not in all_ports:
    all_ports[curr_user] = {}

tabs = st.tabs(["📂 پورٹ فولیو مینیجر", "🔍 اٹو مارکیٹ اسکینر", "📊 تکنیکی تجزیہ"])

# TAB 1: PORTFOLIO MANAGER WITH DELETE OPTION
with tabs[0]:
    st.subheader("📂 پورٹ فولیو مینجمنٹ (شامل کریں یا فروخت شدہ شیئر حذف کریں)")
    
    # 1. Add Stock Form
    with st.expander("➕ نیا شیئر پورٹ فولیو میں شامل کریں", expanded=False):
        with st.form("add_stock_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_sym = st.text_input("اسٹاک سمبل (مثلاً MLCF)").upper().strip()
            with c2:
                new_price = st.number_input("خریداری قیمت (Rs.)", min_value=1.0, value=50.0)
            with c3:
                new_qty = st.number_input("تعداد (Quantity)", min_value=1, value=100)
                
            c4, c5 = st.columns(2)
            with c4:
                t_sell = st.number_input("ٹارگٹ سیل (Target Sell Rs.)", min_value=1.0, value=round(new_price * 1.15, 2))
            with c5:
                s_loss = st.number_input("اسٹاپ لاس (Stop Loss Rs.)", min_value=1.0, value=round(new_price * 0.90, 2))

            if st.form_submit_button("پورٹ فولیو میں محفوظ کریں"):
                if new_sym:
                    all_ports[curr_user][new_sym] = {
                        "Buy Price": new_price,
                        "Quantity": new_qty,
                        "Target Sell": t_sell,
                        "Stop Loss": s_loss
                    }
                    save_db(FILE_PATH, all_ports)
                    st.success(f"✅ {new_sym} محفوظ ہو گیا اور GitHub پر خودکار سنک ہو گیا!")
                    st.rerun()

    # 2. Portfolio Table & Delete Option
    user_p = all_ports.get(curr_user, {})
    if user_p:
        st.subheader("📋 آپ کی ہولڈنگز اور انفرادی ڈیلیٹ کے اختیارات:")
        
        tot_invested = 0
        tot_current = 0
        
        for sym, data in list(user_p.items()):
            p_res = fetch_psx_live_data(sym)
            live_price = p_res["price"] if p_res["status"] == "Success" else data["Buy Price"]
            
            b_price = data["Buy Price"]
            qty = data["Quantity"]
            c_val = b_price * qty
            l_val = live_price * qty
            pnl = l_val - c_val
            
            tot_invested += c_val
            tot_current += l_val
            
            # Status Alerts
            status_txt = "🟢 ہولڈ رکھیں"
            if live_price >= data.get("Target Sell", b_price * 1.15):
                status_txt = "🎯 ٹارگٹ پورا! بیچ دیں (SELL)"
            elif live_price <= data.get("Stop Loss", b_price * 0.90):
                status_txt = "⚠️ اسٹاپ لاس الرٹ"

            col_a, col_b, col_c, col_d, col_e = st.columns([1.5, 2, 2, 2, 1.5])
            with col_a:
                st.markdown(f"**{sym}** ({qty} شیئرز)")
            with col_b:
                st.write(f"خرید: Rs.{b_price:,.2f} | لائیو: Rs.{live_price:,.2f}")
            with col_c:
                pnl_color = "green" if pnl >= 0 else "red"
                st.markdown(f"نفع/نقصان: <span style='color:{pnl_color};font-weight:bold;'>Rs.{pnl:+,.2f}</span>", unsafe_allow_html=True)
            with col_d:
                st.write(status_txt)
            with col_e:
                # Individual Delete Button
                if st.button(f"🗑️ ڈیلیٹ", key=f"del_{sym}"):
                    del all_ports[curr_user][sym]
                    save_db(FILE_PATH, all_ports)
                    st.warning(f"❌ {sym} پورٹ فولیو سے حذف کر دیا گیا ہے!")
                    st.rerun()
            st.divider()
            
        tot_pnl = tot_current - tot_invested
        m1, m2, m3 = st.columns(3)
        m1.metric("کل سرمایہ کاری", f"Rs. {tot_invested:,.2f}")
        m2.metric("موجودہ مارکیٹ مالیت", f"Rs. {tot_current:,.2f}")
        m3.metric("مجموعی نفع / نقصان", f"Rs. {tot_pnl:+,.2f}")
    else:
        st.info("آپ کے پورٹ فولیو میں فی الوقت کوئی شیئر نہیں ہے۔ نیا شیئر شامل کرنے کے لیے اوپر فارم استعمال کریں۔")

# TAB 2: MARKET SCANNER
with tabs[1]:
    st.subheader("🔍 لائیو مارکیٹ اٹو اسکینر (KSE-100 & KMI-30)")
    if st.button("🚀 لائیو مارکیٹ اسکین شروع کریں"):
        all_list = [(s, "🕌 شریعہ") for s in SHARIAH_STOCKS] + [(s, "🏛️ جنرل") for s in NON_SHARIAH_STOCKS]
        scan_results = []
        progress = st.progress(0)
        
        for idx, (s_sym, cat) in enumerate(all_list):
            try:
                df_scan = yf.download(f"{s_sym}.KA", period="1mo", interval="1d", progress=False)
                if not df_scan.empty:
                    c_close = df_scan['Close'].iloc[:, 0] if isinstance(df_scan['Close'], pd.DataFrame) else df_scan['Close']
                    c_price = c_close.iloc[-1]
                    r_val = calculate_rsi(c_close).iloc[-1]
                    
                    sig = "متوازن (Hold)"
                    if r_val <= 38:
                        sig = "🟢 خرید کا موقع (BUY)"
                    elif r_val >= 68:
                        sig = "🔴 منافع بک کریں (SELL)"
                        
                    scan_results.append({
                        "اسٹاک": s_sym,
                        "قسم": cat,
                        "قیمت": f"Rs. {c_price:,.2f}",
                        "RSI": round(r_val, 2),
                        "سگنل": sig
                    })
            except Exception:
                pass
            progress.progress((idx + 1) / len(all_list))
            
        st.dataframe(pd.DataFrame(scan_results), use_container_width=True)

# TAB 3: TECHNICAL CHART
with tabs[2]:
    st.subheader("📊 چارٹ و ٹیکنیکل اشارے")
    s_input = st.text_input("اسٹاک کا نام لکھیں:", value="FFC").upper().strip()
    if s_input:
        try:
            df_chart = yf.download(f"{s_input}.KA", period="6mo", interval="1d", progress=False)
            if not df_chart.empty:
                close = df_chart['Close'].iloc[:, 0] if isinstance(df_chart['Close'], pd.DataFrame) else df_chart['Close']
                fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=close)])
                fig.update_layout(template="plotly_dark", height=450)
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.error("ڈیٹا لوڈ نہیں ہو سکا۔")
