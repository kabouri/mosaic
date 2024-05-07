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







class MACD(IndicatorOHLCV):
    """Moving Average Convergence Divergence (MACD)"""

    fast: int = Field(
        0, description=" The short period")
    slow:int = Field(
        0, description="The long period")
    signal:int = Field(
        0, description="The signal period")
    
    var_macd_fast_fmt: str = Field(
     "MACD_{macd_fast}_{macd_slow}_{macd_signal}", description="Indicator name format")
    var_macd_slow_fmt: str = Field(
     "MACDs_{macd_fast}_{macd_slow}_{macd_signal}", description="Indicator name format")
    var_macd_signal_fmt: str = Field(
     "MACDh_{macd_fast}_{macd_slow}_{macd_signal}", description="Indicator name format")

    @property
    def var_macd_fast(self):
        return self.var_macd_fast_fmt.format(**self.dict())
    
    @property
    def var_macd_slow(self):
        return self.var_macd_slow_fmt.format(**self.dict())
    
    @property
    def var_macd_signal(self):
        return self.var_macd_signal_fmt.format(**self.dict())
    
    @property
    def indic_name_offset(self):
        return self.offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)

    @property
    def indic_d_name_offset(self):
        return self.offset_fmt.format(indic_name=self.indic_d_name,
                                      offset=-self.offset)


    def compute(self, ohlcv_df, **kwrds):
        """Compute MACD"""
        super().compute(ohlcv_df, **kwrds)

        indic_df = pd.DataFrame(index=ohlcv_df.index)
        # OHLCV variable identification
        var_close = self.ohlcv_names.get("close", "close")
        # Compute MACD 
        indic_df =ta.macd(ohlcv_df[var_close],fast=self.fast, slow=self.slow, signal=self.signal, append=False)
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df).reset_index().dropna()

        fig = make_subplots(rows=3, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02)

        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close], name="OHLC"),
                      row=1, col=1)

        color_indic = px.colors.qualitative.T10[0]
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[f"MACD_{self.fast}_{self.slow}_{self.signal}"],
            name="MACD",
            mode='lines',
            line_color=color_indic
        ),
            row=3, col=1)
        
        fig.add_trace(go.Bar(
            x=indic_df["time"],
            y=indic_df[f"MACDh_{self.fast}_{self.slow}_{self.signal}"],
            name="MACDh"
        ),
            row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[f"MACDs_{self.fast}_{self.slow}_{self.signal}"],
            name="MACDs",
            mode='lines',
            line_color=color_indic
        ),
            row=3, col=1)
        
        

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig