import streamlit as st
import pandas as pd
import json
import os
import requests
import base64
from bs4 import BeautifulSoup
import yfinance as yf

st.set_page_config(
    page_title="PSX AI Multi-User Investing Portal",
    page_icon="🏛️",
    layout="wide"
)

# Secrets & File Paths
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
REPO_NAME = st.secrets.get("REPO_NAME", "Masterjaved/psx-ai-bot")
PORTFOLIO_FILE = "portfolios_db.json"
USERS_FILE = "users_db.json"

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

# Load Users & Portfolios
users_db = load_json(USERS_FILE, {})
if "javed" not in users_db:
    users_db["Masterjaved"] = {"pass": "javed123", "email": "masterjaved@gmail.com"}

ports_db = load_json(PORTFOLIO_FILE, {})

st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .main { background: linear-gradient(135deg, #0d1b1e 0%, #000000 100%); color: #ffffff; }
    .psx-header {
        background: linear-gradient(90deg, #004d40 0%, #05291d 50%, #00251a 100%);
        padding: 20px; border-radius: 12px; border-bottom: 4px solid #FFD700;
        margin-bottom: 20px; text-align: center;
    }
    .psx-header h1 { color: #ffffff; font-size: 2rem; margin: 0; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

SHARIAH_STOCKS = ['FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 'SHEL', 'SEARL', 'AVN', 'MARI', 'PSO']
PENNY_STOCKS = ['CNERGY', 'KEL', 'TELE', 'WTL', 'HUMNL', 'TRG', 'BYCO', 'PACE', 'SILK', 'ANL', 'HASCOL', 'BOP', 'FNEL', 'FLYNG', 'LOADS']

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

st.markdown("<div class='psx-header'><h1>🏛 PSX AI محفوظ و ملٹی یوزر پورٹل</h1></div>", unsafe_allow_html=True)

# Authentication Session
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
            if u_input in users_db:
                u_info = users_db[u_input]
                saved_pass = u_info.get("pass") if isinstance(u_info, dict) else u_info
                if saved_pass == p_input:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = u_input
                    st.sidebar.success(f"خوش آمدید {u_input}!")
                    st.rerun()
                else:
                    st.sidebar.error("غلط پاسورڈ!")
            else:
                st.sidebar.error("یوزر نیم موجود نہیں!")
                
    else:  # Sign Up
        st.sidebar.subheader("نیا اکاؤنٹ بنائیں")
        new_u = st.sidebar.text_input("نیا یوزر نیم").strip()
        new_e = st.sidebar.text_input("ای میل ایڈریس (ای میل رپورٹ کے لیے)").strip()
        new_p = st.sidebar.text_input("نیا پاسورڈ", type="password").strip()
        confirm_p = st.sidebar.text_input("پاسورڈ کی تصدیق", type="password").strip()
        
        if st.sidebar.button("رجسٹر کریں"):
            if not new_u or not new_p or not new_e:
                st.sidebar.error("تمام خانے پر کرنا لازمی ہیں۔")
            elif "@" not in new_e or "." not in new_e:
                st.sidebar.error("درست ای میل درج کریں۔")
            elif new_p != confirm_p:
                st.sidebar.error("پاسورڈ میچ نہیں ہو رہے!")
            elif new_u in users_db:
                st.sidebar.error("یہ یوزر نیم پہلے سے موجود ہے!")
            else:
                users_db[new_u] = {"pass": new_p, "email": new_e}
                save_json(USERS_FILE, users_db)
                st.sidebar.success("✅ رجسٹریشن کامیاب! اب لاگ ان والے آپشن پر جا کر لاگ ان کریں۔")
else:
    st.sidebar.success(f"لاگ ان بطور: **{st.session_state['user_id']}**")
    if st.sidebar.button("لاگ آؤٹ"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.rerun()

curr_user = st.session_state["user_id"]
is_admin = (curr_user == "javed")

if is_admin:
    tab_list = ["📂 پورٹ فولیو مینیجر", "👥 یوزر مینجمنٹ (ایڈمن)", "⚡ پینی اسٹاکس (Rs. 5-25)", "🔍 مارکیٹ اسکینر"]
else:
    tab_list = ["📂 پورٹ فولیو مینیجر", "⚡ پینی اسٹاکس (Rs. 5-25)", "🔍 مارکیٹ اسکینر"]

tabs = st.tabs(tab_list)

# TAB 1: PORTFOLIO
with tabs[0]:
    if not st.session_state["logged_in"]:
        st.warning("⚠️ اپنے پورٹ فولیو تک رسائی حاصل کرنے کے لیے سائڈ بار سے لاگ ان یا نیا سائن اپ کریں۔")
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
                    
                c4, c5 = st.columns(2)
                with c4:
                    t_sell = st.number_input("ٹارگٹ سیل (Target Sell)", min_value=0.5, value=round(new_price * 1.15, 2))
                with c5:
                    s_loss = st.number_input("اسٹاپ لاس (Stop Loss)", min_value=0.5, value=round(new_price * 0.90, 2))

                if st.form_submit_button("محفوظ کریں"):
                    if new_sym:
                        ports_db[curr_user][new_sym] = {
                            "Buy Price": new_price,
                            "Quantity": new_qty,
                            "Target Sell": t_sell,
                            "Stop Loss": s_loss
                        }
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
                st.divider()

# TAB 2: ADMIN USER MANAGEMENT (FULL CONTROL)
if is_admin:
    with tabs[1]:
        st.subheader("👥 ایڈمن ڈیش بورڈ: یوزر و پاسورڈ مینجمنٹ")
        
        col_adm1, col_adm2 = st.columns(2)
        
        with col_adm1:
            st.markdown("### ➕ نیا یوزر ڈائریکٹ شامل کریں")
            with st.form("admin_add_user"):
                adm_u = st.text_input("یوزر نیم")
                adm_e = st.text_input("ای میل ایڈریس")
                adm_p = st.text_input("پاسورڈ")
                if st.form_submit_button("یوزر شامل کریں"):
                    if adm_u and adm_p and adm_e:
                        users_db[adm_u] = {"pass": adm_p, "email": adm_e}
                        save_json(USERS_FILE, users_db)
                        st.success(f"✅ یوزر '{adm_u}' شامل ہو گیا!")
                        st.rerun()
                    else:
                        st.error("تمام خانے پر کریں۔")

        with col_adm2:
            st.markdown("### 🔑 کسی بھی یوزر کا پاسورڈ تبدیل کریں")
            with st.form("admin_change_pass"):
                target_user = st.selectbox("یوزر منتخب کریں", list(users_db.keys()))
                update_pass = st.text_input("نیا پاسورڈ درج کریں")
                if st.form_submit_button("پاسورڈ اپ ڈیٹ کریں"):
                    if update_pass:
                        curr_info = users_db[target_user]
                        if isinstance(curr_info, dict):
                            curr_info["pass"] = update_pass
                        else:
                            users_db[target_user] = {"pass": update_pass, "email": "masterjaved@gmail.com"}
                        save_json(USERS_FILE, users_db)
                        st.success(f"✅ '{target_user}' کا پاسورڈ اپ ڈیٹ ہو گیا!")
                        st.rerun()

        st.divider()
        st.markdown("### 📋 تمام رجسٹرڈ یوزرز کی فہرست")
        for u_name, u_info in list(users_db.items()):
            u_p = u_info.get("pass") if isinstance(u_info, dict) else u_info
            u_e = u_info.get("email", "N/A") if isinstance(u_info, dict) else "N/A"
            
            col_u1, col_u2, col_u3, col_u4 = st.columns([2, 2, 2, 1])
            with col_u1:
                st.write(f"👤 **{u_name}**")
            with col_u2:
                st.write(f"🔑 `{u_p}`")
            with col_u3:
                st.write(f"📧 `{u_e}`")
            with col_u4:
                if u_name != "javed":
                    if st.button("🗑 ڈیلیٹ", key=f"del_user_{u_name}"):
                        del users_db[u_name]
                        if u_name in ports_db:
                            del ports_db[u_name]
                            save_json(PORTFOLIO_FILE, ports_db)
                        save_json(USERS_FILE, users_db)
                        st.success(f"یوزر '{u_name}' ڈیلیٹ کر دیا گیا!")
                        st.rerun()
            st.divider()

# TAB 3: PENNY STOCKS
p_tab_idx = 2 if is_admin else 1
with tabs[p_tab_idx]:
    st.subheader("⚡ سستے اور ایکٹیو پینی اسٹاکس (Rs. 5-25)")
    if st.button("🔍 سستے شیئرز اسکین کریں"):
        penny_results = []
        progress = st.progress(0)
        for idx, s_sym in enumerate(PENNY_STOCKS):
            try:
                df_p = yf.download(f"{s_sym}.KA", period="1mo", interval="1d", progress=False)
                if not df_p.empty:
                    c_close = df_p['Close'].iloc[:, 0] if isinstance(df_p['Close'], pd.DataFrame) else df_p['Close']
                    c_vol = df_p['Volume'].iloc[:, 0] if isinstance(df_p['Volume'], pd.DataFrame) else df_p['Volume']
                    price = c_close.iloc[-1]
                    vol = c_vol.iloc[-1]
                    r_val = calculate_rsi(c_close).iloc[-1]
                    
                    if 3.0 <= price <= 30.0:
                        penny_results.append({
                            "اسٹاک": s_sym,
                            "قیمت (Rs.)": f"{price:,.2f}",
                            "روزانہ حجم": f"{int(vol):,}",
                            "RSI": round(r_val, 2)
                        })
            except Exception:
                pass
            progress.progress((idx + 1) / len(PENNY_STOCKS))
        if penny_results:
            st.dataframe(pd.DataFrame(penny_results), use_container_width=True)

# TAB 4: GENERAL SCANNER
g_tab_idx = 3 if is_admin else 2
with tabs[g_tab_idx]:
    st.subheader("🔍 مارکیٹ اسکینر")
    if st.button("🚀 اسکین شروع کریں"):
        all_list = SHARIAH_STOCKS + PENNY_STOCKS
        gen_results = []
        progress = st.progress(0)
        for idx, s_sym in enumerate(all_list):
            try:
                df_scan = yf.download(f"{s_sym}.KA", period="1mo", interval="1d", progress=False)
                if not df_scan.empty:
                    c_close = df_scan['Close'].iloc[:, 0] if isinstance(df_scan['Close'], pd.DataFrame) else df_scan['Close']
                    c_price = c_close.iloc[-1]
                    r_val = calculate_rsi(c_close).iloc[-1]
                    gen_results.append({
                        "اسٹاک": s_sym,
                        "قیمت": f"Rs. {c_price:,.2f}",
                        "RSI": round(r_val, 2)
                    })
            except Exception:
                pass
            progress.progress((idx + 1) / len(all_list))
        st.dataframe(pd.DataFrame(gen_results), use_container_width=True)
