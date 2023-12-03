
import pandas as pd
import numpy as np
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


########## Mésure de performance ###################################

def drawdown_max(returns_cumulative):
    """Calcule le drawdown maximum et sa durée pour une série de rendements cumulés"""

    # Calcule les niveaux des plus hauts sommets atteints
    peaks = np.maximum.accumulate(returns_cumulative)
    # Calcule la différence entre les plus hauts sommets et les niveaux courants
    drawdown = peaks - returns_cumulative
    drawdown_max = drawdown.max()
    strat_dd = drawdown[drawdown == 0]
    strat_dd_diff = strat_dd.index[1:] - strat_dd.index[:-1]
    # Durée du drawdown maximum en termes de timedelta
    strat_dd_duration = strat_dd_diff.max()
    # Date de début du drawdown maximum
    drawdown_start = strat_dd.index[strat_dd_diff.argmax()]
    # Date de fin du drawdown maximum
    drawdown_end = strat_dd.index[strat_dd_diff.argmax() + 1]
    dd_durations = drawdown_end - drawdown_start

    return drawdown_max, dd_durations


############# Calcul de valeur de portfeuille ###############

def calculer_valeurs_portefeuille(df, investissement_initial):
    portefeuille = investissement_initial

    for _, row in df.iterrows():
        portefeuille *= (1 + row['returns'])

    return portefeuille
##################################################################### backtest_strategy_long #######################################################################


class Backtest:
    def __init__(self, data_df, buy_hold_min_time=1, var_buy_on=None, var_sell_on=None,
                 initial_cash=10000, transaction_cost=None):
        self.data_df = data_df
        self.buy_hold_min_time = buy_hold_min_time
        self.var_buy_on = var_buy_on
        self.var_sell_on = var_sell_on  # Nouveau: variable pour les ordres de vente
        self.initial_cash = initial_cash
        self.transaction_cost = transaction_cost if transaction_cost is not None else 0
        
        if self.var_buy_on not in self.data_df.columns:
            raise ValueError(f"Variable {self.var_buy_on} not found in data_df")

        if self.var_sell_on not in self.data_df.columns:
            raise ValueError(f"Variable {self.var_sell_on} not found in data_df")

        self.bt_results = None
        self.bt_eval_indic = None
        self.bt_eval_raw = None
        self.bt_results = None
        self.bt_eval_indic = None
        self.bt_eval_raw = None
    
        
    def drawdown_max(self):
        """Calcule le drawdown maximum et sa durée pour une série de rendements cumulés"""
        if not hasattr(self, 'bt_eval_raw') or "ret_strat_t" not in self.bt_eval_raw:
            raise ValueError("bt_eval_raw['ret_strat_t'] not available. Run backtest_eval() first.")

        returns_cumulative = self.bt_eval_raw["ret_strat_t"]

        # Calcule les niveaux des plus hauts sommets atteints
        peaks = np.maximum.accumulate(returns_cumulative)
        # Calcule la différence entre les plus hauts sommets et les niveaux courants
        drawdown = peaks - returns_cumulative
        drawdown_max = drawdown.max()
        strat_dd = drawdown[drawdown == 0]
        strat_dd_diff = strat_dd.index[1:] - strat_dd.index[:-1]
        # Durée du drawdown maximum en termes de timedelta
        strat_dd_duration = strat_dd_diff.max()
        # Date de début du drawdown maximum
        drawdown_start = strat_dd.index[strat_dd_diff.argmax()]
        # Date de fin du drawdown maximum
        drawdown_end = strat_dd.index[strat_dd_diff.argmax() + 1]
        dd_durations = drawdown_end - drawdown_start

        return drawdown_max, dd_durations
    
    def calculate_exposure(self):
        if not hasattr(self, 'bt_results') or "orders_raw" not in self.bt_results or "orders_df" not in self.bt_results:
            raise ValueError("bt_results not available. Run backtest_strategy_long() first.")

        total_period_duration = self.bt_results["orders_raw"].index[-1] - self.bt_results["orders_raw"].index[0]
        invested_duration = self.bt_results["orders_df"]["trade_duration"].sum()
        exposure_percentage = (invested_duration / total_period_duration) * 100
        return exposure_percentage
    
    def calculate_profit_factor(self):
        if not hasattr(self, 'bt_results') or "orders_df" not in self.bt_results:
            raise ValueError("bt_results not available. Run backtest_strategy_long() first.")

        total_profit = self.bt_results["orders_df"]["returns"].loc[self.bt_results["orders_df"]["returns"] > 0].sum()
        total_loss = self.bt_results["orders_df"]["returns"].loc[self.bt_results["orders_df"]["returns"] < 0].sum()
        profit_factor = abs(total_profit / total_loss)
        return profit_factor


    def backtest_strategy_long(self, strategy_fun, var_buy_on=None, var_sell_on=None,**strategy_parameters):
        var_buy_on = var_buy_on if var_buy_on is not None else self.var_buy_on
        var_sell_on = var_sell_on if var_sell_on is not None else self.var_sell_on
        order_value_s = strategy_fun.execute(self.data_df)      
        order_value_const = order_value_s.fillna(0).rolling(self.buy_hold_min_time).max()
        idx_na = order_value_s.isnull()
        order_value_const.loc[idx_na] = np.nan
        order_value_final_s = order_value_const.fillna(method="ffill").fillna(0)
        orders_dt = order_value_final_s.loc[order_value_final_s.shift() != order_value_final_s]
        
        if orders_dt.iloc[0] == 0:
            orders_dt = orders_dt.iloc[1:]

        var_buy_price = self.var_buy_on
        var_sell_price = self.var_sell_on  # Nouveau: variable pour les ordres de vente
        
        idx_buy = orders_dt.index[orders_dt == 1] 
        buy_price = self.data_df[var_buy_price].loc[idx_buy]
        buy_price_df = buy_price.reset_index().rename(columns={"time": "buy_time", var_buy_price: "buy_price"})

        idx_sell = orders_dt.index[orders_dt != 1]
        sell_price = self.data_df[var_sell_price].loc[idx_sell]
        sell_price_df = sell_price.reset_index().rename(columns={"time": "sell_time", var_sell_price: "sell_price"})
        
        orders_df = pd.concat([buy_price_df, sell_price_df], axis=1).dropna()

        if not orders_dt.empty and  orders_dt.iloc[-1] == 1:
           # Récupérer la dernière date de votre DataFrame ohlcv_df
           last_date = self.data_df.index[-1]

          # Ajouter une entrée de vente (0) dans la série orders_dt à cette dernière date
           orders_dt.loc[last_date] = 0
           
           # Obtenez le temps et le prix d'achat de la dernière transaction d'achat
           last_buy_time = orders_dt.index[orders_dt == 1][-1]
           last_buy_price = self.data_df[var_buy_price].loc[last_buy_time]
         # S'il y a un achat sans vente correspondante, créez une vente forcée
           last_sell_price = self.data_df[var_sell_price].iloc[-1]  # Prix de clôture de la dernière période
           last_sell_time = self.data_df.index[-1]  # Temps de la dernière période
    
         # Créez une ligne de données pour la vente forcée
           forced_sell = pd.DataFrame({
        'buy_time': [last_buy_time],
        'buy_price': [last_buy_price],
        'sell_time': [last_sell_time],
        'sell_price': [last_sell_price] 
        })

          # Ajoutez la vente forcée à votre DataFrame d'ordres
           orders_df = pd.concat([orders_df, forced_sell]).reset_index(drop=True)

        else: 
            pass
        orders_df["inter_trade_duration"] =orders_df["buy_time"] - orders_df["sell_time"].shift(1)
        orders_df["trade_duration"] = orders_df["sell_time"] - orders_df["buy_time"]
        orders_df["returns"] = (orders_df["sell_price"] - orders_df["buy_price"]) / orders_df["buy_price"]
        
        cash_balance = self.initial_cash
        asset_holding = 0
        cash_balances = [cash_balance]

        for i, row in orders_df.iterrows():
            asset_holding = (cash_balance / (row['buy_price'] * (1 + self.transaction_cost)))
            cash_balance = (cash_balance - (row['buy_price'] * asset_holding * (1 + self.transaction_cost)))
            cash_balance = (cash_balance + (row['sell_price'] * asset_holding * (1 - self.transaction_cost)))
            asset_holding = 0
            cash_balances.append(cash_balance)

        orders_df['cash_balance'] = cash_balances[1:]
        final_asset_value = asset_holding * self.data_df[var_buy_price].iloc[-1]
        final_total_balance = cash_balance + final_asset_value
        
        self.bt_results = {
            "var_buy_on": self.var_buy_on,
            "var_sell_on": var_sell_on,
            "orders_raw": order_value_final_s,
            "orders_df": orders_df,
            "final_total_balance": final_total_balance,
             "orders_signal":orders_dt,
        }
        
        return self.bt_results 
    
    def backtest_eval(self):
        
        bt_eval_indic = {}
        bt_eval_raw = {}
        var_price ='close'
        
        
        
        bt_eval_raw["ret_asset_single"] = self.data_df[var_price].pct_change(1).shift(-1).fillna(0)
        bt_eval_indic["ret_asset_period"] = self.data_df[var_price].iloc[-1] / self.data_df[var_price].iloc[0] - 1
        ret1_log = np.log(bt_eval_raw["ret_asset_single"] + 1)
        ret1_log_strat = (ret1_log * self.bt_results["orders_raw"]).dropna()
        ret1_log_strat_orders = np.log(self.bt_results["orders_df"]["returns"] + 1)
        
        bt_eval_raw["ret_strat_t"] = np.exp(ret1_log_strat.cumsum()) - 1
        bt_eval_raw["ret_strat_orders"] = pd.Series(np.exp(ret1_log_strat_orders.cumsum()) - 1)
        bt_eval_raw["ret_strat_orders"].index = self.bt_results["orders_df"]["sell_time"]
        bt_eval_raw["ret_strat_orders"].dropna(inplace=True)

        if len(bt_eval_raw["ret_strat_orders"]) > 0:
            bt_eval_indic["gross_ret_strat"] = bt_eval_raw["ret_strat_orders"].iloc[-1]
        else:
            bt_eval_indic["gross_ret_strat"] = 0

        net_ret1_log_strat_orders = ret1_log_strat_orders - (self.transaction_cost * 2)
        bt_eval_raw["net_ret_strat_orders"] = pd.Series(np.exp(net_ret1_log_strat_orders.cumsum()) - 1)
        bt_eval_raw["net_ret_strat_orders"].index = self.bt_results["orders_df"]["sell_time"]
        bt_eval_raw["net_ret_strat_orders"].dropna(inplace=True)

        if len(bt_eval_raw["net_ret_strat_orders"]) > 0:
            bt_eval_indic["net_ret_strat"] = bt_eval_raw["net_ret_strat_orders"].iloc[-1]
        else:
            bt_eval_indic["net_ret_strat"] = 0

        bt_eval_indic["trade_duration_mean"] = self.bt_results["orders_df"]["trade_duration"].mean()
        bt_eval_indic["inter_trade_duration_mean"] = (self.bt_results["orders_df"]["buy_time"] - self.bt_results["orders_df"]["sell_time"].shift(1)).mean()
        bt_eval_indic["N_trade"] = len(self.bt_results["orders_df"])
        bt_eval_raw["trade_duration"]=self.bt_results["orders_df"]["trade_duration"]
        #bt_eval_indic["draw_max"] = drawdown_max(bt_eval_raw["ret_strat_t"])[0]
       
        self.bt_eval_indic = bt_eval_indic
        self.bt_eval_raw = bt_eval_raw
        return self.bt_eval_indic, self.bt_eval_raw
