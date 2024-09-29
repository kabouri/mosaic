import sys
sys.path.insert(0, '/home/abdel/Bureau/new_project/mosaic')
import mosaic   
import mosaic.decision_model.dm_ta as sta 
import mosaic.decision_model.dm_base as sml
import mosaic.indicator as mid
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401import pandas as pd
import pandas as pd
import dash
from datetime import datetime
from dash.dependencies import Input, Output
import plotly.io as pio
import ccxt
import numpy as np
from dash.dash_table.Format import Group
from dash import dash_table
from dash.dash_table import DataTable
from plotly.graph_objs import Box
import mosaic
import importlib
import os
import dash
import dash_bootstrap_components as dbc
import sys
from scipy import stats
import backtest_class as btu
import hashlib
import json
from dash import Dash, dcc, html, State
import dash
from dash import dcc
from dash import html
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
import importlib
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

# Initialisation de Binance
exchange = ccxt.binance()
kraken = ccxt.kraken()
bitfinex = ccxt.bitfinex()





exchange=ExchangeCCXT(name='binance')
exchange.connect()










# utiliser la classe fetch_ohlcv de mosaic 

def fetch_ohlcv(symbol, timeframe='1h', start_date=None, end_date=None,  exchange_name='binance'):
    # Convertit les dates en timestamp UNIX (en millisecondes)


    exchange=ExchangeCCXT(name=exchange_name)
    exchange.connect()
    df=exchange.get_historic_ohlcv(
                    date_start=start_date+" 00:00:00",
                    date_end=end_date+" 00:00:00",
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

symbol = 'GOLD/USDT'
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
    'DojiStrategy':sta.DojiStrategy,
    'DM1ML':sml.DM1ML,
    'DM2ML':sml.DM2ML,
    
    
}

strategy_indicator_mapping = {
    'RSIStrategy': mid.RSI,
    'BBStrategy': mid.BBands,
    'MOMStrategy': mid.MOM,
    'STOCHStrategy':mid.STOC,
    'MFIStrategy': mid.mfi,
    'MACDStrategy':mid.MACD,
    'ATRStrategy': mid.ATR,
    'ADXStrategy':mid.ADX,
    'IchimokuStrategy':mid.Ichimoku,
    'DonchianChannelStrategy':mid.DonchianChannel,
     'FibonacciRetracementStrategy':mid.FibonacciRetracement,
     'MACRossoverStrategy':mid.MA,
     'HAMMERStrategy':mid.Hammer,
     'MACD_SMA_Strategy':[mid.MACD,mid.MA],
     'RSIDivergenceStrategy':mid.RSI,
     'BreakoutStrategy':mid.BBands,
     'MACD_RSIStrategy':[mid.RSI,mid.MACD],
     'MACDDivergenceStrategy':mid.MACD,
     'DojiStrategy':mid.Doji,
     'DM1ML': [mid.RSI,mid.MFI,mid.MOM],  # Pas d'indicateur spécifique pour DM1ML
     'DM2ML': None,  # Pas d'indicateur spécifique pour DM2ML
   
     }


