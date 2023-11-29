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

class STOC(IndicatorOHLCV):
    """Indicator: Stochastic Oscillator (STOCH)"""

    window_long: int = Field(
        0, description="MA long window size used to compute the indicator")
    window_short: int = Field(
        0, description="MA short window size used to compute the indicator")
    smooth_k: int = Field(
        3, description="smooth_k (int): The Slow %D period. Default: 3")
    var_window_long_fmt: str = Field(
     "STOCHk_{window_long}_{window_short}_{smooth_k}", description="Indicator name format")
    var_window_short_fmt: str = Field(
     "STOCHd_{window_long}_{window_short}_{smooth_k}", description="Indicator name format")

   
    @property
    def var_window_long(self):
        return self.var_window_long_fmt.format(**self.dict())
    
    
    @property
    def var_window_short(self):
        return self.var_window_short_fmt.format(**self.dict())
  

    @property
    def var_window_long_offset(self):
        return self.var_window_long_offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)
    @property
    def var_window_short_offset(self):
        return self.var_window_short_offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)

    @property
    def bw_window(self):
        return super().bw_window + self.window_long+self.window_short+self.smooth_k

    # @property
    # def indic_name(self):
        # return self.indic_fmt.format(window_long=self.window_long, window_short=self.window_short, smooth_k=self.smooth_k)

    # @property
    # def indic_d_name(self):
    #     return self.indic_d_fmt.format(
    #         indic_name=self.indic_name,
    #         window=self.window)

    # @property
    # def indic_name_offset(self):
    #     return self.offset_fmt.format(indic_name=self.indic_name,
    #                                   offset=-self.offset)

    # @property
    # def indic_d_name_offset(self):
    #     return self.offset_fmt.format(indic_name=self.indic_d_name,
    #                                   offset=-self.offset)

    # @property
    # def labels(self):
    #     return [f"{int(self.levels[0])}-"] + \
    #         [f"{int(x)}-{int(y)}"
    #          for x, y in zip(self.levels[:-1], self.levels[1:])] + \
    #         [f"{int(self.levels[-1])}+"]

    def compute(self, ohlcv_df, **kwrds):
        """Compute STOCH"""
        super().compute(ohlcv_df, **kwrds)
        
        # OHLCV variable identification
        df=ta.stoch(
            close=ohlcv_df["close"],
            high=ohlcv_df["high"],
            low=ohlcv_df["low"],
            k=self.window_long,
            d=self.window_short)
        # indic_df = pd.DataFrame(index=ohlcv_df.index)
        # indic_df[self.indic_fmt_k] = ta.stoch(
        #     close=ohlcv_df["close"],
        #     high=ohlcv_df["high"],
        #     low=ohlcv_df["low"],
        #     k=self.window_long,
        #     d=self.window_short

        # )
        # indic_df[self.indic_fmt_d] = ta.stoch(
        #     close=ohlcv_df["close"],
        #     high=ohlcv_df["high"],
        #     low=ohlcv_df["low"],
        #     k=self.window_long,
        #     d=self.window_short

        # )
        
        return df

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
        fig.add_trace(go.Scatter(x=indic_df["time"], y=indic_df[f"STOCHk_{self.window_long}_{self.window_short}_{self.smooth_k}"],
                                 mode='lines',
                                 name='% K'), row=3, col=1)

        fig.add_trace(go.Scatter(x=indic_df["time"], y=indic_df[f"STOCHd_{self.window_long}_{self.window_short}_{self.smooth_k}"],
                                 mode='lines',
                                 name='% D'), row=3, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
