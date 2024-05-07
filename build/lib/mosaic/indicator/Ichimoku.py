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


class Ichimoku(IndicatorOHLCV):
    """Ichimoku Kinko Hyo (Ichimoku Cloud)"""

    tenkan_window: int = Field(9, description="Window for Tenkan Sen")
    kijun_window: int = Field(26, description="Window for Kijun Sen")
    senkou_span_b_window: int = Field(52, description="Window for Senkou Span B")
    displacement: int = Field(26, description="Number of periods for displacement")

    var_tenkan_fmt: str = Field("TenkanSen_{tenkan_window}", description="Indicator name format for Tenkan Sen")
    var_kijun_fmt: str = Field("KijunSen_{kijun_window}", description="Indicator name format for Kijun Sen")
    var_senkou_a_fmt: str = Field("SenkouSpanA", description="Indicator name format for Senkou Span A")
    var_senkou_b_fmt: str = Field("SenkouSpanB_{senkou_span_b_window}", description="Indicator name format for Senkou Span B")
    var_chikou_fmt: str = Field("ChikouSpan", description="Indicator name format for Chikou Span")

    @property
    def var_tenkan(self):
        return self.var_tenkan_fmt.format(**self.dict())
    
    @property
    def var_kijun(self):
        return self.var_kijun_fmt.format(**self.dict())

    @property
    def var_senkou_a(self):
        return self.var_senkou_a_fmt

    @property
    def var_senkou_b(self):
        return self.var_senkou_b_fmt.format(**self.dict())

    @property
    def var_chikou(self):
        return self.var_chikou_fmt

    def compute(self, ohlcv_df, **kwrds):
        super().compute(ohlcv_df, **kwrds)
        
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        
        # Tenkan Sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan = (ohlcv_df['high'].rolling(window=self.tenkan_window).max() + 
                  ohlcv_df['low'].rolling(window=self.tenkan_window).min()) / 2
        
        # Kijun Sen (Base Line): (26-period high + 26-period low)/2
        kijun = (ohlcv_df['high'].rolling(window=self.kijun_window).max() + 
                 ohlcv_df['low'].rolling(window=self.kijun_window).min()) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_a = ((tenkan + kijun) / 2).shift(self.displacement)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        senkou_b = ((ohlcv_df['high'].rolling(window=self.senkou_span_b_window).max() + 
                     ohlcv_df['low'].rolling(window=self.senkou_span_b_window).min()) / 2).shift(self.displacement)
        
        # Chikou Span (Lagging Span): Close shifted 26 periods to the past
        chikou = ohlcv_df['close'].shift(-self.displacement)

        indic_df[self.var_tenkan] = tenkan
        indic_df[self.var_kijun] = kijun
        indic_df[self.var_senkou_a] = senkou_a
        indic_df[self.var_senkou_b] = senkou_b
        indic_df[self.var_chikou] = chikou
        
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False):
        var_open = 'open'
        var_high = 'high'
        var_low = 'low'
        var_close = 'close'

        indic_df = self.compute(ohlcv_df).reset_index().dropna()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

    # Add OHLC data
        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                 open=ohlcv_df[var_open],
                                 high=ohlcv_df[var_high],
                                 low=ohlcv_df[var_low],
                                 close=ohlcv_df[var_close], name="OHLC"),
                  row=1, col=1)

    # Add Tenkan, Kijun, and Chikou lines
        fig.add_trace(go.Scatter(x=indic_df.index, y=indic_df[self.var_tenkan], mode='lines', line=dict(width=1, color='blue'), name='Tenkan Sen'), row=2, col=1)
        fig.add_trace(go.Scatter(x=indic_df.index, y=indic_df[self.var_kijun], mode='lines', line=dict(width=1, color='red'), name='Kijun Sen'), row=2, col=1)
        fig.add_trace(go.Scatter(x=indic_df.index, y=indic_df[self.var_chikou], mode='lines', line=dict(width=1, color='green'), name='Chikou Span'), row=2, col=1)

    # Add Ichimoku Cloud
        fig.add_trace(go.Scatter(x=indic_df.index, y=indic_df[self.var_senkou_a], fill=None, mode='lines', line=dict(width=0.5, color='pink'), name='Senkou Span A'), row=2, col=1)
        fig.add_trace(go.Scatter(x=indic_df.index, y=indic_df[self.var_senkou_b], fill='tonexty', mode='lines', line=dict(width=0.5, color='lightseagreen'), name='Senkou Span B'), row=2, col=1)

        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
          return fig, indic_df
        else:
          return fig
