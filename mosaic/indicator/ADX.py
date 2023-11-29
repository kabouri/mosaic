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
from ta.trend import ADXIndicator as taADX







class ADX(IndicatorOHLCV):
    """Average Directional Index (ADX)"""

    window: int = Field(
        0, description="The period over which the ADX is computed.")
    
    var_adx_fmt: str = Field("ADX_{window}", description="Indicator name format")

    @property
    def var_adx(self):
        return self.var_adx_fmt.format(**self.dict())
    
    @property
    def indic_name_offset(self):
        return self.offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)

    def compute(self, ohlcv_df, **kwrds):
        """Compute ADX"""
        super().compute(ohlcv_df, **kwrds)
        
        # OHLCV variable identification
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")
        
        # Compute ADX
        adx = taADX(ohlcv_df[var_high], ohlcv_df[var_low], ohlcv_df[var_close], window=self.window)
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        indic_df[self.var_adx] = adx.adx()
        
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
            y=indic_df[self.var_adx],
            name="ADX",
            mode='lines',
            line_color=color_indic
        ),
            row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, indic_df
        else:
            return fig
