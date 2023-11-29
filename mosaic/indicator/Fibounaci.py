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


class FibonacciRetracement(IndicatorOHLCV):
    """Fibonacci Retracement Indicator"""
    
    level_A: float = Field(0.236, description="Fibonacci level A")
    level_B: float = Field(0.382, description="Fibonacci level B")
    level_C: float = Field(0.618, description="Fibonacci level C")
    
    var_A_fmt: str = Field("Fibonacci_{level_A}", description="Indicator name format for level A")
    var_B_fmt: str = Field("Fibonacci_{level_B}", description="Indicator name format for level B")
    var_C_fmt: str = Field("Fibonacci_{level_C}", description="Indicator name format for level C")

    @property
    def var_A(self):
        return self.var_A_fmt.format(level_A=self.level_A)

    @property
    def var_B(self):
        return self.var_B_fmt.format(level_B=self.level_B)

    @property
    def var_C(self):
        return self.var_C_fmt.format(level_C=self.level_C)

    def compute(self, ohlcv_df):
        peak = ohlcv_df['high'].max()
        trough = ohlcv_df['low'].min()
        
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        indic_df[self.var_A] = peak - self.level_A * (peak - trough)
        indic_df[self.var_B] = peak - self.level_B * (peak - trough)
        indic_df[self.var_C] = peak - self.level_C * (peak - trough)
        
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False):
        var_open = "open"
        var_high = "high"
        var_low = "low"
        var_close = "close"

        indic_df = self.compute(ohlcv_df).reset_index().dropna()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df[var_open],
                                     high=ohlcv_df[var_high],
                                     low=ohlcv_df[var_low],
                                     close=ohlcv_df[var_close], name="OHLC"),
                      row=1, col=1)

        for level, color in zip([self.var_A, self.var_B, self.var_C], ['red', 'green', 'blue']):
            fig.add_trace(go.Scatter(
                x=indic_df.index,
                y=indic_df[level],
                name=f'Fibonacci {level}',
                mode='lines',
                line_color=color
            ),row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
