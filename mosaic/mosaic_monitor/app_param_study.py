import streamlit as st
import pandas as pd
import tqdm
import os
from datetime import datetime
import backtest_class as btu
import sys
sys.path.insert(0, '/home/abdel/Bureau/new_project/mosaic')
import mosaic
from mosaic.trading.exchange import ExchangeCCXT
import pkg_resources
from mosaic.decision_model import dm_ta as sta
import mosaic.decision_model.dm_base as sml
import mosaic.indicator as mid 
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401import pandas as pd
import base64
import dash   
from datetime import datetime
from dash.dependencies import Input, Output
import plotly.io as pio
import ccxt
import itertools
import warnings
import numpy as np
from dash.dash_table.Format import Group
from dash import dash_table
from dash.dash_table import DataTable
from plotly.graph_objs import Box
import importlib
import os
import dash
import dash_bootstrap_components as dbc
import sys
from scipy import stats
import hashlib
import json
from dash import Dash, dcc, html, State
from itertools import product
import time
import numpy as np
from dash import callback_context
import plotly.express as px
import plotly.graph_objects as go
import mosaic.predict_model.pm_stats as pms
from plotly.subplots import make_subplots
import requests
#import mosaic.decision_model as sta
import numpy as np
import os
import sys
import tqdm
import time
from mosaic.trading.exchange import ExchangeCCXT
import pkg_resources
#mosaic_version = pkg_resources.get_distribution(" mosaic_abdel.mosaic_test").version
#print('mosaic version:', mosaic_version)
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401
pio.templates.default = "plotly_dark"
warnings.filterwarnings('ignore')
# Initialisation de Binance
exchange = ccxt.binance()



exchange=ExchangeCCXT(name='binance')
exchange.connect()








# utiliser la classe fetch_ohlcv de mosaic 

def fetch_ohlcv(symbol, timeframe='1h', start_date=None, end_date=None,  exchange_name='binance'):
    # Convertit les dates en timestamp UNIX (en millisecondes)


    exchange=ExchangeCCXT(name=exchange_name)
    exchange.connect()
    df=exchange.get_historic_ohlcv(
                    date_start=start_date,
                    date_end=end_date,
                    symbol=symbol,
                    timeframe=timeframe,
                    index="datetime",
                    data_dir="ohlcv_binance",
                    force_reload=False,
                    progress_mode=True,
                )
    
    df.index.name='time'
    df=df.reset_index()
    df['time'] = pd.to_datetime(df['time'],utc=True)
    df.set_index('time', inplace=True)
    df = df[~df.index.duplicated(keep='first')]
    #df.index = df.index.tz_localize('UTC')  # Définit le fuseau horaire sur UTC
    #ipdb.set_trace()
    # since = None
    # if start_date:
    #     since = int(pd.Timestamp(start_date).timestamp() * 1000)
    
    # all_candles = []
    # while True:
    #     exchange = getattr(ccxt, exchange_name)()
    #     candles = exchange.fetch_ohlcv(symbol, timeframe, since)
    #     if len(candles) == 0:
    #         break
    #     since = candles[-1][0] + 1
    #     all_candles.extend(candles)
    #     if end_date and since > int(pd.Timestamp(end_date).timestamp() * 1000):
    #         break
    
    # df = pd.DataFrame(all_candles, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    # df['time'] = pd.to_datetime(df['time'], unit='ms')
    # df.set_index('time', inplace=True)
    # df.index = df.index.tz_localize('UTC')  # Définit le fuseau horaire sur UTC
    # # Filtrage final basé sur les dates de début et de fin
    # if start_date:
    #     df = df[df.index >= start_date]
    # if end_date:
    #     df = df[df.index <= end_date]
    
    return df

# # Utilisation
# symbol = 'BTC/USDT'
# start_date = '2020-10-01'
# end_date = '2020-12-31'
# data = fetch_ohlcv(symbol, '1h', start_date, end_date)
# #print(data)
# #source_filename = '/home/abdel/Téléchargements/ohlcv_crypto_5m_binance_BTC_USDC_2019-01-01 00_00_00_2022-01-01 00_00_00.csv.bz2'
# # btc_usdc_2021_df = pd.read_csv(source_filename,
#     # index_col="time",
#     # parse_dates=["time"])
# ohlcv_df= data.dropna()
# print("Data loaded")


############################################################################################
def get_trading_fees(exchange_name, symbol=None):
    exchange = getattr(ccxt, exchange_name)()
    exchange.load_markets()
    
    if symbol is not None:
        market = exchange.markets.get(symbol)
        if market is not None:
            return market.get('maker'), market.get('taker')
        else:
            return None, None
    
    trading_fees = {}
    for symbol, market in exchange.markets.items():
        maker = market.get('maker')
        taker = market.get('taker')
        
        if maker is not None and taker is not None:
            trading_fees[symbol] = {'maker': maker, 'taker': taker}
            
    return trading_fees

def find_exchanges_for_symbol(symbol):
    exchanges_for_symbol = []
    for exchange_id in ccxt.exchanges:
        exchange = getattr(ccxt, exchange_id)()
        try:
            exchange.load_markets()
            if symbol in exchange.symbols:
                exchanges_for_symbol.append(exchange_id)
        except (ccxt.NetworkError, ccxt.ExchangeError):
            pass
        except Exception as e:
            print(f"An unexpected error occurred for exchange {exchange_id}: {type(e).__name__}, {str(e)}")
    return exchanges_for_symbol

symbol = 'BTC/USDT'
#exchanges = find_exchanges_for_symbol(symbol)
#print(f"Exchanges that support {symbol}: {exchanges}")

#################### 1. Configuration des stratégies et de leurs paramètres:
#Exchanges that support GOLD/USDT: ['bittrex', 'coinex', 'gate', 'gateio', 'hitbtc', 'hitbtc3', 'phemex']

# Define the strategies and their parameters



