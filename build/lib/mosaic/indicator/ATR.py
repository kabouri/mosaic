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



class ATR(IndicatorOHLCV):
    """Indicator: Average True Range (ATR)"""
    period_atr: int = Field(
        0, description="MA window size used to compute the indicator")
    
    indic_fmt: str = Field(
        "ATRr_{period_atr}", description="Indicator name format")
    
    @property
    def bw_window(self):
        return super().bw_window + self.window

    @property
    def indic_name(self):
        return self.indic_fmt.format(period_atr=self.period_atr)

    @property
    def indic_name_offset(self):
        return self.offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)


    def compute(self, ohlcv_df, **kwrds):
        """Compute ATR"""
        super().compute(ohlcv_df, **kwrds)
        
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        indic_df[self.indic_name] = ta.atr(ohlcv_df['high'], ohlcv_df['low'],
                            ohlcv_df['close'], length=self.period_atr)
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
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[f"ATRr_{self.period_atr}"],
            name="ATR",
            mode='markers+lines',
            line_color=color_indic
        ),
            row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
