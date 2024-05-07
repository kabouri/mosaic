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







class Hammer(IndicatorOHLCV):
    beta: float = Field(2.0, description="Multiplier for lower shadow length in hammer pattern")
    alpha: float = Field(0.5, description="Multiplier for upper shadow length in hammer pattern")
    
    def compute(self, ohlcv_df):
        # Create a DataFrame for hammer patterns
        hammer_df = pd.DataFrame(index=ohlcv_df.index)
        
        # Define the hammer conditions
        lower_shadow = ohlcv_df['open'] - ohlcv_df['low']
        body = ohlcv_df['close'] - ohlcv_df['open']
        upper_shadow = ohlcv_df['high'] - ohlcv_df['close']
        
        hammer_condition = ((body > 0) &
                            (lower_shadow >= self.beta * body) &
                            (upper_shadow <= self.alpha * body))
        
        hammer_df['hammer'] = hammer_condition
        
        return hammer_df
    
    def plotly(self, ohlcv_df, layout={}, ret_indic=False):
        hammer_df = self.compute(ohlcv_df).reset_index().dropna()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

        # Adding OHLC candles
        fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                     open=ohlcv_df['open'],
                                     high=ohlcv_df['high'],
                                     low=ohlcv_df['low'],
                                     close=ohlcv_df['close'],
                                     name="OHLC"),row=1, col=1)

        # Highlighting hammers
        hammers = ohlcv_df[hammer_df['hammer'].values]
        # Adding Hammer markers
        fig.add_trace(go.Scatter(x=hammers.index, 
                             y=hammers['low'], 
                             mode='markers', 
                             marker=dict(size=10, color='blue', symbol='triangle-up'), 
                             name="Hammer"))

    # Adding arrows pointing to Hammer candles
        annotations = []
        offset = 0.5 
        for idx, row in hammers.iterrows():
            annotations.append(
            go.layout.Annotation(
                x=idx,
                y=row['low'] - offset, # Adjusting the position of the arrow above the hammer
                xref="x",
                yref="y",
                text="",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="blue",
                ax=0,
                ay=30,  # Length of the arrow
            )
        )

        fig.update_layout(annotations=annotations)
        
        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)

        if ret_indic:
            return fig, hammer_df
        else:
            return fig
