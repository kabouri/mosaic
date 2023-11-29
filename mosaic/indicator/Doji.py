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








class Doji(IndicatorOHLCV):
    threshold_ratio: float = Field(0.03, description="Ratio of the candle's range that the open-close distance must be within to qualify as a Doji")

    def compute(self, ohlcv_df):
        # Create a DataFrame for Doji patterns
        doji_df = pd.DataFrame(index=ohlcv_df.index)
        
        # Calculate the candle's range
        high_low_range = ohlcv_df['high'] - ohlcv_df['low']
        
        # Identify the Doji candles
        doji_df['doji'] = (abs(ohlcv_df['open'] - ohlcv_df['close']) <= high_low_range * self.threshold_ratio)

        return doji_df

    def plotly(self, ohlcv_df):
        doji_df = self.compute(ohlcv_df)
        dojis = ohlcv_df[doji_df['doji']]

        fig = make_subplots(rows=1, cols=1)

        # Adding OHLC candles
        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df['open'],
                                     high=ohlcv_df['high'],
                                     low=ohlcv_df['low'],
                                     close=ohlcv_df['close'],
                                     name="OHLC"))

        # Adding Doji markers
        fig.add_trace(go.Scatter(x=dojis.index, 
                                 y=dojis['high'], 
                                 mode='markers', 
                                 marker=dict(size=10, color='orange', symbol='star'), 
                                 name="Doji"))

        # Setting titles and layout
        fig.update_layout(
            title="Doji Patterns on OHLC Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Legend",
            xaxis_rangeslider_visible=False
        )

        return fig