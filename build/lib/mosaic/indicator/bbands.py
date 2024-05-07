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






class BBands(IndicatorOHLCV):
    """Indicator: Bollinger Bands (BBANDS)"""
    
    length: int = Field(
        0, description="The number of periods (usually days) used to calculate the moving average in the middle band")
    std:float = Field(
        0, description=" The number of standard deviations away from the moving average to calculate the upper and lower bands")
    ddof: int=Field(
        0, description='ddof is a parameter used to adjust the calculation of standard deviation or variance as a function of sample size and degree of freedom. set at 0 by pandas ta')
    
    var_bb_length_fmt: str = Field(
     "BBL_{length}_{std}", description="Indicator name format")
    var_bb_std_fmt: str = Field(
     "BBM_{length}_{std}", description="Indicator name format")
    var_bb_ddof_fmt: str = Field(
     "BBU_{length}_{std}", description="Indicator name format")

    @property
    def var_bb_length(self):
        return self.var_bb_length_fmt.format(**self.dict())
    
    @property
    def var_bb_std(self):
        return self.var_bb_std_fmt.format(**self.dict())
    
    @property
    def var_bb_ddof(self):
        return self.var_bb_ddof_fmt.format(**self.dict())

    @property
    def indic_name_offset(self):
        return self.offset_fmt.format(indic_name=self.indic_name,
                                      offset=-self.offset)

    def compute(self, ohlcv_df, **kwrds):
        
        """Compute BBands """
        
        super().compute(ohlcv_df, **kwrds)
        
        indic_df = pd.DataFrame(index=ohlcv_df.index)
        indic_df =ta.bbands(ohlcv_df['close'], self.length, self.std,
                   ddof=0)
        return indic_df

    def plotly(self, ohlcv_df, layout={}, ret_indic=False, **params):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        indic_df = self.compute(ohlcv_df).reset_index().dropna()
        print(indic_df)

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
            y=indic_df[f"BBL_{self.length}_{self.std}"],
            name="BBL",
            mode='lines',
            line_color=color_indic
        ),
            row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[f"BBM_{self.length}_{self.std}"],
            name="BBM",
            mode='lines'
        ),
            row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=indic_df["time"],
            y=indic_df[f"BBU_{self.length}_{self.std}"],
            name="BBU",
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
