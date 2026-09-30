import json
import os
import smtplib
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GitHub Secrets سے معلومات حاصل کرنا
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

# شریعہ کمپلائنٹ (KMI-30 / Islamic Compliant) اسٹاکس کی فہرست
SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

# KSE-100 اور دیگر ایکٹیو اسٹاکس
NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

if s_email and s_pass and r_email:
    if is_morning:
        subject = '🌅 PSX پری اوپننگ AI رپورٹ (شریعہ و KSE-100 بریک آؤٹ الرٹس)'
        header_title = '🌅 PSX مارکیٹ پری اوپننگ جامع AI رپورٹ'
    else:
        subject = 'جاوید اقبال صاحب، پریشان بالکل نہ ہوں! گٹ ہب (GitHub) میں بعض اوقات ویب پیج کیشے (Cache) یا نیٹ ورک کی تاخیر کی وجہ سے پرانی فائل ہی بار بار دکھاتا رہتا ہے، جس کی وجہ سے نیا کوڈ سیو نہیں ہو پاتا اور وہی ایرر سامنے آتا رہتا ہے[cite: 6]۔

اس مسئلے کا ۱۰۰٪ حل یہ ہے کہ ہم پرانی فائل کو بالکل ڈیلیٹ کر کے ایک نئی اور صاف فائل بنا لیں:

---

### طریقہ (فائل ڈیلیٹ کر کے نئی بنانے کا):

#### **قدم ۱: پرانی `send_report.py` کو ڈیلیٹ کریں**
1. اپنے GitHub پر جا کر **`send_report.py`** فائل پر کلک کریں۔
2. اوپر دائیں طرف **تین نقطوں (`...`)** پر کلک کریں اور **`Delete file`** منتخب کریں۔
3. نیچے سبز رنگ کا **`Commit changes`** بٹن دبا دیں۔ (اب وہ غلطی والی فائل ختم ہو جائے گی)۔

#### **قدم ۲: بالکل نئی `send_report.py` بنائیں**
1. ہوم پیج پر **`Add file`** ➔ **`Create new file`** پر کلک کریں۔
2. فائل کا نام رکھیں: **`send_report.py`**
3. نیچے دیا گیا کوڈ بالکل اسی طرح کاپی کر کے وہاں پیسٹ کر دیں:

```python
import json
import os
import smtplib
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GitHub Secrets سے معلومات حاصل کرنا
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

# شریعہ کمپلائنٹ (KMI-30 / Islamic Compliant) اسٹاکس کی فہرست
SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

# KSE-100 اور دیگر ایکٹیو اسٹاکس
NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

if s_email and s_pass and r_email:
    if is_morning:
        subject = '🌅 PSX پری اوپننگ AI رپورٹ (شریعہ و KSE-100 بریک آؤٹ الرٹس)'
        header_title = '🌅 PSX مارکیٹ پری اوپننگ جامع AI رپورٹ'
    else:
        subject = '🌆 PSX شام کی پورٹ فولیو و کلوزنگ سمری رپورٹ'
        header_title = 'جاوید اقبال صاحب، پریشان بالکل نہ ہوں! گٹ ہب (GitHub) میں بعض اوقات ویب پیج کیشے (Cache) یا نیٹ ورک کی تاخیر کی وجہ سے پرانی فائل ہی بار بار دکھاتا رہتا ہے، جس کی وجہ سے نیا کوڈ سیو نہیں ہو پاتا اور وہی ایرر سامنے آتا رہتا ہے[cite: 6]۔

اس مسئلے کا ۱۰۰٪ حل یہ ہے کہ ہم پرانی فائل کو بالکل ڈیلیٹ کر کے ایک نئی اور صاف فائل بنا لیں:

---

### طریقہ (فائل ڈیلیٹ کر کے نئی بنانے کا):

#### **قدم ۱: پرانی `send_report.py` کو ڈیلیٹ کریں**
1. اپنے GitHub پر جا کر **`send_report.py`** فائل پر کلک کریں۔
2. اوپر دائیں طرف **تین نقطوں (`...`)** پر کلک کریں اور **`Delete file`** منتخب کریں۔
3. نیچے سبز رنگ کا **`Commit changes`** بٹن دبا دیں۔ (اب وہ غلطی والی فائل ختم ہو جائے گی)۔

#### **قدم ۲: بالکل نئی `send_report.py` بنائیں**
1. ہوم پیج پر **`Add file`** ➔ **`Create new file`** پر کلک کریں۔
2. فائل کا نام رکھیں: **`send_report.py`**
3. نیچے دیا گیا کوڈ کاپی کر کے وہاں پیسٹ کر دیں:

```python
import json
import os
import smtplib
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GitHub Secrets سے معلومات حاصل کرنا
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