strategy_parameters = {
        'RSIStrategy': [
        {'id': 'buy-level-input', 'type': 'number', 'placeholder': 'Buy Level', 'min': 0, 'max': 100, 'value': 30},
        {'id': 'sell-level-input', 'type': 'number', 'placeholder': 'Sell Level', 'min': 0, 'max': 100, 'value': 70},
        {'id': 'window-input', 'type': 'number', 'placeholder': 'RSI Window', 'min': 1, 'max': 100, 'value': 14}, ],
        'MFIStrategy': [
        {'id': 'buy-level-input', 'type': 'number', 'placeholder': 'Buy Level', 'min': 0, 'max': 100, 'value': 30},
        {'id': 'sell-level-input', 'type': 'number', 'placeholder': 'Sell Level', 'min': 0, 'max': 100, 'value': 70},
        {'id': 'length-mfi-input', 'type': 'number', 'placeholder': 'MFI Window', 'min': 1, 'max': 100, 'value': 14}, ],
       'BBStrategy': [
        {'id': 'std-input', 'type': 'number', 'placeholder': 'BB std', 'min': 0, 'max': 20, 'value': 2},
        {'id': 'length-bb-input', 'type': 'number', 'placeholder': 'BB Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'ddof-input', 'type': 'number', 'placeholder': 'BB ddof', 'min': 0, 'max': 0, 'value': 0}, ],
        'MOMStrategy': [
        {'id': 'period-input', 'type': 'number', 'placeholder': 'period mom', 'min': 0, 'max': 100, 'value': 14},
        {'id': 'threshold-input', 'type': 'number', 'placeholder': 'mom threshold', 'min': 0, 'max': 10, 'value': 0}, ],
       'MACRossoverStrategy': [
        {'id': 'short_window-input', 'type': 'number', 'placeholder': 'sma period', 'min': 0, 'max': 300, 'value': 10},
        {'id': 'long_window-input', 'type': 'number', 'placeholder': 'sma period', 'min': 0, 'max': 100, 'value': 20},],

        'STOCHStrategy': [
        {'id': 'buy-level-input', 'type': 'number', 'placeholder': 'Buy Level', 'min': 0, 'max': 100, 'value': 30},
        {'id': 'sell-level-input', 'type': 'number', 'placeholder': 'Sell Level', 'min': 0, 'max': 100, 'value': 70},
        {'id': 'short-window-stoch-input', 'type': 'number', 'placeholder': 'window stoch short', 'min': 0, 'max': 100, 'value': 3},
        {'id': 'long-window-stoch-input', 'type': 'number', 'placeholder': 'window stoch long', 'min': 0, 'max': 100, 'value': 14},
        {'id': 'smoothk-window-stoch-input', 'type': 'number', 'placeholder': 'smoothk stoch ', 'min': 3, 'max': 3, 'value': 3},],
    
        'MACDStrategy': [
        {'id': 'level-input', 'type': 'number', 'placeholder': ' Level', 'min': -10, 'max': 10,'step': 0.01, 'value': 0},
        {'id': 'fast-input', 'type': 'number', 'placeholder': 'fast window', 'min': 5, 'max': 100, 'value': 12},
        {'id': 'slow-input', 'type': 'number', 'placeholder': 'slow window', 'min': 3, 'max': 100, 'value': 26},
        {'id': 'signal-input', 'type': 'number', 'placeholder': 'signal window', 'min': 2, 'max': 100, 'value': 9},],
       
        'MACD_RSIStrategy': [
        {'id': 'fast-input', 'type': 'number', 'placeholder': 'fast window', 'min': 5, 'max': 100, 'value': 12},
        {'id': 'slow-input', 'type': 'number', 'placeholder': 'slow window', 'min': 3, 'max': 100, 'value': 26},
        {'id': 'signal-input', 'type': 'number', 'placeholder': 'signal window', 'min': 2, 'max': 100, 'value': 9},
        {'id': 'buy-level-input', 'type': 'number', 'placeholder': 'Buy Level', 'min': 0, 'max': 100, 'value': 30},
        {'id': 'sell-level-input', 'type': 'number', 'placeholder': 'Sell Level', 'min': 0, 'max': 100, 'value': 70},
        {'id': 'window-input', 'type': 'number', 'placeholder': 'RSI Window', 'min': 1, 'max': 100, 'value': 14}, ],
        
        
      
        'ATRStrategy': [
        {'id': 'threshold_atr-input', 'type': 'number', 'placeholder': 'threshold_atr', 'min': 0.01, 'max': 0.25,'step': 0.01, 'value': 0.1},
        {'id': 'period_atr-input', 'type': 'number', 'placeholder': 'period_atr', 'min': 5, 'max': 100, 'value': 14},],
       
    
        'HAMMERStrategy': [
        {'id': 'window-input', 'type': 'number', 'placeholder': ' window', 'min': 2, 'max': 100,'step': 1, 'value': 14},
        {'id': 'beta-input', 'type': 'number', 'placeholder': 'beta hammer', 'min': 1.5, 'max': 150, 'value': 2},
        {'id': 'alpha-input', 'type': 'number', 'placeholder': 'alpha hammer', 'min': 0.0, 'max': 0.9, 'value': 0.1},
        {'id': 'profit_threshold-input', 'type': 'number', 'placeholder': 'profit_threshold', 'min': 0, 'value': 0.03},
         {'id': 'stop_loss_threshold-input', 'type': 'number', 'placeholder': 'stop_loss_threshold', 'value': -0.01},

        
        ],
     
        'BreakoutStrategy': [
        {'id': 'window-input', 'type': 'number', 'placeholder': ' window', 'min': 2, 'max': 100,'step': 1, 'value': 14},
        {'id': 'std-input', 'type': 'number', 'placeholder': 'BB std', 'min': 0, 'max': 20, 'value': 2},
        {'id': 'length-bb-input', 'type': 'number', 'placeholder': 'BB Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'ddof-input', 'type': 'number', 'placeholder': 'BB ddof', 'min': 0, 'max': 0, 'value': 0}, ],
     
        'ParabolicSARStrategy': [
        {'id': 'acceleration-input', 'type': 'number', 'placeholder': ' acceleration', 'min': 0.01, 'max': 0.06,'step': 0.01, 'value': 0.02},
        {'id': 'maximum-input', 'type': 'number', 'placeholder': 'maximum', 'min': 0.1, 'max': 0.6, 'step': 0.1,'value': 0.2},],
     
        'RSIDivergenceStrategy': [
        {'id': 'window-input', 'type': 'number', 'placeholder': 'RSI Window', 'min': 1, 'max': 100, 'value': 14},],
        
        'MACDDivergenceStrategy': [
        {'id': 'fast-input', 'type': 'number', 'placeholder': 'fast window', 'min': 5, 'max': 100, 'value': 12},
        {'id': 'slow-input', 'type': 'number', 'placeholder': 'slow window', 'min': 3, 'max': 100, 'value': 26},
        {'id': 'signal-input', 'type': 'number', 'placeholder': 'signal window', 'min': 2, 'max': 100, 'value': 9},],
        
        'FibonacciRetracementStrategy': [
        {'id': 'level_A-input', 'type': 'number', 'placeholder': 'level_A ', 'min': 0.1, 'max': 0.8,'step': 0.12  , 'value': 0.382},
        {'id': 'level_B-input', 'type': 'number', 'placeholder': 'level_B ', 'min': 0.1, 'max': 0.82,'step': 0.12  ,'value': 0.5},
        {'id': 'level_C-input', 'type': 'number', 'placeholder': 'level_C ', 'min': 0.1, 'max': 0.8,'step':0.12, 'value': 0.618}, ],
        
        'ADXStrategy': [
        {'id': 'buy-level-input', 'type': 'number', 'placeholder': 'Buy Level', 'min': 0, 'max': 100, 'value': 25},
        {'id': 'sell-level-input', 'type': 'number', 'placeholder': 'Sell Level', 'min': 0, 'max': 100, 'value': 20},
        {'id': 'window-input', 'type': 'number', 'placeholder': 'adx Window', 'min': 1, 'max': 100, 'value': 14},],
        
        'IchimokuStrategy': [
        {'id': 'tenkan_window-input', 'type': 'number', 'placeholder': 'tenkan_window', 'min': 0, 'max': 200, 'value': 9},
        {'id': 'kijun_window-input', 'type': 'number', 'placeholder': 'kijun_window', 'min': 0, 'max': 200, 'value': 26},
        {'id': 'senkou_span_b_window-input', 'type': 'number', 'placeholder': 'senkou_span_b', 'min': 1, 'max': 200, 'value': 52},
        {'id': 'displacement-input', 'type': 'number', 'placeholder': 'displacement', 'min': 1, 'max': 200, 'value': 26},],
        
        'DonchianChannelStrategy': [
        {'id': 'window-Donchianchanel-input', 'type': 'number', 'placeholder': 'window', 'min': 0, 'max': 300, 'value': 10}, ],
        
        
        'KeltnerChannelStrategy': [
        {'id': 'window-input', 'type': 'number', 'placeholder': 'window', 'min': 1, 'max':300, 'value': 20},
        {'id': 'multiplier-input', 'type': 'number', 'placeholder': 'multiplier', 'min': 0.1, 'max': 10,'step':0.1, 'value': 2.0},],
       
        'MACD_SMA_Strategy': [
        {'id': 'fast-input', 'type': 'number', 'placeholder': 'fast window', 'min': 5, 'max': 100, 'value': 12},
        {'id': 'slow-input', 'type': 'number', 'placeholder': 'slow window', 'min': 3, 'max': 100, 'value': 26},
        {'id': 'signal-input', 'type': 'number', 'placeholder': 'signal window', 'min': 2, 'max': 100, 'value': 9},
        {'id': 'short_window-input', 'type': 'number', 'placeholder': 'sma period', 'min': 0, 'max': 300, 'value': 10},
        {'id': 'long_window-input', 'type': 'number', 'placeholder': 'sma period', 'min': 0, 'max': 100, 'value': 20},],
        
       'HoffmanIRBStrategy': [
        {'id': 'window-input', 'type': 'number', 'placeholder': 'window', 'min': 1, 'max':300, 'value': 20},],
        
        'KalmanMeanReversionStrategy': [
       {'id': 'initial_state', 'type': 'number', 'placeholder': 'Initial State', 'value': 0},
       {'id': 'observation_covariance', 'type': 'number', 'placeholder': 'Observation Covariance', 'min': 0.001, 'max': 10, 'value': 1},
       {'id': 'transition_covariance', 'type': 'number', 'placeholder': 'Transition Covariance', 'min': 0.001, 'max': 10, 'value': 1},
       {'id': 'transition_matrices', 'type': 'number', 'placeholder': 'Transition Matrices', 'min': 0.001, 'max': 2, 'value': 1},],
       
               
       'DojiStrategy': [
        {'id': 'doji_threshold_ratio', 'type': 'number', 'placeholder': ' doji_threshold_ratio', 'min': 0.01, 'max':0.06, 'value': 0.03},
        {'id': 'risk_reward_ratio', 'type': 'number', 'placeholder': ' risk_reward_ratio', 'min': 1, 'max':4, 'value': 2},
        ],
        

       


        'DM1ML': [
        {'id': 'dm1ml-model-dropdown', 'type': 'text', 'placeholder': ' Model'},
        {'id': 'dm1ml-indicators-dropdown', 'type': 'text', 'placeholder': 'Indicators'},
        {'id': 'dm1ml-sell_threshold-input', 'type': 'number', 'placeholder': 'Sell Threshold', 'min': 0, 'max': 0.06,'step': 0.01, 'value': 0},
        {'id': 'dm1ml-buy_threshold-input', 'type': 'number', 'placeholder': 'buy Threshold', 'min': 0, 'max': 0.06,'step': 0.01, 'value': 0},
        {'id': 'dm1ml-returns_horizon-input', 'type': 'number', 'placeholder': 'returns horizon','value':1},
        {'id': 'window-input', 'type': 'number', 'placeholder': 'RSI Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'length-mfi-input', 'type': 'number', 'placeholder': 'MFI Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'period-input', 'type': 'number', 'placeholder': 'period mom', 'min': 0, 'max': 100, 'value': 14},],

        'DM2ML': [
        {'id': 'dm2ml-buy-model-dropdown', 'type': 'text', 'placeholder': ' Buy Model'},
        {'id': 'dm2ml-buy-indicators-dropdown', 'type': 'text', 'placeholder': 'Buy Indicators'},
        {'id': 'dm2ml-returns_horizon-input', 'type': 'number', 'placeholder': 'returns horizon','value':1},
        {'id': 'dm2ml-buy-threshold-input', 'type': 'number', 'placeholder': 'Buy Threshold', 'min': 0, 'max': 0.06,'step': 0.01, 'value': 0},
        {'id': 'dm2ml-sell-model-dropdown', 'type': 'text', 'placeholder': 'Sell Model'},
        {'id': 'dm2ml-sell-indicators-dropdown', 'type': 'text', 'placeholder': 'Sell Indicators'},
        {'id': 'dm2ml-sell-threshold-input', 'type': 'number', 'placeholder': 'Sell Threshold', 'min': 0, 'max': 0.06,'step': 0.01, 'value': 0},
         {'id': 'window-input', 'type': 'number', 'placeholder': 'RSI Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'length-mfi-input', 'type': 'number', 'placeholder': 'MFI Window', 'min': 1, 'max': 100, 'value': 14},
        {'id': 'period-input', 'type': 'number', 'placeholder': 'period mom', 'min': 0, 'max': 100, 'value': 14},
        {'id': 'buy-direction-input', 'type': 'text', 'placeholder': 'Buy Direction'},
        {'id': 'sell-direction-input', 'type': 'text', 'placeholder': 'Sell Direction'},

 
    ]}








param_mapping = {
    'buy-level-input': 'buy_level',
    'sell-level-input': 'sell_level',
    'window-input': 'window',
    'length-mfi-input':'length',
    'length-bb-input': 'length',
    'std-input': 'std',
    'ddof-input':'ddof',
    'period-input': 'period_mom',
    'threshold-input': 'threshold',
    'short_window-input': 'short_moving_average',
    'long_window-input': 'long_moving_average',
    'short-window-stoch-input' : 'window_long',
    'long-window-stoch-input' : 'window_short',
     'smoothk-window-stoch-input':'smooth_k',
     'level-input':'level',
     'fast-input':'fast',
     'slow-input':'slow',
     'signal-input':'signal',
     'threshold_atr-input':'threshold_atr',
     'period_atr-input':'period_atr',
     'ema_period-input' : 'ema_period',
     'beta-input': 'beta',
     'alpha-input' : 'alpha',
     'profit_threshold-input': 'profit_threshold',
     'stop_loss_threshold-input':'stop_loss_threshold',
     'window-input': 'window',
     'threshold_bk-input': 'threshold_bk',
     'acceleration-input':'acceleration',
     'maximum-input':'maximum',
     'level_A-input':'level_A',
     'level_B-input':'level_B',
     'level_C-input':'level_C',
     'tenkan_window-input':'tenkan_window',
     'kijun_window-input':'kijun_window',
     'senkou_span_b_window-input': 'senkou_span_b_window',
     'displacement-input': 'displacement',
     'window-Donchianchanel-input':'window',
     'multiplier-input':'multiplier',
    'dm1ml-model-dropdown': 'pm',
    'dm1ml-indicators-dropdown': 'features',
    'dm1ml-buy_threshold-input': 'buy_threshold',
    'dm1ml-sell_threshold-input': 'sell_threshold',
    'dm1ml-returns_horizon-input':'returns_horizon',
    'dm2ml-buy-model-dropdown': 'DM2ML',
    'dm2ml-buy-indicators-dropdown': 'features',
    'dm2ml-buy-threshold-input': 'buy_threshold',
    'dm2ml-sell-model-dropdown': 'DM2ML',
    'dm2ml-sell-indicators-dropdown': 'features',
    'dm2ml-sell-threshold-input': 'sell_threshold',
    'dm2ml-returns_horizon-input':'returns_horizon',
    'sell-direction-input' : 'direction',
    'buy-direction-input' : 'direction',
    'initial_state':'initial_state',
    'observation_covariance':'observation_covariance',
    'transition_covariance':'transition_covariance',
    'transition_matrices':'transition_matrices',
    'doji_threshold_ratio':'doji_threshold_ratio',
    'risk_reward_ratio':'risk_reward_ratio',

   
 }



available_exchanges = ['binance','coinex','kraken','bittrex']



########################################################## Création de l'application Dash et de ses composants:


#ohlcv_df = pd.read_csv("/home/abdel/mosaic/ohlcv_binance_BTC:FDUSD_1s_2023-09-12 00:00:00+02:00_2023-09-15 00:00:00+02:00.csv.bz2", index_col="datetime")

# dm=sml.DM2ML(
#     pm_buy=pms.PMLogit(returns_horizon=1,features=[mid.RSI(window=12),mid.MFI(length=10)],direction='up'),
#     pm_sell=pms.PMLogit(returns_horizon=1,features=[mid.RSI(window=12),mid.MFI(length=10)],direction='down'),
#     buy_threshold=0,
#     sell_threshold=0
# )


# dm.fit(ohlcv_df)
# print(dm.execute(ohlcv_df))



########################################################## Création de l'application Dash et de ses composants:


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True)

# Mise en page de l'onglet de configuration
config_tab_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Backtesting & Live Trading Assistant', className='display-4 mt-4 mb-5', style={
                'color': '#ef7b26',  # Couleur du titre
                'text-align': 'center',
                'font-size': '65px',
                'font-weight': 'bold',
                'text-shadow': '2px 2px 4px #000000'  # Ombre du texte
            })
        ], style={
            'border': '2px solid #ef7b26',  # Bordure orange
            'padding': '10px',
            'border-radius': '10px',
            'margin': '10px',
            'box-shadow': '5px 5px 10px #888888'  # Ombre autour de la boîte
        })
    ]),
    dcc.Loading(
        id="loading",
        type="cube",
        children=[
            html.Div(id='fee-info', style={'fontSize': 18, 'color': 'white'}),  # Couleur du texte
            html.Div(id='debug-output'),
            dcc.Dropdown(
                id='exchange-dropdown',
                options=[{'label': exchange, 'value': exchange} for exchange in available_exchanges],
                value='binance',
                style={'color': 'black'}  # Couleur du texte déroulant
            ),
            
            dcc.Dropdown(
                id='symbol-dropdown',
                options=[
                    {'label': 'BTC/USDT', 'value': 'BTC/USDT'},
                    {'label': 'ETH/USDT', 'value': 'ETH/USDT'},
                    {'label': "BTC/FDUSD", 'value': "BTC/FDUSD"},
                    {'label': 'GOLD/USDT', 'value': 'GOLD/USDT'},
                ],
                value='BTC/USDT',
                style={'color': 'black'}
            ),
            dcc.Dropdown(
                id='timeframe-dropdown',
                options=[
                    {'label': '1 hour', 'value': '1h'},
                    {'label': '1 day', 'value': '1d'},
                    {'label': '1 minute', 'value': '1m'},
                    {'label': '5 minutes', 'value': '5m'},
                    {'label': '3 minutes', 'value': '3m'},
                ],
                value='1h',
                style={'color': 'black'}
            ),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date='2018-01-01',
                end_date='2019-01-01',
                display_format='YYYY-MM-DD',
                style={'color': 'black'}
            ),

            dcc.DatePickerRange(
                id='date-picker-range_fit',
                start_date='2021-01-01',
                end_date='2021-05-01',
                display_format='YYYY-MM-DD',
                style={'color': 'black'}
            ),
            dcc.Dropdown(
                id='strategy-dropdown',
                options=[{'label': k, 'value': k} for k in strategy_dict.keys()],
                value='RSIStrategy',
                style={'color': 'black'}
            ),

            html.Label('Variable for Buy Orders:', style={'color': 'white'}),
            dcc.Dropdown(
                id='var-buy-dropdown',
                options=[
                    {'label': 'Close Price', 'value': 'close'},
                    {'label': 'Open Price', 'value': 'open'},
                    {'label': 'High Price', 'value': 'high'},
                    {'label': 'Low Price', 'value': 'low'},
                ],
                value='close',
                style={'color': 'black'}
            ),
            html.Label('Variable for Sell Orders:', style={'color': 'white'}),
            dcc.Dropdown(
                id='var-sell-dropdown',
                options=[
                    {'label': 'Close Price', 'value': 'close'},
                    {'label': 'Open Price', 'value': 'open'},
                    {'label': 'High Price', 'value': 'high'},
                    {'label': 'Low Price', 'value': 'low'},
                ],
                value='close',
                style={'color': 'black'}
            ),
            html.Label('Fees:', style={'color': 'white'}),
            dcc.RadioItems(
                id='fee-type',
                options=[
                    {'label': 'Maker', 'value': 'maker'},
                    {'label': 'Taker', 'value': 'taker'},
                    {'label': 'free', 'value': 0},
                ],
                value='maker',
                labelStyle={
                    'display': 'inline-block',
                    'margin-right': '20px',
                    'color': 'white',
                    'fontSize': 15,
                    'border': '2px solid white',
                    'border-radius': '10px',
                    'padding': '9px',
                    'cursor': 'pointer'
                }),
            html.Label('Paramètres of the selected strategy:', style={'color': 'white'}),
            html.Div(id='dynamic-inputs'),
            html.Button('Run the backtest', id='Run the backtest-button', style={'backgroundColor': 'red', 'color': 'white'}),

            html.Button('Start Live Trading', id='start-trading-button', n_clicks=0, style={'backgroundColor': 'green', 'color': 'white'}),
            html.Label('API Key:', style={'color': 'white'}),
            dcc.Input(id='api-key-input', type='text', placeholder='Enter API Key'),
            html.Label('API Secret:', style={'color': 'white'}),
            dcc.Input(id='api-secret-input', type='password', placeholder='Enter API Secret'),
            html.Div(id='trading-status', children='Trading Status: Not Started', style={'color': 'white'}),
        
        ]
    )
], fluid=True,style={'background-color': 'lightblue'})


