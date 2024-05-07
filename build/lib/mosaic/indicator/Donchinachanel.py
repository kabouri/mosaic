from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import typing
import pandas_ta as ta
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class DonchianChannel(IndicatorOHLCV):
    """Donchian Channel Indicator"""

    window: int = Field(
        20, description="The window period over which the Donchian Channel is computed."
    )
    
    var_high_fmt: str = Field("Donchian_High_{window}", description="Indicator name format for upper channel")
    var_low_fmt: str = Field("Donchian_Low_{window}", description="Indicator name format for lower channel")

    @property
    def var_high(self):
        return self.var_high_fmt.format(**self.dict())

    @property
    def var_low(self):
        return self.var_low_fmt.format(**self.dict())

    def compute(self, ohlcv_df):
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        indic_df[self.var_high] = ohlcv_df['high'].rolling(window=self.window).max()
        indic_df[self.var_low] = ohlcv_df['low'].rolling(window=self.window).min()
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False):
        donchian_df = self.compute(ohlcv_df).reset_index().dropna()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,vertical_spacing=0.02)

        # Adding OHLC candles
        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df['open'],
                                     high=ohlcv_df['high'],
                                     low=ohlcv_df['low'],
                                     close=ohlcv_df['close'],
                                     name="OHLC"),row=1, col=1)

        # Adding Donchian Bands
        fig.add_trace(go.Scatter(x=ohlcv_df.index, y=donchian_df[self.var_high], mode='lines', name="Donchian High", line=dict(color='blue')), row=2, col=1)
        fig.add_trace(go.Scatter(x=ohlcv_df.index, y=donchian_df[self.var_low], mode='lines', name="Donchian Low", line=dict(color='red')), row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)
        
        if ret_indic:
            return fig, donchian_df
        else:
            return fig