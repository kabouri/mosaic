from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import typing
import pandas_ta as ta
from pydantic import Field
from .indicator import IndicatorOHLCV
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401






class MA(IndicatorOHLCV):
    """
    Moving Average 
    """
    long_moving_average: int = Field(
        0, description="MA long window")
    short_moving_average: int = Field(
        0, description="MA short window ")
    mode: str = Field(
        "SMA", description="Calulation mode 'SMA' or 'EMA'")
    var_MA_long_fmt: str = Field(
     "MA_{long_moving_average}", description="Indicator name format")
    var_MA_short_fmt: str = Field(
     "MA_{short_moving_average}", description="Indicator name format")

   
    @property
    def var_MA_long(self):
        return self.var_MA_long_fmt.format(**self.dict())
    
    
    @property
    def var_MA_short(self):
        return self.var_MA_short_fmt.format(**self.dict())
  

    @property
    def var_MA_long_offset(self):
        return self.var_MA_long_offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)
    @property
    def var_MA_short_offset(self):
        return self.var_MA_short_offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)

    @property
    def bw_window(self):
        return super().bw_window + self.window_long+self.window_short+self.smooth_k

    def compute(self, ohlcv_df, **kwrds):
        """Compute MA """
        super().compute(ohlcv_df, **kwrds)
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        if self.mode == "SMA":
            indic_df[self.var_MA_short] = ohlcv_df['close'].rolling(window=self.short_moving_average).mean()
            indic_df[self.var_MA_long] = ohlcv_df['close'].rolling(window=self.long_moving_average).mean()
        else:
            indic_df[self.var_MA_short] = ohlcv_df['close'].ewm(span=self.short_moving_average, adjust=False).mean()
            indic_df[self.var_MA_long] = ohlcv_df['close'].ewm(span=self.long_moving_average, adjust=False).mean()
        
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df).reset_index().dropna()
        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02)

        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close], name="OHLC"),
                      row=1, col=1)

        color_indic = px.colors.qualitative.T10[0]
        fig.add_trace(go.Scatter(x=indic_df["time"], y=indic_df[self.var_MA_long],
                                 mode='lines',
                                 name='MA long'), row=2, col=1)

        fig.add_trace(go.Scatter(x=indic_df["time"], y=indic_df[self.var_MA_short],
                                 mode='lines',
                                 name='MA short '), row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
