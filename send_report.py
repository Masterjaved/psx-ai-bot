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

# GitHub Secrets
s_email = os.environ.get('SENDER_EMAIL')
s_pass = os.environ.get('SENDER_PASS')
r_email = os.environ.get('RECEIVER_EMAIL')

now_utc_hour = datetime.datetime.utcnow().hour
is_morning = now_utc_hour < 8

def load_db(fp):
    return json.load(open(fp, 'r', encoding='utf-8')) if os.path.exists(fp) else {}

port_db = load_db('portfolios_db.json')

SHARIAH_STOCKS = [
    'FFC', 'OGDC', 'LUCK', 'HUBC', 'PPL', 'ENGRO', 'EFERT', 'SYS', 
    'MLCF', 'DGKC', 'POL', 'MEBL', 'PAEL', 'AIRLINK', 'FCCL', 'PRL', 
    'SHEL', 'SEARL', 'AVN', 'GATRON', 'TREAT', 'MARI', 'PSO', 'DCR'
]

NON_SHARIAH_STOCKS = [
    'TRG', 'CNERGY', 'KEL', 'HUMNL', 'TELE', 'WTL', 'MCB', 'UBL', 'HBL', 'BANK'
]

if s_email and s_pass and r_email:
    if is_morning:
        subject = 'PSX Morning Market AI Report'
        header_title = 'PSX Pre-Opening AI Market Report'
    else:
        subject = 'PSX Evening Portfolio & Closing Report'
        header_title = 'PSX Market Closing Portfolio Report'

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

                tag = "[Shariah Compliant]" if is_shariah else "[KSE-100 / General]"

                if latest_rsi <= 38 or (latest_vol > 1.8 * avg_vol and latest_rsi < 60):
                    buy_list.append(f"• {wsym} {tag} | Price: Rs.{curr_p:,.2f} | RSI: {latest_rsi} --> BUY Signal")
                elif latest_rsi >= 68:
                    sell_list.append(f"• {wsym} {tag} | Price: Rs.{curr_p:,.2f} | RSI: {latest_rsi} --> SELL Signal")
        except Exception:
            pass

    body += "BUY Signals / Breakout Opportunities:\n\n"
    if buy_list:
        body += "\n".join(buy_list) + "\n"
    else:
        body += "• No stocks in buy zone currently.\n"

    body += "\n--------------------------------------------------\n"

    body += "SELL Signals / Overbought Alerts:\n\n"
    if sell_list:
        body += "\n".join(sell_list) + "\n"
    else:
        body += "• No stocks in overbought zone currently.\n"

    body += "\n==================================================\n"

    for user, u_port in port_db.items():
        if u_port:
            body += f"\nPortfolio Status ({user.upper()}):\n\n"
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

                status = 'HOLDING'
                if price >= t_sell:
                    status = 'TARGET REACHED'
                elif price <= s_loss:
                    status = 'STOP LOSS ALERT'

                sharia_tag = " [Shariah]" if sym in SHARIAH_STOCKS else ""
                body += f"• {sym}{sharia_tag}: Buy Rs.{b_price:,.2f} | Live Rs.{price:,.2f} | P&L: Rs.{pnl:+,.2f} [{status}]\n"

            tot_pnl = tot_val - tot_cost
            body += f"\nTotal Investment: Rs.{tot_cost:,.2f} | Current Value: Rs.{tot_val:,.2f}\n"
            body += f"Total P&L: Rs.{tot_pnl:+,.2f}\n"

    body += "\n==================================================\n"
    body += "Report generated automatically by PSX AI Cloud System."

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
        print('Email sent successfully!')
    except Exception as e:
        print('Email failed:', e)