row_stat=dbc.Row( [
    html.Div(id='output-graph1', style={'width': '25%', 'display': 'inline-block', 'backgroundColor': 'lightblue', 'padding': '20px'}),
    html.Div(id='output-graph2', style={'width': '25%', ' display': 'inline-block', 'backgroundColor': 'lightblue', 'padding': '20px'}),
    html.Div(id='output-graph3', style={'width': '25%', 'display': 'inline-block', 'backgroundColor': 'lightblue', 'padding': '20px'}),
    html.Div(id='output-graph4', style={'width': '25%', 'display': 'inline-block', 'backgroundColor': 'lightblue', 'padding': '20px'}),])

# Mise en page de l'onglet de résultats
results_tab_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Statistiques des stratégies', className='display-4 mt-4 mb-5', style={
                'color': '#ef7b26',
                'text-align': 'center',
                'font-size': '65px',
                'font-weight': 'bold',
                'text-shadow': '2px 2px 4px #000000'
            })
        ], style={
            'border': '2px solid #ef7b26',
            'padding': '10px',
            'border-radius': '10px',
            'margin': '10px',
            'box-shadow': '5px 5px 10px #888888'
        })
    ]),
    html.Div(id='output-container'),
    html.Div(id='output-graph', style={'width': '100%', 'backgroundColor': 'lightblue', 'padding': '20px'}),
    html.Div(id='output-graph5', style={'width': '100%', 'display': 'inline-block', 'backgroundColor': 'lightblue', 'padding': '20px'}),
    row_stat,
],fluid=True,style={'background-color': 'lightblue'})

