
# Table des matières

1.  [Introduction](#introduction)
2.  [Technical prerequisites](#init-env)
3.  [Create the decision model](#org254be7d)
4.  [Bot Specification](#org933efcc)
        1.  [YAML Configuration](#orgc643419)
5.  [Executing the bot in backtest mode](#org112c14b)



<a id="introduction"></a>

# Introduction

This tutorial explains how to create a trading bot using a deterministic rule based on a technical
indicators. For example, consider a traditional trading method that uses RSI thresholds to
trigger buy and sell orders.


<a id="init-env"></a>

# Technical prerequisites

The MOSAIC library requires Python version >= 3.10.

To facilitate your development projects, it is recommended to use a Python virtual environment to
perform this tutorial. So start by installing the `pew` manager if you haven't already done so: 

    pip install pew

Then create a new virtual environment:

    pew new mosaic_bot_rsi

Now create a directory that will contain the files of this tutorial, e.g. `mosaic_bot_rsi`, and
navigate to this directory: 

    mkdir mosaic_bot_rsi
    cd mosaic_bot_rsi

Note that you can save this directory as associated with the virtual environment you just created
with the command: 

    pew setproject

Finally, install the MOSAIC library in your environment from GitHub:

    pip install https://github.com/edgemind-sas/mosaic.git          

If the installation was successful, you should be able to import the MOSAIC library in a Python
session and display its version: 

    import mosaic
    
    print(mosaic.__version__)

    0.0.42


<a id="org254be7d"></a>

# Create the decision model

Let's create a decision model based on RSI indicator. To do this, we define a decision model class
`DMRSI` that inherits from class `mdm.DMDR`.

What you need is to define :

-   The `features` attributes as a dictionary that contains an RSI indicator (from the MOSAIC
    library) with its period (here of length 10) as the only technical indicator needed.
-   A method `compute_signal_idx` that accepts a pandas DataFrame, `features_df`, which is expected to contain
    RSI values. The method defines the strategy by making buy signals when the RSI is below `self.buy_threshold` and sell signals when
    it is above `self.sell_threshold`. It returns two Pandas Series with boolean values indicating these
    events.

    import typing
    import mosaic.indicator as mid
    import mosaic.decision_model as mdm
    
    class DMRSI(mdm.DMDR):
        features: typing.Dict[str, mid.Indicator] = {
            "rsi": mid.RSI(length=10)
        }
    
        def compute_signal_idx(self, features_df):
            """
            Compute the buy and sell signal indices based on the RSI feature from the input dataframe.
    
            This method must be defined to implement the specific decision rules for trading signals.
            Iat utilizes the Relative Strength Index (RSI) to determine buy and sell points by comparing
            the RSI values against predefined thresholds.
    
            Args:
                features_df (pandas.DataFrame): Dataframe containing at least the RSI feature.
    
            Returns:
                tuple of (pandas.Series, pandas.Series): 
                - The first series contains boolean values representing the buy signals (True where the RSI is below the buy threshold).
                - The second series contains boolean values representing the sell signals (True where the RSI is above the sell threshold).
    
            Note:
                The caller must ensure the input dataframe contains the necessary features
                prescribed by the 'features' attribute of the class (especially 'rsi').
            """
            # Get RSI values
            rsi_s = features_df[self.features["rsi"].names("rsi")]
    
            # Compute index of buy and sell signals
            idx_buy = rsi_s < self.buy_threshold
            idx_sell = rsi_s > self.sell_threshold
    
            return idx_buy, idx_sell


<a id="org933efcc"></a>

# Bot Specification


<a id="orgc643419"></a>

### YAML Configuration

To build our bot, we use the following configuration file (called here `bot.yaml`) that specifies
our trading strategy:

    bot:
      name: "mosaic_bot_rsi"
      mode: "btfast"
      bt_buy_on: high
      bt_sell_on: low
      
      ds_trading: &ds_trading
        symbol: "BTC/USDT"
        timeframe: "1h"
        dt_start: "2023-01-01 00:00:00"
        dt_end: "2023-07-01 00:00:00"
        
      decision_model:
        cls: DMRSI
        buy_threshold: 30
        sell_threshold: 70
                
      exchange :
        cls: ExchangeCCXT
        name: binance

-   `bot`: This block specifies the trading bot configuration details.
    -   `name`: Bot name.
    -   `mode`: Operating mode, "btfast" for quick backtesting.
    -   `bt_buy_on` and `bt_sell_on`: Assumptions for buy and sell prices in backtesting.
    -   `ds_trading`: Data source for real-time trading or backtesting.
    -   `decision_model`: Specifies buy and sell thresholds for our RSI based decision model.
    -   `exchange`: Details of the exchange where OHLCV data is retrieved.
        -   `name`: The exchange's name, in this case, Binance.


<a id="org112c14b"></a>

# Executing the bot in backtest mode

Next, create the following Python file `bot.py` to backtest the bot defined in the previous YAML
file.

    import mosaic.trading as mtr
    import yaml
    
    with open("bot.yaml", 'r', encoding="utf-8") as yaml_file:
        bot_config = yaml.load(yaml_file,
                               Loader=yaml.SafeLoader)
        bot_config["bot"].setdefault("cls", "BotTrading")
        bot = mtr.BotTrading.from_dict(bot_config["bot"])
    
    bot.start(
        data_dir=".",
        progress_mode=True,
    )
    
    print(bot)

Launch the bot by running the `python bot.py` command and see the results :

    Buy orders:   0%|                                                            | 0/33 [00:00<?, ?it/s]Buy orders: 100%|█████████████████████████████████████████████████| 33/33 [00:00<00:00, 8043.47it/s]
    Sell orders:   0%|                                                           | 0/33 [00:00<?, ?it/s]Sell orders: 100%|████████████████████████████████████████████████| 33/33 [00:00<00:00, 5995.50it/s]
    Executing orders:   0%|                                                      | 0/66 [00:00<?, ?it/s]Executing orders: 100%|███████████████████████████████████████████| 66/66 [00:00<00:00, 3485.57it/s]
    Bot
        MOSAIC version: 0.0.42
        ID: 59923bb7c7350f3e058f1727978c67b01cbb2e9fea72501a7ab9518e585b085c
        Name: mosaic_bot_rsi
        Symbol: BTC/USDT
        Timeframe: 1h
        Mode: btfast
            Buy on: high
            Sell on: low
    
    Session
        Started at: 2023-11-10 09:17:31.239250+01:00
        Ended at: 2023-11-10 09:17:35.510283+01:00
        Duration: 0:00:04.271033
        OHLCV period: 180 days, 23:00:00 | 2023-01-01 00:00:00+01:00 -> 2023-07-01 00:00:00+02:00
        Current quote price: 30713.99 USDT
        # Open orders: 0
        # Cancelled orders: 0
    
    Exchange
        Name: binance
        Fees:
            Taker: 0.001
            Maker: 0.001
    
    Portfolio
        Time: 2023-06-30 23:00:00+02:00
        Initial quote amount: 1.00
        Quote amount: 0.861
        Base amount: 0.0
        Quote exposed: 0.0
        Quote value: 0.861
        KPI
            Asset performance: 1.83
            Strategy performance: [38;5;1m0.861[0m
            # orders executed: 33 buys | 33 sells
            Mean intertrade duration: 3 days, 1:12:43.636364
            Mean intratrade duration: 2 days, 3:52:43.636364