strategy_dict = {
    'RSIStrategy': sta.RSIStrategy,
    'BBStrategy':  sta.BBStrategy,
    'MOMStrategy':  sta.MOMStrategy,
    'MACRossoverStrategy':  sta.SMAStrategy,
    'STOCHStrategy': sta.STOCAStrategy,
    'MFIStrategy': sta.MFIStrategy,
    'MACDStrategy':sta.MACDStrategy,
    'ATRStrategy':sta.ATRStrategy,
    'HAMMERStrategy':sta.HammerStrategy,
    'RSIDivergenceStrategy':sta.RSIDivergenceStrategy,
    'MACDDivergenceStrategy':sta.MACDDivergenceStrategy,
    'FibonacciRetracementStrategy':sta.FibonacciRetracementStrategy,
    'ADXStrategy':sta.ADXStrategy,
    'IchimokuStrategy':sta.IchimokuStrategy,
    'DonchianChannelStrategy':sta.DonchianChannelStrategy,
    'MACD_SMA_Strategy':sta.MACD_SMA_Strategy,
    'BreakoutStrategy':sta.BreakoutStrategy,
    'MACD_RSIStrategy':sta.MACD_RSIStrategy,
    #'KalmanMeanReversionStrategy': sta.KalmanMeanReversionStrategy,
    'DojiStrategy':sta.DojiStrategy,
    'DM1ML':sml.DM1ML,
    'DM2ML':sml.DM2ML,
    
}

  
    # Définissez les options de modèle disponibles pour 'DM1ML'
dm1ml_model_options = {
    'PMOLS': pms.PMOLS,
    'PMLogit': pms.PMLogit,
    # Ajoutez d'autres options de modèle au besoin
    }

# Définissez les options d'indicateur disponibles pour 'DM1ML'
dm1ml_indicator_options = {
    'RSI': mid.RSI(),
    'MFI': mid.MFI(),
    'MOM':mid.MOM(),
    # Ajoutez d'autres options d'indicateur au besoin
}

direction_sell={
    'down':'down',
}


direction_buy={
    'up':'up',
}