# Créez la mise en page globale
app.layout = dbc.Container([
    dbc.Tabs([
        dbc.Tab(label="Configuration", children=config_tab_layout),
        dbc.Tab(label="Statistiques des stratégies", children=results_tab_layout),
    ],),
], fluid=True, style={'backgroundColor': '#ecf0f1'})  # Nouvelle couleur de fond globale

######################################################  Callbacks et logique de l'application  ###############################################

@app.callback(
    Output('dynamic-inputs', 'children'),
    Input('strategy-dropdown', 'value')
)

def update_input_fields(strategy_name):
    children = []
    for param in strategy_parameters.get(strategy_name, []):
        label = html.Label(param['placeholder'], style={
    'fontSize': '20px',  # taille de la police
    'color': 'white',    # couleur du texte
    'margin': '10px 0' ,
    'marginRight': '20px',
    'marginLeft': '20px'  # marge autour du label pour un meilleur espacement
}) 
        input_field = dcc.Input(**param,style={'width': '100px'})
        children.extend([label, input_field])  # Ajoutez le label puis le champ d'entrée à la liste des enfants
    #print(f"Input fields for {strategy_name}: {children}")
    return children


 
def instantiate_pm(pm_value, kwargs):
    rsi_window = kwargs.get('window-input', 14)  # Utilisez 14 comme valeur par défaut si non spécifiée
    mfi_window = kwargs.get('length-mfi-input', 14)  # Utilisez 14 comme valeur par défaut si non spécifiée
    mom_window = kwargs.get('period-input', 14)  # Utilisez 14 comme valeur par défaut si non spécifiée

    rsi_indicator = mid.RSI(window=rsi_window)
    mfi_indicator = mid.MFI(window=mfi_window)
    mom_indicator = mid.MOM(window=mom_window)

    if pm_value == 'PMOLS':
        features = [rsi_indicator, mfi_indicator, mom_indicator]
        return pms.PMOLS(returns_horizon=kwargs.get('dm1ml-returns_horizon-input', 1), features=features)
    
    elif pm_value == 'DM2ML':
        buy_direction = kwargs.get('buy-direction-dropdown', 'up')  # Direction d'achat par défaut : 'up'
        sell_direction = kwargs.get('sell-direction-dropdown', 'down')  # Direction de vente par défaut : 'down'
        
        if buy_direction not in ['up', 'down'] or sell_direction not in ['up', 'down']:
            raise ValueError("Direction non valide. Utilisez 'up' ou 'down'.")
        
        features = [rsi_indicator]#, mfi_indicator, mom_indicator]
        pm_buy = pms.PMLogit(returns_horizon=kwargs.get('dm2ml-returns_horizon-input', 1), features=features, direction=buy_direction)
        pm_sell = pms.PMLogit(returns_horizon=kwargs.get('dm2ml-returns_horizon-input', 1), features=features, direction=sell_direction)

        buy_threshold = kwargs.get('dm2ml-buy-threshold-input')
        sell_threshold = kwargs.get('dm2ml-sell-threshold-input')


        buy_threshold = float(buy_threshold) if buy_threshold is not None else 0.0  # Vous pouvez définir une valeur par défaut autre que 0.0 si nécessaire
        sell_threshold = float(sell_threshold) if sell_threshold is not None else 0.0  # Idem ici
   
        
        return sml.DM2ML(pm_buy=pm_buy, pm_sell=pm_sell, buy_threshold=buy_threshold, sell_threshold=sell_threshold)


    else:
        raise ValueError(f"Modèle non supporté: {pm_value}")