# شریعہ کمپلائنٹ (KMI-30 / Islamic Compliant) اسٹاکس کی فہرست
SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

# KSE-100 اور دیگر ایکٹیو اسٹاکس
NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

if s_email and s_pass and r_email:
    if is_morning:
        subject = '🌅 PSX پری اوپننگ AI رپورٹ (شریعہ و KSE-100 بریک آؤٹ الرٹس)'
        header_title = '🌅 PSX مارکیٹ پری اوپننگ جامع AI رپورٹ'
    else:
        subject = '🌆 PSX شام کی پورٹ فولیو و کلوزنگ سمری رپورٹ'
        header_title = 'جاوید اقبال صاحب، پریشان بالکل نہ ہوں! گٹ ہب (GitHub) میں بعض اوقات ویب پیج کیشے (Cache) یا نیٹ ورک کی تاخیر کی وجہ سے پرانی فائل ہی بار بار دکھاتا رہتا ہے، جس کی وجہ سے نیا کوڈ سیو نہیں ہو پاتا اور وہی ایرر سامنے آتا رہتا ہے[cite: 6]۔

اس مسئلے کا ۱۰۰٪ حل یہ ہے کہ ہم پرانی فائل کو بالکل ڈیلیٹ کر کے ایک نئی اور صاف فائل بنا لیں:

---

### طریقہ (فائل ڈیلیٹ کر کے نئی بنانے کا):

#### **قدم ۱: پرانی `send_report.py` کو ڈیلیٹ کریں**
1. اپنے GitHub پر جا کر **`send_report.py`** فائل پر کلک کریں۔
2. اوپر دائیں طرف **تین نقطوں (`...`)** پر کلک کریں اور **`Delete file`** منتخب کریں۔
3. نیچے سبز رنگ کا **`Commit changes`** بٹن دبا دیں۔ (اب وہ غلطی والی فائل ختم ہو جائے گی)۔

#### **قدم ۲: بالکل نئی `send_report.py` بنائیں**
1. ہوم پیج پر **`Add file`** ➔ **`Create new file`** پر کلک کریں۔
2. فائل کا نام رکھیں: **`send_report.py`**
3. نیچے دیا گیا کوڈ کاپی کر کے وہاں پیسٹ کر دیں:

```python
import json
import os
import smtplib
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GitHub Secrets سے معلومات حاصل کرنا
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

# شریعہ کمپلائنٹ (KMI-30 / Islamic Compliant) اسٹاکس کی فہرست
SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

# KSE-100 اور دیگر ایکٹیو اسٹاکس
NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

if s_email and s_pass and r_email:
    if is_morning:
        subject = '🌅 PSX پری اوپننگ AI رپورٹ (شریعہ و KSE-100 بریک آؤٹ الرٹس)'
        header_title = '🌅 PSX مارکیٹ پری اوپننگ جامع AI رپورٹ'
    else:
        subject = '🌆 PSX شام کی پورٹ فولیو و کلوزنگ سمری رپورٹ'
        header_title = '🌆 PSX مارکیٹ کلوزنگ پورٹ فولیو رپورٹ'

    body = f"{header_title}\n"
    body += "==================================================\n\n"

    all_stocks = [(s, True) for s in SHARIAH_STOCKS] + [(s, False) for s in NON_SHARIAH_STOCKS]

    buy_list = []
    sell_list = []

    for wsym, is_shariah in all_stocks:
        try:
            df = yf.download(f'{wsym}.KA', period='1mo', interval='1d', progress=False)
            if not df.empty:
                close = df['Close'].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df['Close']
                volume = df['Volume'].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df['Volume']

                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain / loss)))
                latest_rsi = round(rsi.iloc[-1], 2)

                avg_vol = volume.rolling(10).mean().iloc[-1]
                latest_vol = volume.iloc[-1]
                curr_p = close.iloc[-1]

                tag = "🕌 [شریعہ کمپلائنٹ]" if is_shariah else "🏛️️ [KSE-100 / جنرل]"

                # خرید کا موقع (Oversold یا Volume Surge)
                if latest_rsi <= 38 or (latest_vol > 1.8 * avg_vol and latest_rsi < 60):
                    buy_list.append(f"• {wsym} {tag} | قیمت: Rs.{curr_p:,.2f} | RSI: {latest_rsi} --> 🟢 (خرید کا بہترین موقع / Momentum)")
                
                # بیچنے کا موقع (Overbought Zone)
                elif latest_rsi >= 68:
                    sell_list.append(f"• {wsym} {tag} | قیمت: Rs.{curr_p:,.2f} | RSI: {latest_rsi} --> 🔴 (منافع بک کریں / SELL)")
        except Exception:
            pass

    # 1. خرید والے شیئرز
    body += "🚀 **خریداری / بڑھوتری کے قوی امکانات والے شیئرز (BUY Signals):**\n\n"
    if buy_list:
        body += "\n".join(buy_list) + "\n"
    else:
        body += "• اس وقت کوئی شیئر اوور سولڈ زون میں نہیں ہے۔\n"

    body += "\n--------------------------------------------------\n"

    # 2. مہنگے / بیچنے والے شیئرز
    body += "⚠️ **اوور باٹ / مہنگے شیئرز (SELL Signals / Profit Booking):**\n\n"
    if sell_list:
        body += "\n".join(sell_list) + "\n"
    else:
        body += "• اس وقت کوئی شیئر انتہائی مہنگے (Overbought) زون میں نہیں ہے۔\n"

    body += "\n==================================================\n"

    # 3. پورٹ فولیو کا جائزہ
    for user, u_port in port_db.items():
        if u_port:
            body += f"\n📂 **{user.upper()} کا ذاتی پورٹ فولیو:**\n\n"
            tot_cost = 0
            tot_val = 0

            for sym, pinfo in u_port.items():
                try:
                    p_url = f'[https://dps.psx.com.pk/company/](https://dps.psx.com.pk/company/){sym}'
                    res = requests.get(p_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).text
                    soup = BeautifulSoup(res, 'html.parser')
                    p_div = soup.find('div', {'class': 'quote__close'})
                    price = float(p_div.text.strip().replace('Rs.', '').replace(',', '')) if p_div else pinfo.get('Buy Price', 0)
                except Exception:
                    price = pinfo.get('Buy Price', 0)

                b_price = pinfo.get('Buy Price', 0)
                qty = pinfo.get('Quantity', 1)
                t_sell = pinfo.get('Target Sell', b_price * 1.15)
                s_loss = pinfo.get('Stop Loss', b_price * 0.90)

                c_tot = b_price * qty
                v_tot = price * qty
                tot_cost += c_tot
                tot_val += v_tot
                pnl = v_tot - c_tot

                status = 'ہولڈنگ (HOLDING)'
                if price >= t_sell:
                    status = '🎯 ٹارگٹ مکمل (بیچ دیں)'
                elif price <= s_loss:
                    status = '⚠️ اسٹاپ لاس الرٹ'

                sharia_tag = " 🕌" if sym in SHARIAH_STOCKS else ""
                body += f"• {sym}{sharia_tag}: خرید Rs.{b_price:,.2f} | لائیو Rs.{price:,.2f} | نفع/نقصان: Rs.{pnl:+,.2f} [{status}]\n"

            tot_pnl = tot_val - tot_cost
            body += f"\n💰 کل سرمایہ کاری: Rs.{tot_cost:,.2f} | موجودہ مالیت: Rs.{tot_val:,.2f}\n"
            body += f"📈 کل نفع / نقصان: Rs.{tot_pnl:+,.2f}\n"

    body += "\n==================================================\n"
    body += "یہ رپورٹ PSX AI کلاؤڈ سسٹم سے خودکار طریقے سے بھیجی گئی ہے۔"

    try:
        msg = MIMEMultipart()
        msg['From'] = s_email
        msg['To'] = r_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(s_email, s_pass)
        server.send_message(msg)
        server.quit()
        print('ای میل کامیابی سے بھیج دی گئی ہے!')
    except Exception as e:
        print('ای میل بھیجنے میں غلطی:', e)