strategy_parameters = {
    'RSIStrategy': [
        {'id': 'buy_level', 'placeholder': 'Buy Level', 'min_value': 1, 'max_value': 100,'step':1, 'default_value': (30, 70)},
        {'id': 'sell_level', 'placeholder': 'Sell Level', 'min_value': 1, 'max_value': 100, 'step':1,'default_value': (30,70)},
        {'id': 'window', 'placeholder': 'RSI Window', 'min_value': 1, 'max_value': 100, 'step':1,'default_value': (14, 30)},
    ],
    'MFIStrategy': [
        {'id': 'buy_level', 'placeholder': 'Buy Level', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (30, 70)},
        {'id': 'sell_level', 'placeholder': 'Sell Level', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (30,70)},
        {'id': 'length', 'placeholder': 'MFI Window', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (14, 30)},
    ],
    
   'HAMMERStrategy': [
    {'id': 'beta', 'type': 'number', 'placeholder': 'beta hammer', 'min_value': 11.0, 'max_value': 100.0, 'step': 1.0, 'default_value': (1.5, 2.8)},
    {'id': 'alpha', 'type': 'number', 'placeholder': 'alpha hammer', 'min_value': 0.0, 'max_value': 0.01, 'step': 0.01, 'default_value': (0.1, 0.7)},
    {'id': 'profit_threshold', 'type': 'number', 'placeholder': 'profit_threshold', 'min_value': 0.01, 'max_value': 0.03, 'step': 0.01, 'default_value': (0.0, 0.1)},
    {'id': 'stop_loss_threshold', 'type': 'number', 'placeholder': 'stop_loss_threshold', 'min_value': -0.02, 'max_value': 0.0, 'step': 0.01, 'default_value': (-0.03, -0.015)},
    {'id': 'window', 'type': 'number', 'placeholder': ' window', 'min_value': 2, 'max_value': 100,'step': 1, 'value': 14},
],

   'BBStrategy': [
    {'id': 'std', 'type': 'number', 'placeholder': 'BB std', 'min_value': 0.0, 'max_value': 20.0,'step':0.01, 'default_value': (0.01,20.0)},
    {'id': 'length', 'type': 'number', 'placeholder': 'BB Window', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (1,100)},
    {'id': 'ddof', 'type': 'number', 'placeholder': 'BB ddof', 'min_value': 0, 'max_value': 0, 'default_value': (0,0)},],


    'MOMStrategy': [
    {'id': 'period_mom', 'type': 'number', 'placeholder': 'period mom', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (10, 20)},
    {'id': 'threshold', 'type': 'number', 'placeholder': 'mom threshold', 'min_value': -0.3, 'max_value': 3.0,'step':0.1, 'default_value': (0, 5)},],


    'MACRossoverStrategy': [
    {'id': 'short_moving_average', 'type': 'number', 'placeholder': 'sma period', 'min_value': 0, 'max_value': 300, 'default_value': (1, 150)},
    {'id': 'long_moving_average', 'type': 'number', 'placeholder': 'sma period', 'min_value': 0, 'max_value': 100, 'default_value': (1, 300)},],


    'STOCHStrategy': [
    {'id': 'buy_level', 'type': 'number', 'placeholder': 'Buy Level', 'min_value': 1, 'max_value': 100, 'step':5, 'default_value': (1, 100)},
    {'id': 'sell_level', 'type': 'number', 'placeholder': 'Sell Level', 'min_value': 1, 'max_value': 100,'step':5 ,'default_value': (1, 100)},
    {'id': 'window_short', 'type': 'number', 'placeholder': 'window stoch short', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (3, 50)},
    {'id': 'window_long', 'type': 'number', 'placeholder': 'window stoch long', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (3, 50)},
    {'id': 'smooth_k', 'type': 'number', 'placeholder': 'smoothk stoch ', 'min_value': 3, 'max_value': 3,  'default_value': (3, 3)},],

    'MACDStrategy': [
    {'id': 'level', 'type': 'number', 'placeholder': ' Level', 'min_value': -10.0, 'max_value': 10.0, 'step': 0.01, 'default_value': (-10, 10)},
    {'id': 'fast', 'type': 'number', 'placeholder': 'fast window', 'min_value': 5, 'max_value': 100,'step':5, 'default_value': (10, 20)},
    {'id': 'slow', 'type': 'number', 'placeholder': 'slow window', 'min_value': 3, 'max_value': 100,'step':5, 'default_value': (20, 30)},
    {'id': 'signal', 'type': 'number', 'placeholder': 'signal window', 'min_value': 2, 'max_value': 100,'step':5, 'default_value': (5, 10)},],

       
    'MACD_RSIStrategy': [
    {'id': 'fast', 'type': 'number', 'placeholder': 'fast window', 'min_value': 5, 'max_value': 100,'step':5, 'default_value': (10, 20)},
    {'id': 'slow', 'type': 'number', 'placeholder': 'slow window', 'min_value': 3, 'max_value': 100,'step':5, 'default_value': (20, 30)},
    {'id': 'signal', 'type': 'number', 'placeholder': 'signal window', 'min_value': 2, 'max_value': 100,'step':5, 'default_value': (5, 10)},
    {'id': 'buy_level', 'type': 'number', 'placeholder': 'Buy Level', 'min_value': 1, 'max_value': 100, 'step':5, 'default_value': (20, 40)},
    {'id': 'sell_level', 'type': 'number', 'placeholder': 'Sell Level', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (60, 80)},
    {'id': 'window', 'type': 'number', 'placeholder': 'RSI Window', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (10, 20)},],

        
      
   'ATRStrategy': [
    {'id': 'threshold_atr', 'type': 'number', 'placeholder': 'threshold_atr', 'min_value': 0.01, 'max_value': 0.25, 'step': 0.01, 'default_value': (0.05, 0.15)},
    {'id': 'period_atr', 'type': 'number', 'placeholder': 'period_atr', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (10, 20)},],

     'BreakoutStrategy': [
    {'id': 'window', 'type': 'number', 'placeholder': 'window MA', 'min_value': 2, 'max_value': 100, 'step': 1, 'default_value': (10, 30)},
    {'id': 'std', 'type': 'number', 'placeholder': 'BB std', 'min_value': 0.0, 'max_value': 20.0, 'step':0.01,'default_value': (0.01,20.0)},
    {'id': 'length', 'type': 'number', 'placeholder': 'BB Window', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (10, 20)},
    {'id': 'ddof', 'type': 'number', 'placeholder': 'BB ddof', 'min_value': 0, 'max_value': 0, 'default_value': (0, 0)},],

     'RSIDivergenceStrategy': [
    {'id': 'window', 'type': 'number', 'placeholder': 'RSI Window', 'min_value': 1, 'max_value': 100, 'default_value': (2,100)},],

       'MACDDivergenceStrategy': [
    {'id': 'fast', 'type': 'number', 'placeholder': 'fast window', 'min_value': 5, 'max_value': 100, 'default_value': (12, 20)},
    {'id': 'slow', 'type': 'number', 'placeholder': 'slow window', 'min_value': 3, 'max_value': 100, 'default_value': (26, 40)},
    {'id': 'signal', 'type': 'number', 'placeholder': 'signal window', 'min_value': 2, 'max_value': 100, 'default_value': (9, 15)},],

       'FibonacciRetracementStrategy': [
    {'id': 'level_A', 'type': 'number', 'placeholder': 'level_A ', 'min_value': 0.1, 'max_value': 0.8, 'default_value': (0.382, 0.5)},
    {'id': 'level_B', 'type': 'number', 'placeholder': 'level_B ', 'min_value': 0.1, 'max_value': 0.82, 'default_value': (0.5, 0.618)},
    {'id': 'level_C', 'type': 'number', 'placeholder': 'level_C ', 'min_value': 0.1, 'max_value': 0.8, 'default_value': (0.618, 0.75)},],

        'ADXStrategy': [
    {'id': 'buy_level', 'type': 'number', 'placeholder': 'Buy Level', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (1,100)},
    {'id': 'sell_level', 'type': 'number', 'placeholder': 'Sell Level', 'min_value': 1, 'max_value': 100, 'step':5,'default_value': (1,100)},
    {'id': 'window', 'type': 'number', 'placeholder': 'adx Window', 'min_value': 1, 'max_value': 100,'step':5, 'default_value': (2,60)},],

    'IchimokuStrategy': [
    {'id': 'tenkan_window', 'type': 'number', 'placeholder': 'tenkan_window', 'min_value': 1, 'max_value': 200,'step':10, 'default_value': (0, 200)},
    {'id': 'kijun_window', 'type': 'number', 'placeholder': 'kijun_window', 'min_value': 1, 'max_value': 200, 'step':10,'default_value': (0, 200)},
    {'id': 'senkou_span_b_window', 'type': 'number', 'placeholder': 'senkou_span_b', 'min_value': 1, 'max_value': 200,'step':10, 'default_value': (1, 200)},
    {'id': 'displacement', 'type': 'number', 'placeholder': 'displacement', 'min_value': 1, 'max_value': 200,'step':10, 'default_value': (1, 200)},],

     'DonchianChannelStrategy': [
    {'id': 'window', 'type': 'number', 'placeholder': 'window', 'min_value': 1, 'max_value': 300, 'default_value': (0, 300)},],

        
        
    'KeltnerChannelStrategy': [
        {'id': 'window', 'type': 'number', 'placeholder': 'window', 'min': 1, 'max':300, 'default_value': 20},
        {'id': 'multiplier', 'type': 'number', 'placeholder': 'multiplier', 'min': 0.1, 'max': 10,'step':0.1, 'default_value': 2.0},],
       
    'MACD_SMA_Strategy': [
    {'id': 'fast', 'type': 'number', 'placeholder': 'fast window', 'min_value': 5, 'max_value': 100,'step':5, 'default_value': (5, 100)},
    {'id': 'slow', 'type': 'number', 'placeholder': 'slow window', 'min_value': 3, 'max_value': 100,'step':5, 'default_value': (3, 100)},
    {'id': 'signal', 'type': 'number', 'placeholder': 'signal window', 'min_value': 2, 'max_value': 100,'step':5, 'default_value': (2, 100)},
    {'id': 'short_moving_average', 'type': 'number', 'placeholder': 'sma short', 'min_value': 0, 'max_value': 300,'step':5, 'default_value': (0, 300)},
    {'id': 'long_moving_average', 'type': 'number', 'placeholder': 'sma long', 'min_value': 0, 'max_value': 100,'step':5, 'default_value': (0, 100)},],

    
    'DojiStrategy': [
    {'id': 'doji_threshold_ratio', 'type': 'number', 'placeholder': ' doji_threshold_ratio', 'min_value': 0.01, 'max_value': 0.06, 'default_value': (0.01, 0.06)},
    {'id': 'risk_reward_ratio', 'type': 'number', 'placeholder': ' risk_reward_ratio', 'min_value': 1, 'max_value': 4, 'default_value': (1, 4)},],


  'DM1ML' : [
    {'id': 'model', 'placeholder': ' Modèle', 'model': dm1ml_model_options},
    {'id': 'indicators', 'placeholder': 'Indicateurs', 'indicator': dm1ml_indicator_options},
    {'id': 'sell_threshold', 'placeholder': 'Seuil de vente', 'min_value': 0.0, 'max_value': 0.06, 'step': 0.01, 'value': 0.0},
    {'id': 'buy_threshold', 'placeholder': 'Seuil d\'achat', 'min_value': -0.02, 'max_value': 0.0, 'step': -0.01},
    {'id': 'returns_horizon', 'placeholder': 'Horizon des rendements', 'min_value': 1, 'max_value': 30, 'step': 1},
    {'id': 'rsi_window', 'placeholder': 'Fenêtre RSI', 'min_value': 1, 'max_value': 100, 'step': 5},
    {'id': 'mfi_window', 'placeholder': 'Fenêtre MFI', 'min_value': 1, 'max_value': 100, 'step': 5},
    {'id': 'mom_period', 'placeholder': 'Période de MOM', 'min_value': 0, 'max_value': 100, 'step': 5},],


 'DM2ML': [
    {'id': 'model', 'type': 'text', 'placeholder': 'Buy Model', 'model': dm1ml_model_options},
    {'id': 'indicators', 'type': 'text', 'placeholder': 'Buy Indicators', 'indicator': dm1ml_indicator_options},
    {'id': 'buy_direction', 'type': 'text', 'placeholder': 'Direction d achat', 'Direction d achat': direction_buy},
    {'id': 'returns_horizon', 'type': 'number', 'placeholder': 'Returns Horizon', 'min_value': 1, 'max_value': 20, 'value': 1},
    {'id': 'buy-threshold', 'type': 'number', 'placeholder': 'Buy Threshold', 'min_value': 0.0, 'max_value': 0.06, 'step': 0.01, 'value': 0},
    {'id': 'sell_threshold', 'type': 'number', 'placeholder': 'Sell Threshold', 'min_value': 0.0, 'max_value': 0.06, 'step': 0.01, 'value': 0},
    {'id': 'sell_model', 'type': 'text', 'placeholder': 'Sell Model', 'model': dm1ml_model_options},
    {'id': 'sell_indicators', 'type': 'text', 'placeholder': 'Sell Indicators', 'indicator': dm1ml_indicator_options},
    {'id': 'window', 'type': 'number', 'placeholder': 'RSI Window', 'min_value': 1, 'max_value': 100, 'value': 14},
    {'id': 'length_mfi', 'type': 'number', 'placeholder': 'MFI Window', 'min_value': 1, 'max_value': 100, 'value': 14},
    {'id': 'mom_period', 'type': 'number', 'placeholder': 'Period MOM', 'min_value': 0, 'max_value': 100, 'value': 14},
     {'id': 'sell_direction', 'type': 'text', 'placeholder':'Direction de vente', 'Direction de vente': direction_sell}]



}