@app.callback(
    [Output('output-container', 'children'),
    Output('output-graph', 'children'),
    Output('output-graph1', 'children'),
    Output('output-graph2', 'children'),
    Output('output-graph3', 'children'),
    Output('output-graph4', 'children'),
    Output('output-graph5', 'children'),
    Output('debug-output', 'children')],
    Input('Run the backtest-button', 'n_clicks'),
    State('strategy-dropdown', 'value'),
    State('dynamic-inputs', 'children'),
    State('symbol-dropdown', 'value'),
    State('timeframe-dropdown', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('date-picker-range_fit', 'start_date'),
    State('date-picker-range_fit', 'end_date'),
    State('exchange-dropdown', 'value'),
    State('var-buy-dropdown', 'value'),
    State('var-sell-dropdown', 'value'),
    State('fee-type', 'value'))



def update_output(n_clicks,strategy_name, input_fields,symbol, timeframe, start_date, end_date,start_date_fit,end_date_fit,exchange_name, var_buy, var_sell, fee_type):
    if n_clicks is None:
        return 'Enter strategy parameters and press Run the backtest.', None, None, None, None, None, None,None
    # Vérification des paramètres nécessaires
    if not strategy_name:
        return 'Strategy name is missing.',None, None, None, None, None, None,None
  
    relevant_param_ids = [param['id'] for param in strategy_parameters[strategy_name]]
    kwargs = {
    param_mapping[field['props']['id']]: field['props']['value'] 
    for field in input_fields 
    if 'id' in field['props'] and field['props']['id'] in relevant_param_ids}
    if not kwargs:
        return 'Strategy parameters not received. Please try again.', None, None, None, None, None, None,None,None
    
    
     # Si l'utilisateur a fourni un symbole, récupérez les données
    if symbol:

        ohlcv_df = fetch_ohlcv(symbol, timeframe, start_date, end_date,exchange_name)
        # Utilisez ohlcv_df comme votre base de données pour les stratégies
    else:
        return 'Please enter a symbol.', None, None, None, None, None, None, None
   
    # Logique de validation pour 'pm'
    if 'pm' in kwargs:
        try:
            kwargs['pm'] = instantiate_pm(kwargs['pm'],kwargs)
            ohlcv_df_fit = fetch_ohlcv(symbol, timeframe, start_date_fit, end_date_fit, exchange_name)
            kwargs['pm'].fit(ohlcv_df_fit)

        except ValueError as e:
            return f"Erreur: {e}", None, None, None, None, None, None, None
        
        # Logique de validation pour 'pm_buy'
    if 'DM2ML' in kwargs:
        try:
            kwargs['DM2ML'] = instantiate_pm(kwargs['DM2ML'], kwargs)
            ohlcv_df_fit = fetch_ohlcv(symbol, timeframe, start_date_fit, end_date_fit, exchange_name)
            kwargs['DM2ML'].fit(ohlcv_df_fit)
        except ValueError as e:
           return f"Erreur: {e}", None, None, None, None, None, None, None

    # Instanciation de la classe de stratégie
    try:
        StrategyClass = strategy_dict[strategy_name]
        strategy = StrategyClass(**kwargs)
    except Exception as e:
        return f"Erreur: {e}", None, None, None, None, None, None, None

    # Condition pour la stratégie DM1ML
     # Après avoir récupéré les données avec fetch_ohlcv
    if ohlcv_df.index.duplicated().any():
       ohlcv_df = ohlcv_df[~ohlcv_df.index.duplicated(keep='first')]
       
    # Exécutez le backtesting
    debug_text = f"Instanciating {strategy_name} with arguments: {kwargs}"
    maker_fee, taker_fee = get_trading_fees(exchange_name,symbol)
    fee_info = f"Fees for {symbol} on {exchange_name}: Maker fee - {maker_fee}, Taker fee - {taker_fee}"
    selected_fee = 0 if fee_type == 0 else (maker_fee if fee_type == 'maker' else taker_fee)
    bt=btu.Backtest(ohlcv_df,transaction_cost=selected_fee,var_buy_on=var_buy, var_sell_on=var_sell)
    bt_results = bt.backtest_strategy_long(strategy)
    bt_eval_indic, bt_eval_raw = bt.backtest_eval()
    
    
########################################################################### Creation de Tableau de statistiques ##########################################
    

    # Créez une représentation en chaîne des résultats pour l'afficher
    #results_df = pd.DataFrame(list(bt_eval_indic.items()),columns = ['Indicator','Value'])
    drawdown,duration = bt.drawdown_max()
    exposure = bt.calculate_exposure()
    profit_factor =round(bt.calculate_profit_factor(),4)
    max_draw={}
    max_draw[f"{strategy_name}"]=drawdown
    max_draw["Référence"]=btu.drawdown_max(((ohlcv_df["close"]/ohlcv_df["close"][0])-1))[0]
    max_draw_dict = sorted(max_draw.items(), key=lambda x: x[1])
    df = pd.DataFrame(max_draw_dict, columns=['Stratégie', 'Value'])
    fig3 = px.bar(df, x='Stratégie', y='Value',color='Stratégie')
    fig3.update_layout(
    title={  'text': 'Le drawdown maximum','y':0.97,  'x':0.5,  'xanchor': 'center', 'yanchor': 'top','font': {'color': '#C0C0C0'}}, title_font=dict( size=20,))
    
    
    
    
    returns = bt_results['orders_df']["returns"]
    # Calculer la moyenne et l'écart-type des rendements
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    if len(returns) > 0:
        x = np.linspace(mean_return - 4 * std_return, mean_return + 4 * std_return, 100)
        y = stats.norm.pdf(x, mean_return, std_return)    
    else:
        return 'La séquence "returns" est vide.'

    # Créer l'histogramme des rendements
    fig4 = go.Figure()
    fig4.add_trace(go.Histogram(x=returns, name='Rendements', nbinsx=50, opacity=0.75))

    # Ajouter la courbe de distribution normale
    fig4.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Distr normale',line=dict(color='rgba(255, 0, 0, 1)')))

    # Mettre à jour le layout
    fig4.update_layout(
    title={
        'text': 'Distribution des Rendements',
        'y': 0.97,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {'color': '#C0C0C0'}
    },
    title_font=dict(size=20),
    xaxis_title='Rendement',
    yaxis_title='Fréquence',
    bargap=0.2
)

    
    
    fee_info=html.Table([
    html.Thead([ html.Tr([html.Th("Fees for"), html.Th(f"{symbol} on {exchange_name}")])  ]),
    html.Tbody([
        html.Tr([html.Td("Maker fee:"), html.Td(maker_fee)]),
        html.Tr([html.Td("Taker fee:"), html.Td(taker_fee)])
    ])
], style={ 'border': '3px solid #C0C0C0','border-radius': '10px','margin': '10px'
})
    
    stats_table=[]
    stats_table.append({
            'Stratégie': strategy_name ,
            'Nombre de transactions': len(bt_results['orders_df']),
            'Performance brut': bt_eval_indic["gross_ret_strat"]+1,
            'Performance net': bt_eval_indic["net_ret_strat"]+1,
            'Volatilité': round(bt_eval_raw["ret_strat_t"].std(),4),
            'Max_drawdown_duration': str(duration),
            'Temps intra trades_mean': str(bt_eval_indic["trade_duration_mean"]),
            'Temps inter trades_mean': str(bt_eval_indic["inter_trade_duration_mean"]),
            'System Quality Number': round((bt_results['orders_df']["returns"].mean() / bt_eval_raw["ret_strat_t"].std())* np.sqrt(len(bt_results["orders_df"])), 4),
            'Exposure Time [%]': round(exposure,4),
            'Profit Factor': profit_factor
            #'Final_total_balance': round(bt_results["final_total_balance"])
        })
    stats_df=pd.DataFrame(stats_table)
    
    BH = pd.DataFrame({"Stratégie": 'Référence', 
                       "Nombre de transactions": [len(ohlcv_df)], 
                       "Performance brut": [round((ohlcv_df["close"][-1]/ohlcv_df["close"][0]), 4)],
                       'Performance net':[round((ohlcv_df["close"][-1]/ohlcv_df["close"][0])*((1 - selected_fee) ** 2),4)], 
                       "Volatilité": [round((ohlcv_df['close'].pct_change(1)).std(), 4)],
                       'Max_drawdown_duration': str(btu.drawdown_max((ohlcv_df["close"]/ohlcv_df["close"][0])-1)[1]),
                       "Temps intra trades_mean": [timeframe],
                       'Temps inter trades_mean': [timeframe],
                       'System Quality Number' : [round((bt_eval_raw["ret_asset_single"].mean()/bt_eval_raw["ret_asset_single"].std())*np.sqrt(len(ohlcv_df)),4)],
                       'Exposure Time [%]':[100]})
    
    results_df = pd.concat([BH, stats_df], ignore_index=True)
    results_table = html.Div([
    html.Div([
    ], style={
        'border': '2px solid #C0C0C0',
        'padding': '10px',
        'border-radius': '10px',
        'margin': '10px',
        'box-shadow': '5px 5px 10px #888888'
    }),    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in results_df.columns],
        data=results_df.to_dict('records'),
        style_data={
            'color': 'white', 
            'backgroundColor': 'black'
        },
        style_header={
            'color': 'white', 
            'backgroundColor': 'black'
        },
        style_table={
            'backgroundColor': 'black',
            'border': '20px solid lightblue',
            'overflowX': 'auto'
        },
        fill_width=True,
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current= 0,
        page_size= 10,
    )
])
    
