from django.shortcuts import render
import requests
import pandas as pd
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt

warnings.filterwarnings('ignore')

# URLS and names
urls = ["https://www.cryptodatadownload.com/cdd/Bitfinex_EOSUSD_d.csv", 
        "https://www.cryptodatadownload.com/cdd/Bitfinex_EDOUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_BTCUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_ETHUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_LTCUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_BATUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_OMGUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_DAIUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_ETCUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_ETPUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_NEOUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_REPUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_TRXUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_XLMUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_XMRUSD_d.csv",
        "https://www.cryptodatadownload.com/cdd/Bitfinex_XVGUSD_d.csv", 
       ]
crypto_names = ["EOS Coin (EOS)",
                "Eidoo (EDO)",
                "Bitcoin (BTC)",
                "Ethereum (ETH)",
                "Litecoin (LTC)",
                "Basic Attention Token (BAT)",
                "OmiseGO (OMG)",
                "Dai (DAI)",
                "Ethereum Classic (ETC)",
                "Metaverse (ETP)",
                "Neo (NEO)",
                "Augur (REP)",
                "TRON (TRX)",
                "Stellar (XLM)",
                "Monero (XMR)",
                "Verge (XVG)"
               ]

START_DATE = "2024-01-11"
RSI_TIME_WINDOW = 7

def df_loader(urls , start_date = "2021-01-01"):
    filenames = []
    all_df = pd.DataFrame()
    for idx, url in enumerate(urls):
        req = requests.get(url, verify=False)
        url_content = req.content
        filename = url[48:]
        csv_file = open(filename , 'wb')
        csv_file.write(url_content)
        csv_file.close()
        filename = filename[:-9]
        filenames.append(filename)
    for file in filenames:
        df = pd.read_csv(file + "USD_d.csv", header = 1, parse_dates=["date"])
        df = df[df["date"] > start_date]
        df.index = df.date
        df.drop(labels = [df.columns[0], df.columns[1], df.columns[8]] , axis = 1 , inplace = True)
        all_df = pd.concat([all_df, df], ignore_index=False)
    return all_df, filenames 

def computeRSI(data, time_window):
    diff = data.diff(1).dropna()
    up_chg = 0 * diff
    down_chg = 0 * diff
    up_chg[diff > 0] = diff[diff > 0]
    down_chg[diff < 0] = diff[diff < 0]
    up_chg_avg = up_chg.ewm(com=time_window-1, min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1, min_periods=time_window).mean()
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    return rsi

def plot_cryptos(request):
    all_df, filenames = df_loader(urls, start_date=START_DATE)
    crypto_df = []
    for file in filenames:
        symbol = file + "/USD"
        temp_df = pd.DataFrame(all_df[all_df["symbol"] == symbol])
        temp_df.drop(columns=["symbol"], inplace=True)
        temp_df["close_rsi"] = computeRSI(temp_df['close'], time_window=RSI_TIME_WINDOW)
        temp_df["high_rsi"] = 30
        temp_df["low_rsi"] = 70
        crypto_df.append(temp_df)

    fig = make_subplots(rows=3, cols=2, shared_xaxes=True,
                        specs=[[{"rowspan": 2}, {"rowspan": 2}], [{"rowspan": 1}, {"rowspan": 1}] , [{},{}]])

    date_buttons = [
        {'step': "all", 'label': "All time"},
        {'count': 1, 'step': "year", 'stepmode': "backward", 'label': "Last Year"},
        {'count': 1, 'step': "year", 'stepmode': "todate", 'label': "Current Year"},
        {'count': 1, 'step': "month", 'stepmode': "backward", 'label': "Last 2 Months"},
        {'count': 1, 'step': "month", 'stepmode': "todate", 'label': "Current Month"},
        {'count': 7, 'step': "day", 'stepmode': "todate", 'label': "Current Week"},
        {'count': 4, 'step': "day", 'stepmode': "backward", 'label': "Last 4 days"},
        {'count': 1, 'step': "day", 'stepmode': "backward", 'label': "Today"},
    ]
    buttons = []
    i = 0
    j = 0
    COUNT = 8
    vis = [False] * len(crypto_names) * COUNT
    for df in crypto_df:
        for k in range(COUNT):
            vis[j+k] = True
        buttons.append({
            'label': crypto_names[i],
            'method': 'update',
            'args': [{'visible': vis},
                     {'title': crypto_names[i] + ' Charts and Indicators'}
                    ]
        })
        i += 1
        j += COUNT
        vis = [False] * len(crypto_names) * COUNT

    for df in crypto_df:
        fig.add_trace(
            go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], showlegend=False),
            row=1, col=1)
        fig.add_trace(
            go.Bar(x=df.index, y=df["Volume USD"], showlegend=False, marker_color='aqua'),
            row=3, col=1)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['close'], mode='lines', showlegend=False, line=dict(color="red", width=4)),
            row=1, col=2)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['low'], fill='tonexty', mode='lines', showlegend=False, line=dict(width=2, color='pink', dash='dash')),
            row=1, col=2)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['high'], fill='tonexty', mode='lines', showlegend=False, line=dict(width=2, color='pink', dash='dash')),
            row=1, col=2)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['close_rsi'], mode='lines', showlegend=False, line=dict(color="aquamarine", width=4)),
            row=3, col=2)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['low_rsi'], fill='tonexty', mode='lines', showlegend=False, line=dict(width=2, color='pink', dash='dash')),
            row=3, col=2)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['high_rsi'], fill='tonexty', mode='lines', showlegend=False, line=dict(width=2, color='pink', dash='dash')),
            row=3, col=2)

    fig.update_layout(
        title='Charts and Indicators',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis=dict(rangeselector=dict(buttons=date_buttons)),
        updatemenus=[{'buttons': buttons}],
        height=1200, width=1800)

    fig_div = fig.to_html(full_html=False)
    return render(request, 'charts/plot.html', {'plot_div': fig_div})