maker_fee, taker_fee = get_trading_fees('binance',symbol='BTC/USDT')

# Créez une application Streamlit
st.set_page_config(page_title="Mon Application Streamlit",
                   layout="wide",)  # Utilisez une mise en page large pour les onglets

# Créez des onglets pour la configuration et les résultats
tabs = st.sidebar.radio("Sélectionnez un onglet :", ["Configuration", "Résultats"])

if tabs == "Configuration":
    st.markdown("### **Étude Paramétrique des Stratégies**")

    exchange_name=['binance','coinex','kraken','bittrex']
    selected_exchange_name = st.selectbox("Sélectionnez l'exchnage", exchange_name)

    # Sélectionnez le symbole à étudier
    symbols = ["BTC/USDT", "BTC/USDC"]
    selected_symbol = st.selectbox("Sélectionnez le symbole à étudier (par exemple, BTC/USDT)", symbols)

    # Sélectionnez la période de début et de fin
    timeframes = ['5m', '1m', '15m', '30m', '1h', '4h', '1d']
    selected_timeframe = st.selectbox("Sélectionnez la période de temps (timeframe)", timeframes)
    
    start_date = st.date_input("Date de début:", datetime(2018, 1, 1))
    end_date = st.date_input("Date de fin:", datetime(2019, 1, 1))
    
    # Sélectionnez la stratégie
    selected_strategy = st.selectbox("Sélectionnez la stratégie à analyser:", list(strategy_dict.keys()))
    strategy_parameters_specific = strategy_parameters[selected_strategy]

    strategy_params = {}
    for param in strategy_parameters_specific:
        min_value = param.get('min_value', None)
        max_value = param.get('max_value', None)
        #step=param.get('step',None)
        default_step = param.get('step')  # Valeur par défaut pour step
        model_options = param.get('model', None)
        indicator_options = param.get('indicator', None)
        direction_options_sell=param.get('Direction de vente',None)
        direction_options_buy=param.get('Direction d achat',None)

        # if min_value is not None and max_value is not None and min_value != max_value:
        #   # Utiliser st.number_input pour min_val, max_val et step
        #    min_val = st.number_input(f'Minimum {param["placeholder"]}', min_value=min_value, max_value=max_value, value=min_value, step=step)
        #    max_val = st.number_input(f'Maximum {param["placeholder"]}', min_value=min_value, max_value=max_value, value=max_value, step=step)
        #    step_val = st.number_input(f'Step pour {param["placeholder"]}', min_value=0, value=step)

        if min_value is not None and max_value is not None and min_value != max_value:
            # Permettre à l'utilisateur de définir le pas
            step = st.number_input(f'Step pour {param["placeholder"]}', value=default_step)
            min_val, max_val = st.slider(
            param['placeholder'],
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
            step=step
        )
            strategy_params[param['id']] = (min_val, max_val,step)
        elif model_options is not None:
            selected_model_name = st.selectbox(param['placeholder'], list(model_options.keys()))
            selected_model = model_options.get(selected_model_name)
            strategy_params[param['id']] = selected_model
        elif indicator_options is not None:
            selected_indicators = st.multiselect(param['placeholder'], list(indicator_options.keys()))
            selected_indicators = [indicator_options.get(indicator_name) for indicator_name in selected_indicators]
            strategy_params[param['id']] = selected_indicators

        elif direction_options_buy is not None:
             direction_name=st.selectbox(param['placeholder'], list(direction_buy.keys()))
             direction=direction_options_buy.get(direction_name)
             strategy_params[param['id']] = direction
        elif direction_options_sell is not None:
             direction_name_sell=st.selectbox(param['placeholder'], list(direction_sell.keys()))
             direction_sell=direction_options_sell.get(direction_name_sell)
             strategy_params[param['id']] = direction_sell
        else:
           strategy_params[param['id']] = param.get('value', None)
           min_value = min_value if min_value is not None else max_value
           strategy_params[param['id']] = (min_value,max_value)


    #ipdb.set_trace()

    # Affichez les paramètres de la stratégie
#     strategy_params = {}
#     for param in strategy_parameters_specific:
#         min_value = param.get('min_value', None)
#         max_value = param.get('max_value', None)
#         model_options = param.get('model', None)
#         indicator_options = param.get('indicator', None)

