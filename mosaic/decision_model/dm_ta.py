import pydantic
import typing
import pandas as pd
import numpy as np
import random
#import tqdm
from pykalman import KalmanFilter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..utils.data_management import HyperParams
#from ..trading.core import SignalBase
from ..core import ObjMOSAIC
from ..predict_model.pm_base import PredictModelBase
import mosaic.indicator as idu
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401

# PandasSeries = typing.TypeVar('pandas.core.frame.Series')
# PandasDataFrame = typing.TypeVar('pandas.core.frame.DataFrame')

        




class Strategy:
    def __init__(self, name):
        self.name = name

    def execute(self, ohlcv_df):
        raise NotImplementedError

class RSIStrategy(Strategy):
    def __init__(self, buy_level, sell_level, window):
        super().__init__("RSI Strategy")
        self.buy_level = buy_level
        self.sell_level = sell_level
        self.window = window
        self.indicator = idu.RSI(window=self.window, mode='wilder')

    def execute(self, ohlcv_df):
        # Compute RSI
        rsi_df = self.indicator.compute(ohlcv_df)
        rsi_df=rsi_df.shift(1)
        # Initialize order_value_s as a series filled with nan values
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        # Define buy and sell conditions
        idx_buy = rsi_df[f'RSI_{self.window}'] < self.buy_level
        idx_sell = rsi_df[f'RSI_{self.window}'] > self.sell_level
        # Update order_value_s with 1 for buying, 0 for selling, and leave as nan for holding
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0
        # Return the series of order values
        return order_value_s



class MFIStrategy(Strategy):
    def __init__(self, buy_level, sell_level, length):
        super().__init__("MFI Strategy")
        self.buy_level = buy_level
        self.sell_level = sell_level
        self.length =length
        self.indicator = idu.MFI(length=self.length)

    def execute(self, ohlcv_df):
        # Compute MFI
        mfi_df = self.indicator.compute(ohlcv_df)
        # Initialize order_value_s as a series filled with nan values
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        # Define buy and sell conditions
        idx_buy = mfi_df[f'MFI_{self.length}'] < self.buy_level
        idx_sell = mfi_df[f'MFI_{self.length}'] > self.sell_level
        # Update order_value_s with 1 for buying, 0 for selling, and leave as nan for holding
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0
        # Return the series of order values
        return order_value_s


class BBStrategy(Strategy):
    def __init__(self,length,std,ddof):
        super().__init__("mean rev Strategy")
        self.length = length
        #self.std = std
        self.ddof = ddof
        self.std = std if std is not None and float(std) >= 0 else 2.0
        self.indicator = idu.BBands(length=self.length,std=self.std,ddof=0)

    def execute(self, ohlcv_df):
        # Compute BB
        bb_df = self.indicator.compute(ohlcv_df)
        # Initialize order_value_s as a series filled with nan values
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        # Define buy and sell conditions
        if isinstance(self.std,float):
           idx_buy = bb_df[f'BBL_{self.length}_{float(self.std)}'] > ohlcv_df["close"] 
           idx_sell = bb_df[f'BBU_{self.length}_{float(self.std)}'] < ohlcv_df["close"]
        # Update order_value_s with 1 for buying, 0 for selling, and leave as nan for holding
        else:
           idx_buy = bb_df[f'BBL_{self.length}_{self.std}.{self.ddof}'] > ohlcv_df["close"] 
           idx_sell = bb_df[f'BBU_{self.length}_{self.std}.{self.ddof}'] < ohlcv_df["close"]
           
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0
        # Return the series of order values
        return order_value_s





class BreakoutStrategy(Strategy):
    def __init__(self,window,length,std,ddof):
        super().__init__("Breakout Strategy")
        self.window = window
        self.length = length
        #self.std = std
        self.ddof = ddof
        self.std = std if std is not None and float(std) >= 0 else 2.0
        self.indicator = idu.BBands(length=self.length,std=self.std,ddof=0)


    def execute(self, ohlcv_df):
        bb_df = self.indicator.compute(ohlcv_df)
        avg_volume = ohlcv_df['volume'].rolling(self.window).mean()
        lowerband=bb_df[f'BBL_{self.length}_{float(self.std)}']
        upperband=bb_df[f'BBU_{self.length}_{float(self.std)}']
        # Initialize a series to hold our order signals
        order_signals = pd.Series(index=ohlcv_df.index, dtype='float64')

        for i in range(1, len(ohlcv_df)):
            if (ohlcv_df['close'].iloc[i] > upperband.iloc[i] and
                ohlcv_df['volume'].iloc[i] > avg_volume.iloc[i] and
                ohlcv_df['close'].iloc[i-1] <= upperband.iloc[i-1]):
                order_signals.iloc[i] = 1  # Buy signal represented by 1
            elif (ohlcv_df['close'].iloc[i] < lowerband.iloc[i] and
                  ohlcv_df['volume'].iloc[i] > avg_volume.iloc[i] and
                  ohlcv_df['close'].iloc[i-1] >= lowerband.iloc[i-1]):
                order_signals.iloc[i] = 0  # Sell signal represented by 0

        return order_signals




class MOMStrategy(Strategy):
    def __init__(self, threshold,period_mom):
        super().__init__("MOM Strategy")
        self.threshold = threshold
        self.period_mom=period_mom
        self.indicator = idu.MOM(period_mom=self.period_mom)

    def execute(self, ohlcv_df):
        # Compute MFI
        mom_df = self.indicator.compute(ohlcv_df)
        # Initialize order_value_s as a series filled with nan values
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        # Define buy and sell conditions
        idx_buy = mom_df[f"MOM_{self.period_mom}"]> self.threshold
        idx_sell = mom_df[f"MOM_{self.period_mom}"]< self.threshold
        # Update order_value_s with 1 for buying, 0 for selling, and leave as nan for holding
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0
        # Return the series of order values
        return order_value_s





class SMAStrategy:
    def __init__(self, short_moving_average, long_moving_average):
        self.long_moving_average=long_moving_average
        self.short_moving_average=short_moving_average
        self.indicator=idu.MA(long_moving_average=self.long_moving_average,short_moving_average=self.short_moving_average)

    def execute(self, ohlcv_df):
        """
        Génère des signaux de trading en se basant sur une stratégie de moyenne mobile.
        Achète lorsque la moyenne mobile courte croise la moyenne mobile longue de bas en haut.
        Vend lorsque la moyenne mobile courte croise la moyenne mobile longue de haut en bas.
        """
        indic_df=self.indicator.compute(ohlcv_df)
        order_value_s = pd.Series(index=ohlcv_df.index,
                                  name="order_value",
                                  dtype="float")

        idx_buy = indic_df[f"MA_{self.short_moving_average}"] > indic_df[f'MA_{self.long_moving_average}']
        idx_sell = indic_df[f"MA_{self.short_moving_average}"] < indic_df[f'MA_{self.long_moving_average}']
        
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        # Retourner les signaux
        return order_value_s








class STOCAStrategy(Strategy):
    def __init__(self,buy_level,sell_level,window_long,window_short,smooth_k):
        super().__init__("STOC Strategy")
        self.buy_level=buy_level
        self.sell_level=sell_level
        self.window_long=window_long
        self.window_short=window_short
        self.indicator = idu.STOC(window_long=self.window_long,window_short=self.window_short,smooth_k=3)

    def execute(self, ohlcv_df):
        # Compute STOC
        stoc_df = self.indicator.compute(ohlcv_df)
        # Initialize order_value_s as a series filled with nan values
        order_value_s = pd.Series(index=stoc_df.index, name="order_value", dtype="float")
        # Define buy and sell conditions
        idx_buy = (stoc_df[f"STOCHk_{self.window_long}_{self.window_short}_3"] < self.buy_level) & (stoc_df[f"STOCHd_{self.window_long}_{self.window_short}_3"]< self.buy_level) & (stoc_df[f"STOCHk_{self.window_long}_{self.window_short}_3"]> stoc_df[f"STOCHd_{self.window_long}_{self.window_short}_3"])
        idx_sell = (stoc_df[f"STOCHd_{self.window_long}_{self.window_short}_3"] > self.sell_level) & (stoc_df[f"STOCHk_{self.window_long}_{self.window_short}_3"]> self.sell_level) & (stoc_df[f"STOCHk_{self.window_long}_{self.window_short}_3"]< stoc_df[f"STOCHd_{self.window_long}_{self.window_short}_3"])
        # Update order_value_s with 1 for buying, 0 for selling, and leave as nan for holding
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0
        # Return the series of order values
        return order_value_s




class HammerStrategy(Strategy):
    def __init__(self, alpha, beta, profit_threshold, stop_loss_threshold,window):
        self.alpha = alpha
        self.beta = beta
        self.indicator = idu.Hammer(alpha=self.alpha, beta=self.beta)
        self.profit_threshold = profit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.window=window
        
    def execute(self, ohlcv_df):
        # Detect hammer patterns
        hammer_df = self.indicator.compute(ohlcv_df)
        # Calcul du volume moyen sur les x derniers jours
        average_volume = ohlcv_df['volume'].rolling(window=self.window).mean()
        # Create a Series for orders
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        order_value_s[:] = np.nan
        # Correction de volume_condition
        volume_condition = ohlcv_df['volume'] > average_volume
        holding = False
        entry_price = 0
        
        for i in range(1, len(ohlcv_df)):
              
            if hammer_df['hammer'][i-1] and volume_condition[i-1] and not holding:
                # Buy condition based on hammer pattern
                order_value_s[i] = 1
                holding = True
                entry_price = ohlcv_df['close'][i]
                
            elif holding:
                # Sell condition based on profit threshold
                if (ohlcv_df['close'][i] - entry_price) / entry_price >= self.profit_threshold:
                    order_value_s[i] = 0
                    holding = False
                    entry_price = None  # Réinitialisation du prix d'entrée

                # Stop-loss condition
                elif ( ohlcv_df['close'][i]-entry_price) / entry_price <= self.stop_loss_threshold:
                    order_value_s[i] = 0
                    holding = False
                    entry_price = None  # Réinitialisation du prix d'entrée
        
        return order_value_s








class ATRStrategy(Strategy):
    def __init__(self, threshold_atr,period_atr):
        super().__init__("ATR Strategy")
        self.threshold_atr = threshold_atr
        self.period_atr=period_atr
        self.indicator=idu.ATR(period_atr=self.period_atr)
    def execute(self, ohlcv_df):
        atr_df=self.indicator.compute(ohlcv_df)
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        
        # Générer les signaux d'achat et de vente
        idx_buy = (ohlcv_df['close'] > ohlcv_df['close'].shift(1) + self.threshold_atr * atr_df[f'ATRr_{self.period_atr}']) & (ohlcv_df['close'].shift(1) > ohlcv_df['close'].shift(2))
        idx_sell = ((ohlcv_df['close'] < ohlcv_df['close'].shift(1) - self.threshold_atr * atr_df[f'ATRr_{self.period_atr}']) & (ohlcv_df['close'].shift(1) < ohlcv_df['close'].shift(2)))
        
        # Exécuter les transactions en fonction des signaux
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s




class MACDStrategy(Strategy):
    def __init__(self, level,fast, slow, signal):
        super().__init__("MACD Strategy")
        self.level = level
        self.fast=fast
        self.slow=slow
        self.signal=signal
        self.indicator=idu.MACD(fast=self.fast,slow=self.slow,signal=self.signal)

    def execute(self, ohlcv_df):
        macd_df=self.indicator.compute(ohlcv_df)
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        macd_line = macd_df[f"MACD_{self.fast}_{self.slow}_{self.signal}"]
        macd_signal=macd_df[f"MACDs_{self.fast}_{self.slow}_{self.signal}"]
        
        idx_buy = (macd_line > self.level) & (macd_line> macd_signal)
        idx_sell = (macd_line < self.level) & (macd_line< macd_signal)

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s




class MACD_RSIStrategy(Strategy):
    def __init__(self,fast,slow, signal,window, buy_level,sell_level):
        super().__init__("MACD_RSI Strategy")
        self.fast = fast
        self.slow = slow
        self.signal =signal
        self.window=window
        self.buy_level = buy_level
        self.sell_level = sell_level
        self.macd_indicator = idu.MACD(fast=self.fast, slow=self.slow, signal=self.signal)
        self.rsi_indicator = idu.RSI(window=self.window)

    def execute(self, ohlcv_df):
        # Compute MACD and RSI
        macd_df=self.macd_indicator.compute(ohlcv_df)
        rsi_df=self.rsi_indicator.compute(ohlcv_df)
        # Initialize order_value_s as a series filled with 0 (sell/hold) values
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        macd_line = macd_df[f"MACD_{self.fast}_{self.slow}_{self.signal}"]
        macd_signal = macd_df[f"MACDs_{self.fast}_{self.slow}_{self.signal}"]
        # Define buy and sell conditions
        idx_buy = (macd_line > macd_signal) & (rsi_df[f'RSI_{self.window}'] < self.buy_level)
        idx_sell = (macd_line < macd_signal) & (rsi_df[f'RSI_{self.window}'] > self.sell_level)

        # Update order_value_s with 1 for buying, 0 for selling
        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        # Return the series of order values
        return order_value_s



class MACD_SMA_Strategy(Strategy):
    def __init__(self, fast, slow, signal, long_moving_average, short_moving_average):
        super().__init__("MACD & SMA Strategy")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.long_moving_average=long_moving_average
        self.short_moving_average=short_moving_average
        self.macd_indicator = idu.MACD(fast=self.fast, slow=self.slow, signal=self.signal)
        self.sma_indicator = idu.MA(long_moving_average=self.long_moving_average,short_moving_average=self.short_moving_average )

    def execute(self, ohlcv_df):
        macd_df = self.macd_indicator.compute(ohlcv_df)
        sma_df = self.sma_indicator.compute(ohlcv_df)
        
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        macd_line = macd_df[f"MACD_{self.fast}_{self.slow}_{self.signal}"]
        macd_signal = macd_df[f"MACDs_{self.fast}_{self.slow}_{self.signal}"]
        
        idx_macd_buy = (macd_line > macd_signal)
        idx_macd_sell = (macd_line < macd_signal)
        
        idx_sma_buy = sma_df[f"MA_{self.short_moving_average}"] > sma_df[f"MA_{self.long_moving_average}"]
        idx_sma_sell = sma_df[f"MA_{self.short_moving_average}"] < sma_df[f"MA_{self.long_moving_average}"]
        
        # Combining both the strategies
        idx_combined_buy = idx_macd_buy & idx_sma_buy
        idx_combined_sell = idx_macd_sell & idx_sma_sell

        order_value_s.loc[idx_combined_buy] = 1
        order_value_s.loc[idx_combined_sell] = 0

        return order_value_s


















class VWPAStrategy(Strategy):
    def __init__(self):
        super().__init__("VWPA Strategy")

    def execute(self, data_df):
        order_value_s = pd.Series(index=data_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        idx_buy = data_df['typical_price'] > data_df['vwap']
        idx_sell = data_df['typical_price'] < data_df['vwap']

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s







# class RSIDivergenceStrategy(Strategy):
#     def __init__(self, window):
#         super().__init__("RSI Divergence Strategy")
#         self.window = window
#         # Supposons que votre RSI soit calculé à l'aide de l'indicateur RSI_Indicator de idu
#         self.indicator = idu.RSIIndicator(window=self.window)

#     def execute(self, ohlcv_df):
#         rsi_df = self.indicator.compute(ohlcv_df)
        
#         order_value_s = pd.Series(index=ohlcv_df.index, 
#                                   name="order_value", 
#                                   dtype="float")
        
#         # Trouver les sommets et creux pour les prix et le RSI
#         ohlcv_df['price_peak'] = (ohlcv_df['close'] > ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] > ohlcv_df['close'].shift(-1))
#         ohlcv_df['price_trough'] = (ohlcv_df['close'] < ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] < ohlcv_df['close'].shift(-1))
#         ohlcv_df['rsi_peak'] = (rsi_df[f'RSI_{self.window}'] > rsi_df[f'RSI_{self.window}'].shift(1)) & (rsi_df[f'RSI_{self.window}'] > rsi_df[f'RSI_{self.window}'].shift(-1))
#         ohlcv_df['rsi_trough'] = (rsi_df[f'RSI_{self.window}'] < rsi_df[f'RSI_{self.window}'].shift(1)) & (rsi_df[f'RSI_{self.window}'] < rsi_df[f'RSI_{self.window}'].shift(-1))

#         # Identifier les divergences haussières et baissières
#         idx_buy = ohlcv_df['price_trough'] & ~ohlcv_df['rsi_trough']
#         idx_sell = ohlcv_df['price_peak'] & ~ohlcv_df['rsi_peak']

#         order_value_s.loc[idx_buy] = 1
#         order_value_s.loc[idx_sell] = 0

#         return order_value_s



class RSIDivergenceStrategy(Strategy):
    def __init__(self, window,sma_period=200):
        super().__init__("RSI Divergence Strategy")
        self.window = window
        self.indicator = idu.RSI(window=self.window)
        self.sma_period = sma_period

    def execute(self, ohlcv_df):
        rsi_df = self.indicator.compute(ohlcv_df)
        
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        ohlcv_df['sma'] = ohlcv_df['close'].rolling(window=self.sma_period).mean()
        # Trouver les sommets et creux pour les prix et le RSI en utilisant uniquement les données passées
        ohlcv_df['price_peak'] = (ohlcv_df['close'] > ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] > ohlcv_df['close'].shift(2))
        ohlcv_df['price_trough'] = (ohlcv_df['close'] < ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] < ohlcv_df['close'].shift(2))
        ohlcv_df['rsi_peak'] = (rsi_df[f'RSI_{self.window}'] > rsi_df[f'RSI_{self.window}'].shift(1)) & (rsi_df[f'RSI_{self.window}'] > rsi_df[f'RSI_{self.window}'].shift(2))
        ohlcv_df['rsi_trough'] = (rsi_df[f'RSI_{self.window}'] < rsi_df[f'RSI_{self.window}'].shift(1)) & (rsi_df[f'RSI_{self.window}'] < rsi_df[f'RSI_{self.window}'].shift(2))

        # Identifier les divergences haussières et baissières
        idx_buy = (ohlcv_df['price_trough'] & ~ohlcv_df['rsi_trough'] & (ohlcv_df['close'] > ohlcv_df['sma']))
        idx_sell = (ohlcv_df['price_peak'] & ~ohlcv_df['rsi_peak'] & (ohlcv_df['close'] < ohlcv_df['sma']))

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s
    


class MACDDivergenceStrategy(Strategy):
    def __init__(self, fast, slow, signal):
        super().__init__("MACD Divergence Strategy")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.indicator = idu.MACD(fast=self.fast, slow=self.slow, signal=self.signal)

    def execute(self, ohlcv_df):
        macd_df = self.indicator.compute(ohlcv_df)
        
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")
        
        # Trouver les sommets et creux pour les prix en utilisant les données passées uniquement
        ohlcv_df['price_peak'] = (ohlcv_df['close'] > ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] > ohlcv_df['close'].shift(2))
        ohlcv_df['price_trough'] = (ohlcv_df['close'] < ohlcv_df['close'].shift(1)) & (ohlcv_df['close'] < ohlcv_df['close'].shift(2))
        
        # Trouver les sommets et creux du MACD en utilisant les données passées uniquement
        macd_line = macd_df[f"MACD_{self.fast}_{self.slow}_{self.signal}"]
        macd_df['macd_peak'] = (macd_line > macd_line.shift(1)) & (macd_line > macd_line.shift(2))
        macd_df['macd_trough'] = (macd_line < macd_line.shift(1)) & (macd_line < macd_line.shift(2))

        # Identifier les divergences haussières et baissières
        idx_buy = ohlcv_df['price_trough'] & ~macd_df['macd_trough'] & (ohlcv_df['close'] > ohlcv_df['close'].shift(1))  # Conditions pour divergence haussière
        idx_sell = ohlcv_df['price_peak'] & ~macd_df['macd_peak'] & (ohlcv_df['close'] < ohlcv_df['close'].shift(1))  # Conditions pour divergence baissière


        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        # S'assurer que les décisions d'achat et de vente ne sont prises qu'après la confirmation de la divergence
        order_value_s = order_value_s.shift(1)
        
        return order_value_s





class FibonacciRetracementStrategy(Strategy):
    def __init__(self, level_A, level_B, level_C):
        super().__init__("Fibonacci Retracement Strategy")
        self.level_A = level_A
        self.level_B = level_B
        self.level_C = level_C
        self.indcator=idu.FibonacciRetracement(level_A=self.level_A,level_B=self.level_B,level_C=self.level_C)
    def execute(self, ohlcv_df):
       
        indic_df=self.indcator.compute(ohlcv_df)
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")

        # Stratégie basée sur les niveaux de Fibonacci
        idx_buy = (ohlcv_df['close'] > indic_df[f"Fibonacci_{self.level_C}"]) & (ohlcv_df['close'] <= indic_df[f"Fibonacci_{self.level_B}"])
        idx_sell = (ohlcv_df['close'] < indic_df[f"Fibonacci_{self.level_A}"]) & (ohlcv_df['close'] >= indic_df[f"Fibonacci_{self.level_B}"])

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s




class ADXStrategy(Strategy):
    def __init__(self, window,buy_level, sell_level):
        super().__init__("ADX Strategy")
        self.window = window
        self.buy_level=buy_level
        self.sell_level=sell_level

        self.indicator = idu.ADX(window=self.window)

    def execute(self, ohlcv_df):
        adx_df = self.indicator.compute(ohlcv_df)
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")

        adx_line = adx_df[f"ADX_{self.window}"]

        # Si l'ADX est supérieur à 25, utilisez des stratégies de suivi de tendance
        idx_trend_following = adx_line > self.buy_level

        # Si l'ADX est inférieur à 20, le marché est en consolidation
        idx_range = adx_line < self.sell_level

        # Pour cette stratégie, nous ne donnons que des signaux pour entrer ou sortir de positions basées sur l'ADX.
        # Nous n'utilisons pas d'autres indicateurs pour donner des signaux d'achat ou de vente.
        # Toutefois, vous pourriez vouloir intégrer d'autres indicateurs pour préciser quand acheter ou vendre.

        # Pour cet exemple, nous supposerons que nous achetons lors d'une tendance haussière et vendons dans un marché de consolidation.
        order_value_s.loc[idx_trend_following] = 1
        order_value_s.loc[idx_range] = 0

        return order_value_s




class IchimokuStrategy(Strategy):
    def __init__(self, tenkan_window, kijun_window, senkou_span_b_window, displacement):
        super().__init__(name="Ichimoku Cloud Strategy")
        self.indicator = idu.Ichimoku(
            tenkan_window=tenkan_window, 
            kijun_window=kijun_window, 
            senkou_span_b_window=senkou_span_b_window, 
            displacement=displacement
        )

    def execute(self, ohlcv_df):
        ichimoku_df = self.indicator.compute(ohlcv_df)
        
        order_value_s = pd.Series(index=ohlcv_df.index, 
                                  name="order_value", 
                                  dtype="float")

        # Achat lorsque le prix passe au-dessus du nuage Ichimoku (Senkou Span A > Senkou Span B)
        idx_buy = (ohlcv_df['close'] > ichimoku_df[self.indicator.var_senkou_a]) & \
                  (ichimoku_df[self.indicator.var_senkou_a] > ichimoku_df[self.indicator.var_senkou_b])
        
        # Vente lorsque le prix passe en dessous du nuage Ichimoku (Senkou Span A < Senkou Span B)
        idx_sell = (ohlcv_df['close'] < ichimoku_df[self.indicator.var_senkou_a]) & \
                   (ichimoku_df[self.indicator.var_senkou_a] < ichimoku_df[self.indicator.var_senkou_b])

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s
    
    
    

class DonchianChannelStrategy(Strategy):
    def __init__(self, window):
        self.window = window
        self.indicator = idu.DonchianChannel(window=self.window)

    def execute(self, ohlcv_df):
        donchian_df = self.indicator.compute(ohlcv_df)
        
        order_value_s = pd.Series(index=ohlcv_df.index, name="order_value", dtype="float")
        
        # Création de trades
        idx_buy = (ohlcv_df['close'] > donchian_df[f'Donchian_High_{self.window}']).rolling(2).sum() == 2
        idx_sell = (ohlcv_df['close'] < donchian_df[f'Donchian_Low_{self.window}']).rolling(2).sum() == 2

        # Retraits de trades
        median_band = (donchian_df[f'Donchian_High_{self.window}'] + donchian_df[f'Donchian_Low_{self.window}']) / 2
        optimal_buy = (ohlcv_df['close'] > median_band) & (ohlcv_df['close'].shift() <= median_band)
        optimal_sell = (ohlcv_df['close'] < median_band) & (ohlcv_df['close'].shift() >= median_band)
        
        # Consolidate signals
        idx_buy |= optimal_buy
        idx_sell |= optimal_sell

        order_value_s.loc[idx_buy] = 1
        order_value_s.loc[idx_sell] = 0

        return order_value_s




class KalmanMeanReversionStrategy(Strategy):
    def __init__(self, initial_state, observation_covariance, transition_covariance, transition_matrices):
        self.initial_state = initial_state
        self.observation_covariance = observation_covariance
        self.transition_covariance = transition_covariance
        self.transition_matrices = transition_matrices

    def execute(self, prices):
        kf = KalmanFilter(initial_state_mean=self.initial_state,
                          observation_covariance=self.observation_covariance,
                          transition_covariance=self.transition_covariance,
                          transition_matrices=self.transition_matrices)
        print(kf)
        # Use Kalman filter to estimate the hidden state (mean price)
        state_means, _ = kf.filter(prices)
        
        # Define the trading signals based on the estimated state
        signals = pd.Series(index=prices.index, data=0)
        signals[prices < state_means[:, 0]] = 1  # Buy signal
        signals[prices > state_means[:, 0]] = -1  # Sell signal

        return signals


class BehavioralVolatilityStrategy(Strategy):
    def __init__(self, atr_period=14, rsi_period=14, sentiment_threshold=0.3, atr_multiplier=1.5):
        self.atr_period = atr_period
        self.rsi_period = rsi_period
        self.sentiment_threshold = sentiment_threshold
        self.atr_multiplier = atr_multiplier

    def execute(self, high, low, close, sentiment_index):
        # Calcul des indicateurs techniques
        atr = talib.ATR(high, low, close, timeperiod=self.atr_period)
        rsi = talib.RSI(close, timeperiod=self.rsi_period)
        
        # Calcul de la moyenne mobile de l'ATR
        atr_ma = pd.Series(atr).rolling(window=60).mean()

        # Initialisation des signaux de trading
        signals = pd.Series(index=close.index, data=0)  # 0 pour 'aucun signal'

        # Signaux d'achat
        buy_signals = (
            (atr > atr_ma * self.atr_multiplier) & 
            (rsi < 30) & 
            (sentiment_index < self.sentiment_threshold)
        )
        signals[buy_signals] = 1  # 1 pour 'achat'

        # Signaux de vente
        sell_signals = (
            (atr < atr_ma / self.atr_multiplier) & 
            (rsi > 70) & 
            (sentiment_index > (1 - self.sentiment_threshold))
        )
        signals[sell_signals] = -1  # -1 pour 'vente'

        return signals



class DojiStrategy(Strategy):
    def __init__(self, doji_threshold_ratio, risk_reward_ratio):
        self.doji_threshold_ratio=doji_threshold_ratio
        self.doji_indicator = idu.Doji(threshold_ratio=self.doji_threshold_ratio)
        self.risk_reward_ratio = risk_reward_ratio

    def execute(self, ohlcv_df):
        # Compute Doji patterns
        doji_df = self.doji_indicator.compute(ohlcv_df)
        
        # Initialize signals
        signals = pd.DataFrame(index=ohlcv_df.index)
        signals['order'] = np.nan  # 0 for no action, 1 for buy, -1 for sell
        signals['stop_loss'] = None  # To track stop-loss price
        signals['take_profit'] = None  # To track take-profit price
        
        # Trading signals based on Doji strategy
        for i in range(1, len(ohlcv_df) - 1):
            # Buying logic
            if doji_df['doji'][i] and ohlcv_df['close'][i+1] > ohlcv_df['close'][i]:
                signals.at[ohlcv_df.index[i+1], 'order'] = 1
                signals.at[ohlcv_df.index[i+1], 'stop_loss'] = ohlcv_df['low'][i]  # Stop-loss below Doji low
                signals.at[ohlcv_df.index[i+1], 'take_profit'] = ohlcv_df['close'][i+1] + \
                                                                 (ohlcv_df['close'][i+1] - ohlcv_df['low'][i]) * self.risk_reward_ratio
            # Selling logic
            elif doji_df['doji'][i] and ohlcv_df['close'][i+1] < ohlcv_df['close'][i]:
                signals.at[ohlcv_df.index[i+1], 'order'] = 0
                signals.at[ohlcv_df.index[i+1], 'stop_loss'] = ohlcv_df['high'][i]  # Stop-loss above Doji high
                signals.at[ohlcv_df.index[i+1], 'take_profit'] = ohlcv_df['close'][i+1] - \
                                                                 (ohlcv_df['high'][i] - ohlcv_df['close'][i+1]) * self.risk_reward_ratio
        
        # Clean up signals DataFrame by removing rows without orders
        signals = signals.dropna(subset=['order'])
        
        # Return only the 'order' column for simplicity if needed
        return signals['order']
 



class StrategyPolyModel(Strategy):
    def __init__(self, degree=2):
        self.degree = degree
        self.model = None

    def train_model(self, X, y):
        """
        Entraîne le modèle de régression polynomiale.
        X : données d'entrée (OHLCV retardées).
        y : rendements du Bitcoin à prédire.
        """
        # Création des caractéristiques polynomiales
        poly_features = PolynomialFeatures(degree=self.degree)
        X_poly = poly_features.fit_transform(X)

        # Séparation en ensembles d'entraînement et de test
        X_train, X_test, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=42)

        # Entraînement du modèle
        self.model = LinearRegression()
        self.model.fit(X_train, y_train)

        # Évaluation du modèle
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        print(f"RMSE: {rmse}")

    def predict(self, X_new):
        """
        Prédit les rendements du Bitcoin basés sur de nouvelles données d'entrée.
        X_new : nouvelles données OHLCV retardées.
        """
        poly_features = PolynomialFeatures(degree=self.degree)
        X_new_poly = poly_features.fit_transform(X_new)
        return self.model.predict(X_new_poly)




