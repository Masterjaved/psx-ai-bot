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

# گٹ ہب سیکریٹس سے ای میل معلومات حاصل کرنا
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

if s_email and s_pass and r_email:
    if is_morning:
        subject = '🌅 PSX پری اوپننگ AI رپورٹ (بڑھوتری والے شیئرز)'
        header_title = '🌅 PSX صبح کی پری اوپننگ مارکیٹ رپورٹ'
    else:
        subject = '🌆 PSX شام کی پورٹ فولیو و کلوزنگ سمری رپورٹ'
        header_title = '🌆 PSX مارکیٹ کلوزنگ پورٹ فولیو رپورٹ'

    body = f"{header_title}\n"
    body += "==================================================\n\n"

    if is_morning:
        body += "🚀 **مارکیٹ کھلنے پر جن شیئرز میں بڑھوتری (Upward Breakout) کے چانسز ہیں:**\n\n"
    else:
        body += "🔍 **مارکیٹ کلوزنگ پر سب سے سستے (Oversold Bargain) شیئرز:**\n\n"

    watch_stocks = ['FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'MEBL', 'SYS', 'MLCF', 'DGKC', 'POL', 'TRG', 'PAEL']
    growth_found = False

    for wsym in watch_stocks:
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

                if latest_rsi <= 38 or (latest_vol > 1.5 * avg_vol and latest_rsi < 60):
                    growth_found = True
                    curr_p = close.iloc[-1]
                    body += f"• {wsym} | قیمت: Rs.{curr_p:,.2f} | RSI: {latest_rsi} --> (خرید زون / بڑھوتری چانس)\n"
        except Exception:
            pass

    if not growth_found:
        body += "• تمام شیئرز فی الحال نارمل رینج میں ہیں۔\n"

    body += "\n--------------------------------------------------\n"

    for user, u_port in port_db.items():
        if u_port:
            body += f"📂 **{user.upper()} کا ذاتی پورٹ فولیو:**\n\n"
            tot_cost = 0
            tot_val = 0

            for sym, pinfo in u_port.items():
                try:
                    p_url = f'https://dps.psx.com.pk/company/{sym}'
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
                    status = '⚠️ اسٹاپ لاس الرٹ (نقصان کا خدشہ)'

                body += f"• {sym}: خرید Rs.{b_price:,.2f} | لائیو Rs.{price:,.2f} | نفع/نقصان: Rs.{pnl:+,.2f} [{status}]\n"

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