###################################### Figures ###################################################################
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=bt_eval_raw['ret_strat_orders'].index, 
                         y=bt_eval_raw['ret_strat_orders'].values, 
                         mode='lines', 
                         name=strategy_name))

    fig.add_trace(go.Scatter(x=ohlcv_df.index, 
                         y=(ohlcv_df["close"]/ohlcv_df["close"][0])-1, 
                         mode='lines', 
                         name='Référence'))
    fig.update_layout(
    title={
        'text': 'Rendements cumulés de la stratégie sélectionnée et la stratégie référence de  '   f'{ohlcv_df.index[0]} au  {ohlcv_df.index[-1]}',
        'y':0.98,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top','font': {'color': '#C0C0C0'} },
    title_font=dict(
        size=20, ))
    
    bt_eval_raw["trade_duration_seconds"] = bt_eval_raw["trade_duration"].dt.total_seconds()
    fig1=px.box(bt_eval_raw["trade_duration_seconds"],color_discrete_sequence=['#FFFF00'])
    fig1.update_layout(
    title={
        'text': 'Le temps intra tarde',
        'y':0.97,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top','font': {'color': '#C0C0C0'}},
    title_font=dict(
        size=20,), yaxis_title="Durée en heures"
)  
    bt_results["orders_df"]["inter_trade_duration_seconds"]=bt_results["orders_df"]["inter_trade_duration"].dt.total_seconds()
    fig2=px.box(bt_results["orders_df"]["inter_trade_duration_seconds"],color_discrete_sequence=['#00FFFF'])
    fig2.update_layout(
    title={
        'text': 'Le temps inter trade',
        'y':0.97,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top','font': {'color': '#C0C0C0'}},
    title_font=dict(
        size=20,
    ),
    yaxis_title="Durée en heures"
)
    
    fig5 = go.Figure()
    layout={}
# Tracer le prix
    if strategy_name in strategy_indicator_mapping:
    # 2. Récupérez la classe ou les classes associées à cette stratégie
        indicator_classes = strategy_indicator_mapping[strategy_name]
        # Si ce n'est qu'une seule classe, convertissez-la en liste
        if not isinstance(indicator_classes, list):
           indicator_classes = [indicator_classes]
    fig5 = make_subplots(rows=len(indicator_classes) + 1, cols=1, shared_xaxes=True, vertical_spacing=0.03)

          
    fig5.add_trace(go.Candlestick(x=ohlcv_df.index,
                open=ohlcv_df['open'],
                high=ohlcv_df['high'],
                low=ohlcv_df['low'],
                close=ohlcv_df['close'],
                name='OHLC'),row=1, col=1)
     # Instanciez la stratégie et appelez sa méthode de tracé
    if strategy_name in strategy_indicator_mapping:
    # 2. Récupérez la classe ou les classes associées à cette stratégie
        indicator_classes = strategy_indicator_mapping[strategy_name]
        # Si ce n'est qu'une seule classe, convertissez-la en liste
        if not isinstance(indicator_classes, list):
           indicator_classes = [indicator_classes]
        row=2
        # 4. Parcourez la liste des classes
        for IndicatorClass in indicator_classes:
            indicator_instance = IndicatorClass(**kwargs)
            indicator_fig = indicator_instance.plotly(ohlcv_df)
        
        # Ajouter les données de l'indicateur à fig5
            for trace in indicator_fig.data:
                if trace.name != 'OHLC':
                   fig5.add_trace(trace,row=row,col=1)
   
            row+=1
# Ajoutez des marqueurs pour les signaux d'achat
    fig5.add_trace(go.Scatter(x=bt_results["orders_signal"][bt_results["orders_signal"] == 1].index, y=ohlcv_df.loc[bt_results["orders_signal"][bt_results["orders_signal"] == 1].index, var_buy], 
                         marker=dict(color='#00FF00', size=10, symbol='circle'), 
                         name='Achat', mode='markers'))

# Ajoutez des marqueurs pour les signaux de vente
    fig5.add_trace(go.Scatter(x=bt_results["orders_signal"][bt_results["orders_signal"]== 0].index, y=ohlcv_df.loc[bt_results["orders_signal"][bt_results["orders_signal"] == 0].index, var_sell], 
                        marker=dict(color='#FF0000', size=10, symbol='circle'),
                         name='Vente', mode='markers'))
    layout["xaxis_rangeslider_visible"] = False

    fig5.update_layout(  title={ 'text': 'Graphique des bougies avec signaux d’achat/vente et indicateur associé a la stratégie','y':0.97, 'x':0.5,   'xanchor': 'center', 'yanchor': 'top','font': {'color': '#C0C0C0'}},
                        xaxis_title='',**layout,
                        yaxis_title='Prix', title_font=dict( size=20, ))
    
    
############################################################################################################

    return results_table,dcc.Graph(figure=fig),dcc.Graph(figure=fig1),dcc.Graph(figure=fig2),dcc.Graph(figure=fig3),dcc.Graph(figure=fig4),dcc.Graph(figure=fig5),debug_text
if __name__ == '__main__':
    app.run_server(port=8040, debug=True)
    
 