#         if min_value is not None and max_value is not None and min_value != max_value:
#             min_val, max_val = st.slider(
#             param['placeholder'],
#             min_value=min_value,
#             max_value=max_value,
#             value=(min_value, max_value)
#  )
#             strategy_params[param['id']] = (min_val, max_val)
#         else:
#         # Gérez le cas où min_value est égal à max_value (valeur fixe)
#            min_value = min_value if min_value is not None else max_value
#            strategy_params[param['id']] = (min_value,max_value)



# # Créez une liste déroulante pour sélectionner le modèle
#     selected_model_name = st.selectbox('Sélectionnez un modèle', list(dm1ml_model_options.keys()))
#     selected_model = dm1ml_model_options.get(selected_model_name, pms.PMOLS)  # Par défaut, utilisez PMOLS si le modèle n'est pas trouvé

# # Créez une liste déroulante pour sélectionner les indicateurs (permettant plusieurs sélections)
#     selected_indicators = st.multiselect('Sélectionnez les indicateurs', list(dm1ml_indicator_options.keys()), ['RSI', 'MFI'])
#     selected_indicators = [dm1ml_indicator_options.get(indicator_name, mid.RSI()) for indicator_name in selected_indicators]

# # Ajoutez des widgets pour les autres paramètres spécifiques à 'DM1ML'
#     sell_threshold = st.slider('Seuil de vente', min_value=0.0, max_value=0.06, step=0.01, value=0.0)
#     buy_threshold = st.slider('Seuil dachat', min_value=0.0, max_value=0.06, step=0.01, value=0.0)
#     returns_horizon = st.number_input('Horizon des rendements', min_value=1, max_value=30, value=1)
#     rsi_window = st.slider('Fenêtre RSI', min_value=1, max_value=100, value=14)
#     mfi_window = st.slider('Fenêtre MFI', min_value=1, max_value=100, value=14) 
#     mom_period = st.slider('Période de MOM', min_value=0, max_value=100, value=14)

# # Créez une instance de la stratégie 'DM1ML' avec les paramètres spécifiés
#     strategy_instance =sml.DM1ML(
#     model=selected_model,
#     indicators=selected_indicators,
#     sell_threshold=sell_threshold,
#     buy_threshold=buy_threshold,
#     returns_horizon=returns_horizon,
#     rsi_window=rsi_window,
#     mfi_window=mfi_window,
#     mom_period=mom_period
# )
    
    # Bouton pour lancer les résultats
    if st.button("Submit"):
        st.session_state.results_df = None  # Réinitialiser les résultats

        st.write(f"Analyse en cours pour le symbole {selected_symbol} de {start_date} à {end_date} en {selected_timeframe} ")

        # Utilisez votre fonction fetch_ohlcv ici pour obtenir les données OHLCV
        ohlcv_df = fetch_ohlcv(selected_symbol, selected_timeframe, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'), selected_exchange_name)
        param_ranges = []
        for param_values in strategy_params.values():
            if isinstance(param_values, tuple) and len(param_values) == 3:
                min_value, max_value, step = param_values
                if min_value == max_value:
                  fixed_value = [min_value]  # Ajoutez la valeur fixe comme une liste
                  param_ranges.append(fixed_value)
                  continue  # Passez à l'itération suivante sans créer de param_range
                if isinstance(min_value, int) and isinstance(max_value, int):
                    if 'step' in param_values:
                        step = param_values['step']
                    param_range = list(range(min_value, max_value + 1,step)) if step is not None else list(range(min_value, max_value + 1))

                elif isinstance(min_value, float) and isinstance(max_value, float):
                    if 'step' in param_values:
                        step = param_values['step']
                    param_range = [round(x, 3) for x in np.arange(min_value, max_value, step)] if step is not None else [round(x, 3) for x in np.arange(min_value, max_value + 0.01, 0.01)]
                else:
                     pass

                param_ranges.append(param_range) # rajouter pour DM1ML a voir 
                #ipdb.set_trace()
            elif isinstance(param_values, type):
                 # Si le paramètre est une classe (modèle)
                     param_ranges.append([param_values])
            elif isinstance(param_values, list) and all(isinstance(val, type) for val in param_values):
        # Si le paramètre est une liste de classes (indicateurs)
                param_ranges.append(param_values)
            else:
        # Autres cas (valeur unique)
               param_ranges.append([param_values])

        #param_ranges = [range(param_values[0], param_values[1] + 1) for param_values in strategy_params.values()]
        parameter_grid = list(itertools.product(*param_ranges))
        #ipdb.set_trace()
        results = []
        for params in tqdm.tqdm(parameter_grid, desc="Parametric Study in Progress"):
            st.session_state.setdefault("results_df", None)  # Initialiser results_df si ce n'est pas déjà fait

            strategy_params_specific = {}
    
            for param_name, param_value in zip(strategy_params.keys(), params):
                strategy_params_specific[param_name] = param_value

            # Mettez à jour le dictionnaire avec les paramètres actuels de la boucle
            for i, param_name in enumerate(strategy_params_specific):
                strategy_params_specific[param_name] = params[i]

            # Sélectionnez la classe ou la fonction de stratégie en fonction du nom
            strategy_class_or_function = strategy_dict[selected_strategy]
            if selected_strategy=='DM1ML':
              # Extrait les indicateurs et les paramètres de fenêtre
                model=strategy_params_specific.pop('model',None)
                indicators = strategy_params_specific.pop('indicators', [])
                rsi_window = strategy_params_specific.pop('rsi_window', None)
                mfi_window = strategy_params_specific.pop('mfi_window', None)
                mom_period = strategy_params_specific.pop('mom_period', None)
                returns=strategy_params_specific.pop('returns_horizon',None)
                # Instanciez ou appelez la stratégie avec les indicateurs instanciés et les autres paramètres
                strategy_instance = strategy_class_or_function(
                pm=model(
                features=[mid.RSI(window=rsi_window),mid.MFI(length=mfi_window),mid.MOM(period_mom=mom_period)], returns_horizon=returns
                ),**strategy_params_specific)
                strategy_instance.fit(ohlcv_df)

            else:

                strategy_instance = strategy_class_or_function(**strategy_params_specific)
            # Exécutez le backtest
            ohlcv_indics_df = ohlcv_df.copy()
            #ipdb.set_trace()
            bt = btu.Backtest(ohlcv_indics_df, transaction_cost=maker_fee, var_buy_on='high', var_sell_on='low')
            bt_results = bt.backtest_strategy_long(strategy_instance)

            # Évaluez les résultats
            bt_eval_indic, bt_eval_raw = bt.backtest_eval()

            # Calculez la performance
            performance = bt_eval_indic["net_ret_strat"] + 1
            # Calculez le nombre de transactions
            nombre_transactions = len(bt_results['orders_df'])
            # Calculez le temps intra-trades moyen
            temps_intra_trades_mean = bt_eval_indic["trade_duration_mean"]

            # Calculez le temps inter-trades moyen
            temps_inter_trades_mean = bt_eval_indic["inter_trade_duration_mean"]

            # Stockez les résultats avec les paramètres pour analyse ultérieure
            results_row = list(params) + [performance, nombre_transactions, temps_intra_trades_mean, temps_inter_trades_mean]
            results.append(results_row)
        # Convertissez les résultats en DataFrame
        results_df = pd.DataFrame(results, columns=[param['id'] for param in strategy_parameters[selected_strategy]] + ['Performance', 'Nombre_transactions', 'Temps_intra_trades_mean', 'Temps_inter_trades_mean'])
        # Stocker les résultats dans la session
        st.session_state.results_df = results_df
        st.session_state.ohlcv_df=ohlcv_df
        st.session_state.selected_strategy=selected_strategy
        st.session_state.strategy_params=strategy_params
        st.session_state.symbol=symbol
        st.session_state.start_date=start_date
        st.session_state.end_date=end_date
        if 'results_df' in st.session_state:
            # Obtenir les informations supplémentaires
            current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            strategy_name = selected_strategy
            parameters = strategy_params 
            database_name = 'BTC_USDT_5m' 
            time_fram=timeframes
            start=start_date
            end=end_date

            # Formater le nom de fichier
            ohlcv_start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            ohlcv_end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            ohlcv_filename= f"ohlcv_{selected_exchange_name}_{selected_symbol.replace('/', ':')}_{selected_timeframe}_{ohlcv_start_date_str}_{ohlcv_end_date_str}"
            # ATTENTION : il se peut que filename devienne trop long pour un nom de fichier
            # Si trop long mettre current_time à la place de strategy_params
            filename = f"Résultats_{strategy_name}_{current_time}__{ohlcv_filename}.csv"
            #if len(filename) > filename_limit:
            #    filename = f"Résultats_{current_time}_{strategy_params}__{ohlcv_filename}.csv"

             # Formater le nom de fichier
            #filename = f"Résultats_{strategy_name}_{database_name}_{current_time}.csv"

            # Chemin complet pour enregistrer le fichier
            #save_path = f"/home/abdel/Bureau/Etude_parametrique/{filename}"

             # Enregistrer le DataFrame en CSV dans le dossier spécifié
            #st.session_state.results_df.to_csv(save_path, index=False)

            # Créer un lien de téléchargement pour le fichier
            #href = f'<a href="file://{save_path}" download="{filename}">Télécharger les résultats</a>'
            #st.markdown(href, unsafe_allow_html=True)


        
    uploaded_file = st.file_uploader("Choisissez un fichier de résultats")
    if uploaded_file is not None:
       st.session_state.uploaded_file = uploaded_file

else:  # Onglet "Résultats"
    st.subheader("Résultats")
    
    if 'results_df' in st.session_state and st.session_state.results_df is not None:
        data_to_use = st.session_state.results_df
        st.write("data_to_use assigné à partir de results_df")
    elif 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
        data_to_use = pd.read_csv(st.session_state.uploaded_file)
        st.write("data_to_use assigné à partir de uploaded_file")
        ohlcv_filename = os.path.join("data", st.session_state.uploaded_file.name.split("__")[1] + ".bz2")
        st.session_state["ohlcv_df"] = pd.read_csv(ohlcv_filename)
    else:
        data_to_use = None
        st.write("data_to_use est None")


    if data_to_use is not None: #and 'ohlcv_df' in st.session_state and st.session_state.ohlcv_df is not None:
        col1, col2 = st.columns(2)        
        # Extraire les noms des paramètres à partir des colonnes du DataFrame
        param_columns = [col for col in data_to_use.columns if col not in  ['Performance','model','indicators','Nombre_transactions']]
        param=[param_columns[0],param_columns[1]]
        # Calcul de la performance moyenne en fonction des deux paramètres
        performance_moy = data_to_use.groupby(param)['Performance'].mean().reset_index()
        #if 'Nombre_transactions' not in data_to_use.columns:
        nombre_trade=data_to_use.groupby(param)['Nombre_transactions'].mean().reset_index()
        performance_moyenne=pd.concat([performance_moy,nombre_trade['Nombre_transactions']], axis=1)
    
        #print(data_to_use)
        with col1:
        # Créer une heatmap
            
            heatmap = go.Heatmap(
             x=performance_moyenne[param_columns[0]],
             y=performance_moyenne[param_columns[1]],
             z=performance_moyenne['Performance'],
             customdata=performance_moyenne['Nombre_transactions'],
             colorscale='Viridis',
             colorbar_title='Performance',
             hovertemplate=f"{param_columns[0]}: %{{x}}<br>{param_columns[1]}: %{{y}}<br>Performance moyenne: %{{z}}<br>Nombre de trades moyenne: %{{customdata}}",)

            layout = go.Layout(
            xaxis=dict(title=param_columns[0]),
            yaxis=dict(title=param_columns[1]),
            title=f'Performance vs. {param_columns[0]} and {param_columns[1]}',)

            fig = go.Figure(data=[heatmap], layout=layout)

        # Afficher la heatmap avec les tooltips
            st.plotly_chart(fig)
            
            
        with col2:
        # Créer une heatmap
            if param_columns[3] not in ['Temps_intra_trades_mean', 'Temps_inter_trades_mean', 'Performance', 'Nombre_transactions']:
               param=[param_columns[2],param_columns[3]]
            # Calcul de la performance moyenne en fonction des deux paramètres
               performance_moy = data_to_use.groupby(param)['Performance'].mean().reset_index()
               nombre_trade=data_to_use.groupby(param)['Nombre_transactions'].mean().reset_index()
               performance_moyenne=pd.concat([performance_moy,nombre_trade['Nombre_transactions']], axis=1)
               heatmap = go.Heatmap(
               x=performance_moyenne[param_columns[2]],
               y=performance_moyenne[param_columns[3]],
               z=performance_moyenne['Performance'],
               customdata=performance_moyenne['Nombre_transactions'],
               colorscale='Viridis',
               colorbar_title='Performance',
               hovertemplate=f"{param_columns[2]}: %{{x}}<br>{param_columns[3]}: %{{y}}<br>Performance moyenne: %{{z}}<br>Nombre de trades moyenne: %{{customdata}}",)

               layout = go.Layout(
               xaxis=dict(title=param_columns[2]),
               yaxis=dict(title=param_columns[3]),
               title=f'Performance vs. {param_columns[2]} and {param_columns[3]}',)
               fig = go.Figure(data=[heatmap], layout=layout)

        # Afficher la heatmap avec les tooltips
               st.plotly_chart(fig)
        
        if data_to_use['Temps_intra_trades_mean'].dtype == object:
             data_to_use['Temps_intra_trades_mean'] = pd.to_timedelta(data_to_use['Temps_intra_trades_mean'])
    
        with col1:
        # Boxplot du temps intra-trade
                fig_boxplot_intra = go.Figure()
                for param_value in data_to_use[param_columns[0]].unique():
                    subset = data_to_use[data_to_use[param_columns[0]] == param_value]
                    fig_boxplot_intra.add_trace(go.Box(y=subset['Temps_intra_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[0]}={param_value}'))
                fig_boxplot_intra.update_layout(xaxis_title=param_columns[0], yaxis_title='Temps Intra-Trade moyen en secondes', title='Boxplot du Temps Intra-Trade  en fonction de   '  +  f'{param_columns[0]}')
                st.plotly_chart(fig_boxplot_intra)

        with col2:
        # Boxplot du temps intra-trade
            
            fig_boxplot_intra = go.Figure()
            for param_value in data_to_use[param_columns[1]].unique():
                subset = data_to_use[data_to_use[param_columns[1]] == param_value]
                fig_boxplot_intra.add_trace(go.Box(y=subset['Temps_intra_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[1]}={param_value}'))
            fig_boxplot_intra.update_layout(xaxis_title=param_columns[1], yaxis_title='Temps Intra-Trade moyen en secondes', title='Boxplot du Temps Intra-Trade en fonction de   '  +  f'{param_columns[1]}')
            st.plotly_chart(fig_boxplot_intra)
        

        with col1:
        # Boxplot du temps intra-trade
           
            fig_boxplot_intra = go.Figure()
            for param_value in data_to_use[param_columns[2]].unique():
                subset = data_to_use[data_to_use[param_columns[2]] == param_value]
                fig_boxplot_intra.add_trace(go.Box(y=subset['Temps_intra_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[2]}={param_value}'))
            fig_boxplot_intra.update_layout(xaxis_title=param_columns[2], yaxis_title='Temps Intra-Trade moyen en secondes', title='Boxplot du Temps Intra-Trade  en fonction de   '  +  f'{param_columns[2]}')
            st.plotly_chart(fig_boxplot_intra)


        with col2:
        # Boxplot du temps intra-trade
            if param_columns[3] not in ['Temps_intra_trades_mean', 'Temps_inter_trades_mean', 'Performance', 'Nombre_transactions']:
                fig_boxplot_intra = go.Figure()
                for param_value in data_to_use[param_columns[3]].unique():
                    subset = data_to_use[data_to_use[param_columns[3]] == param_value]
                    fig_boxplot_intra.add_trace(go.Box(y=subset['Temps_intra_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[3]}={param_value}'))
                fig_boxplot_intra.update_layout(xaxis_title=param_columns[3], yaxis_title='Temps Intra-Trade moyen en secondes', title='Boxplot du Temps Intra-Trade  en fonction de   '  +  f'{param_columns[3]}')
                st.plotly_chart(fig_boxplot_intra)

        

        with col2:
        
        # Boxplot du temps inter-trade
            if data_to_use['Temps_inter_trades_mean'].dtype == object:
               data_to_use['Temps_inter_trades_mean'] = pd.to_timedelta(data_to_use['Temps_inter_trades_mean'])

            fig_boxplot_inter = go.Figure()
            for param_value in data_to_use[param_columns[0]].unique():
                subset =data_to_use[data_to_use[param_columns[0]] == param_value]
                fig_boxplot_inter.add_trace(go.Box(y=subset['Temps_inter_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[0]}={param_value}'))
            fig_boxplot_inter.update_layout(xaxis_title=param_columns[0], yaxis_title='Temps Inter-Trade moyen en secondes', title='Boxplot du Temps Inter-Trade  en fonction de  '  +  f'{param_columns[0]}')
            st.plotly_chart(fig_boxplot_inter)
        
        with col1:
            # Boxplot du temps inter-trade
            
            fig_boxplot_inter = go.Figure()
            for param_value in data_to_use[param_columns[1]].unique():
                subset = data_to_use[data_to_use[param_columns[1]] == param_value]
                fig_boxplot_inter.add_trace(go.Box(y=subset['Temps_inter_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[1]}={param_value}'))
            fig_boxplot_inter.update_layout(xaxis_title=param_columns[1], yaxis_title='Temps Inter-Trade moyen en secondes', title='Boxplot du Temps Inter-Trade en fonction de   '  +  f'{param_columns[1]}')
            st.plotly_chart(fig_boxplot_inter)

        

        with col2:
        
        # Boxplot du temps inter-trade
           
            fig_boxplot_inter = go.Figure()
            for param_value in data_to_use[param_columns[2]].unique():
                subset = data_to_use[data_to_use[param_columns[2]] == param_value]
                fig_boxplot_inter.add_trace(go.Box(y=subset['Temps_inter_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[2]}={param_value}'))
            fig_boxplot_inter.update_layout(xaxis_title=param_columns[2], yaxis_title='Temps Inter-Trade moyen en secondes', title='Boxplot du Temps Inter-Trade  en fonction de  '  +  f'{param_columns[2]}')
            st.plotly_chart(fig_boxplot_inter)
        
        with col1:
            # Boxplot du temps inter-trade
            if param_columns[3] not in ['Temps_intra_trades_mean', 'Temps_inter_trades_mean', 'Performance', 'Nombre_transactions']:
                fig_boxplot_inter = go.Figure()
                for param_value in data_to_use[param_columns[3]].unique():
                    subset = data_to_use[data_to_use[param_columns[3]] == param_value]
                    fig_boxplot_inter.add_trace(go.Box(y=subset['Temps_inter_trades_mean'].apply(lambda x: x.total_seconds()), name=f'{param_columns[3]}={param_value}'))
                fig_boxplot_inter.update_layout(xaxis_title=param_columns[3], yaxis_title='Temps Inter-Trade moyen en secondes', title='Boxplot du Temps Inter-Trade en fonction de   '  +  f'{param_columns[3]}')
                st.plotly_chart(fig_boxplot_inter)

      
        with col1:
        # Distribution du nombre de trades
            
            fig_hist_trades = go.Figure()
            for param_value in data_to_use[param_columns[0]].unique():
                subset = data_to_use[data_to_use[param_columns[0]] == param_value]
                fig_hist_trades.add_trace(go.Box(y=subset['Nombre_transactions'], name=f'{param_columns[0]}={param_value}'))
            fig_hist_trades.update_layout(xaxis_title='Nombre de trades', yaxis_title='Fréquence', title='Distribution du Nombre de Trades en fonction de   '  +  f'{param_columns[0]}')
            st.plotly_chart(fig_hist_trades)

        with col2:
        # Distribution du nombre de trades
            
            fig_hist_trades = go.Figure()
            for param_value in data_to_use[param_columns[1]].unique():
                subset = data_to_use[data_to_use[param_columns[1]] == param_value]
                fig_hist_trades.add_trace(go.Box(y=subset['Nombre_transactions'], name=f'{param_columns[1]}={param_value}'))
            fig_hist_trades.update_layout(xaxis_title='Nombre de trades', yaxis_title='Fréquence', title='Distribution du Nombre de Trades en fonction de   '    +  f'{param_columns[1]}')
            st.plotly_chart(fig_hist_trades)

      

        with col1:
        # Distribution du nombre de trades
           
            fig_hist_trades = go.Figure()
            for param_value in data_to_use[param_columns[2]].unique():
                subset =data_to_use[data_to_use[param_columns[2]] == param_value]
                fig_hist_trades.add_trace(go.Box(y=subset['Nombre_transactions'], name=f'{param_columns[2]}={param_value}'))
            fig_hist_trades.update_layout(xaxis_title='Nombre de trades', yaxis_title='Fréquence', title='Distribution du Nombre de Trades en fonction de   '   +  f'{param_columns[2]}')
            st.plotly_chart(fig_hist_trades)

        with col2:
        # Distribution du nombre de trades
            if param_columns[3] not in ['Temps_intra_trades_mean', 'Temps_inter_trades_mean', 'Performance', 'Nombre_transactions']:
                fig_hist_trades = go.Figure()
                for param_value in data_to_use[param_columns[3]].unique():
                    subset = data_to_use[data_to_use[param_columns[3]] == param_value]
                    fig_hist_trades.add_trace(go.Box(y=subset['Nombre_transactions'], name=f'{param_columns[3]}={param_value}'))
                fig_hist_trades.update_layout(xaxis_title='Nombre de trades', yaxis_title='Fréquence', title='Distribution du Nombre de Trades en fonction de  '  +  f'{param_columns[3]}')
                st.plotly_chart(fig_hist_trades)

        with col1:
           st.markdown("**Dataframe résulats d'etude paramétrique**")
           param_columns = [col for col in data_to_use.columns if col not in  ['model','indicators','Temps_intra_trades_mean', 'Temps_inter_trades_mean']]
           # Triez le DataFrame par colonne de performance (par exemple, "Performance")
           sorted_results_df = data_to_use.sort_values(by='Performance', ascending=False)
           filtered_df = sorted_results_df[param_columns]
           df=pd.DataFrame(filtered_df)
           st.write(df.head(50))
        
        with col1:

            # Utile ? and st.session_state.ohlcv_df is not None:
            if 'ohlcv_df' in st.session_state:
                # Calculez la performance cumulative du "buy and hold"
                st.session_state.ohlcv_df['Buy and Hold'] = (st.session_state.ohlcv_df['close'] /st.session_state.ohlcv_df['close'].iloc[0])
                # Obtenez la dernière valeur de la performance du "buy and hold"
                last_value = st.session_state.ohlcv_df['Buy and Hold'].iloc[-1]
                # Déterminez la couleur de la flèche en fonction de la performance
                arrow_color = 'green' if last_value < 1 else 'red'
                # Affichez la performance avec une flèche en gras
                st.write(f"Performance du Buy and Hold : ", f"<span style='color:{arrow_color}; font-weight:bold;'>{last_value} {'↑' if last_value > 1 else '↓'}</span>", unsafe_allow_html=True)
#           else: #/home/abdel/mosaic/ohlcv_binance_BTC:USDT_5m_2021-03-31 00:00:00 00:00:00_2021-07-31 00:00:00 00:00:00.csv.bz2
#                
#                ohlcv_df=pd.read_csv("/home/abdel/mosaic/ohlcv_binance_BTC:USDT_5m_2018-01-01 00:00:00 00:00:00_2019-01-01 00:00:00 00:00:00.csv.bz2")
#                ohlcv_df['Buy and Hold']=ohlcv_df['close'] /ohlcv_df['close'].iloc[0]
#                last_value = ohlcv_df['Buy and Hold'].iloc[-1]
#                arrow_color = 'green' if last_value < 1 else 'red'
#                st.write(f"Performance du Buy and Hold : ", f"<span style='color:{arrow_color}; font-weight:bold;'>{last_value} {'↑' if last_value > 1 else '↓'}</span>", unsafe_allow_html=True)

        # Créez un graphique pour afficher la performance du "buy and hold"
        with col2:
            #st.line_chart(st.session_state.ohlcv_df['close'])
           # Créez un graphique de chandeliers (candlestick chart) avec Plotly
            # fig = go.Figure(data=[go.Candlestick(x=st.session_state.ohlcv_df.index,
            #                              open=st.session_state.ohlcv_df['open'],
            #                              high=st.session_state.ohlcv_df['high'],
            #                              low=st.session_state.ohlcv_df['low'],
            #                              close=st.session_state.ohlcv_df['close'])])

            # # Personnalisez le titre et les étiquettes des axes
            # fig.update_layout(title='Graphique de Chandeliers (Candlestick Chart)',
            #           xaxis_title='Date',
            #           yaxis_title='Prix')

            # # Affichez le graphique de chandeliers
            # st.plotly_chart(fig)
            if 'ohlcv_df' in st.session_state and st.session_state.ohlcv_df is not None:

                st.write("Evolution de prix en fonction du temps :")
                st.line_chart(st.session_state.ohlcv_df['close'])
            else :
                st.write("Evolution de prix en fonction du temps :")
                st.line_chart(st.session_state.ohlcv_df['close'])
    
    else:
        st.write("Aucun résultat disponible. Veuillez d'abord lancer l'analyse depuis l'onglet de configuration.")
