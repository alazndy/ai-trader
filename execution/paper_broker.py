from utils.logger import setup_logger
from execution.risk_manager import RiskManager
import pandas as pd

logger = setup_logger("Paper_Broker")

class PaperBroker:
    def __init__(self, start_balance=1000.0, commission=0.001, slippage=0.001):
        self.balance = start_balance
        self.initial_balance = start_balance
        self.commission = commission
        self.slippage = slippage
        self.positions = {} # {ticker: {amount, entry_price}}
        self.risk_manager = RiskManager()
        self.trade_log = []
        self.logger = logger

    def log_trade(self, date, action, ticker, price, amount, cost):
        self.trade_log.append({
            'date': date,
            'action': action,
            'ticker': ticker,
            'price': price,
            'amount': amount,
            'cost': cost,
            'balance': self.balance
        })

    def buy(self, ticker, price, date, pct_portfolio=None):
        """
        Buy shares. 
        If pct_portfolio is None, it divides balance by remaining slots?
        Simpler approach: pct_portfolio defaults to 1.0 / len(Active_Tickers) externally, 
        or we handle it here.
        Let's assume the caller handles the sizing strategy or we default to a safe 20%.
        """
        # 1. Apply Slippage (Real execution price)
        exec_price = self.risk_manager.apply_slippage(price, 'buy')
        
        # 2. Determine Budget
        # If pct_portfolio is not provided, we assume we want to invest 
        # a fixed chunk. For now, let's trust the passed pct argument or use available cash.
        if pct_portfolio is None:
             # Default to utilizing 20% of CURRENT total equity? 
             # Or just use "Available Cash" if it's less than that?
             # Let's use simpler logic: 
             # Budget = Current Cash (Balance)  (Aggressive)
             # But if we have 5 tickers, we should only use 1/5th.
             budget = self.balance # This is dangerous if loop runs 5 times fast.
             # Better logic needs to be passed in.
             pass 
        else:
            budget = self.initial_balance * pct_portfolio 
            # Note: We use initial_balance to keep position sizes consistent 
            # even if we lose money, or we can use current equity.
            # Safety: Cap budget to current balance.
            budget = min(budget, self.balance)

        if budget < 100: # Minimum trade check (100 TL)
            return False

        # 3. Calculate Max Amount (considering commission)
        # Cost = Amount * Price + (Amount * Price * Comm)
        # Budget = Amount * Price * (1 + Comm)
        # Amount = Budget / (Price * (1 + Comm))
        max_amount = int(budget / (exec_price * (1 + self.risk_manager.commission_rate)))
        
        if max_amount < 1:
            return False

        # 4. Execute
        cost = self.risk_manager.calculate_cost(max_amount, exec_price)
        total_deduction = (max_amount * exec_price) + cost
        
        self.balance -= total_deduction
        
        # Positions: {ticker: {'amount': 100, 'entry_price': 10.50}}
        current_pos = self.positions.get(ticker, {'amount': 0, 'entry_price': 0.0})
        old_amount = current_pos['amount']
        old_entry = current_pos['entry_price']
        
        # Calculate Weighted Average Price
        new_amount = old_amount + max_amount
        if new_amount > 0:
            avg_price = ((old_amount * old_entry) + (max_amount * exec_price)) / new_amount
        else:
            avg_price = exec_price
            
        self.positions[ticker] = {'amount': new_amount, 'entry_price': avg_price}
        
        self.log_trade(date, 'BUY', ticker, exec_price, max_amount, cost)
        logger.info(f"BUY {ticker}: {max_amount} units @ {exec_price:.2f} (Entry: {avg_price:.2f})")
        # Update Position
        if ticker in self.positions:
            pos = self.positions[ticker]
            # Weighted Average Price
            total_qty = pos['amount'] + quantity
            avg_entry = ((pos['amount'] * pos['entry_price']) + (quantity * exec_price)) / total_qty
            pos['amount'] = total_qty
            pos['entry_price'] = avg_entry
        else:
            self.positions[ticker] = {'amount': quantity, 'entry_price': exec_price}
            
        # Log
        self.log_trade(timestamp, 'BUY', ticker, exec_price, quantity, commission_fee, context)
        self.logger.info(f"BUY {ticker}: {quantity:.4f} units @ {exec_price:.2f} | Context: {context}")
        return True

    def sell(self, ticker, price, timestamp, amount=None, pct_portfolio=1.0, context=None):
        """
        Executes a SELL order.
        """
        if ticker not in self.positions: return False
        
        pos = self.positions[ticker]
        available_qty = pos['amount']
        
        if amount:
            quantity = min(amount, available_qty)
        else:
            quantity = available_qty * pct_portfolio
            
        if quantity <= 0: return False

        # Apply Slippage (Sell lower)
        exec_price = self.risk_manager.apply_slippage(price, 'sell')
        
        gross_revenue = quantity * exec_price
        commission_fee = gross_revenue * self.commission
        net_income = gross_revenue - commission_fee
        
        self.balance += net_income
        
        # Update Position
        pos['amount'] -= quantity
        if pos['amount'] < 1e-6: # Dust cleanup
            del self.positions[ticker]
            
        # Log
        realized_pnl = (exec_price - pos['entry_price']) * quantity if ticker in self.positions else (exec_price - pos['entry_price']) * quantity # If position is closed, entry price is from the closed position
        self.log_trade(timestamp, 'SELL', ticker, exec_price, quantity, commission_fee, context)
        self.logger.info(f"SELL {ticker}: {quantity:.4f} units @ {exec_price:.2f} (PnL: {realized_pnl:.2f}) | Context: {context}")
        return True

    def get_portfolio_value(self, current_price_map):
        """
        Calculates Total Equity = Cash + Stock Value
        current_price_map: {ticker: price}
        """
        equity = self.balance
        for ticker, pos_data in self.positions.items():
            # Handle new structure vs old
            if isinstance(pos_data, dict):
                amount = pos_data['amount']
            else:
                amount = pos_data
                
            if amount > 0:
                price = current_price_map.get(ticker, 0)
                equity += amount * price
        return equity

    def get_position_amt(self, ticker):
        """Helper to safely get amount for a ticker."""
        data = self.positions.get(ticker, {'amount': 0})
        return data['amount'] if isinstance(data, dict) else data
    
    def get_report(self):
        return pd.DataFrame(self.trade_log)

    # --- Persistence Logic ---
    def save_state(self, filepath="data/wallet.json"):
        """Saves current balance and positions to JSON."""
        import json
        state = {
            "balance": self.balance,
            "positions": self.positions,
            "trade_log": self.trade_log
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(state, f, default=str) # default=str for dates
            logger.info("Wallet state saved.")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_state(self, filepath="data/wallet.json"):
        """Loads balance and positions from JSON."""
        import json
        import os
        if not os.path.exists(filepath):
            logger.warning("No wallet state found. Starting fresh.")
            return

        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.balance = state.get("balance", self.balance)
            self.positions = state.get("positions", {})
            self.trade_log = state.get("trade_log", [])
            logger.info(f"Wallet loaded. Balance: {self.balance:.2f}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    # --- Safety Logic ---
    def check_portfolio_safety(self, current_price_map, stop_loss_pct=0.03):
        """
        Checks all positions against Stop-Loss threshold.
        Returns list of tickers to SELL immediately.
        """
        sell_list = []
        for ticker, pos_data in self.positions.items():
            if isinstance(pos_data, dict):
                amount = pos_data['amount']
                entry = pos_data['entry_price']
            else:
                # Legacy or error
                continue
                
            if amount > 0 and entry > 0:
                cur_price = current_price_map.get(ticker)
                if cur_price and self.risk_manager.check_stop_loss(cur_price, entry, stop_loss_pct):
                    logger.warning(f"STOP LOSS TRIPPED: {ticker} (Entry: {entry:.2f}, Current: {cur_price:.2f})")
                    sell_list.append(ticker)
        return sell_list

    # --- Core-Satellite Logic ---
    def rebalance_vault(self, current_price_map, safe_ticker, target_pct=0.50):
        """
        Ensures that 'target_pct' of Total Equity is held in 'safe_ticker'.
        Only Buys/Sells if deviation is significant (> 5%) to avoid churn.
        """
        if safe_ticker not in current_price_map:
            logger.warning(f"Vault: No price data for {safe_ticker}. Skipping rebalance.")
            return

        safe_price = current_price_map[safe_ticker]
        total_equity = self.get_portfolio_value(current_price_map)
        
        # Current Holdings
        pos_data = self.positions.get(safe_ticker, {'amount': 0})
        current_amount = pos_data['amount'] if isinstance(pos_data, dict) else pos_data
        current_val = current_amount * safe_price
        
        target_val = total_equity * target_pct
        diff_val = target_val - current_val
        diff_pct = diff_val / total_equity
        
        # Threshold: Rebalance only if off by 5%
        if abs(diff_pct) < 0.05:
            return

        if diff_val > 0:
            # Need to BUY Safe Asset (Underweight)
            # Rebalance only if deviation > 5% (Buffer to prevent churn)
            if diff_pct < 0.05: 
                return

            to_buy_tl = min(diff_val, self.balance)
            if to_buy_tl > (safe_price * 1):
                logger.info(f"VAULT: Rebalancing. Buying {to_buy_tl:.2f} TL of {safe_ticker}")
                self.execute_vault_buy(safe_ticker, safe_price, to_buy_tl, "VAULT_REBALANCE")
        
        elif diff_val < 0:
            # Need to SELL Safe Asset (Overweight)
            # Usually we don't sell 'Safe' unless we need cash or it grew too much?
            # For "Kasa" logic, we might just keep it.
            # But true Core-Satellite rebalances BOTH ways.
            if abs(diff_pct) > 0.10: # Only sell if WAY overweight (10%)
                to_sell_tl = abs(diff_val)
                # Logic to sell specific amount...
                # For MVP, let's Stick to "Accumulate Vault" mode. 
                # We don't sell Gold to buy Volatile stocks automatically yet.
                pass
        
    def execute_vault_buy(self, ticker, price, amount_tl, date):
        """Direct buy helper for Vault Ops (Amount in TL)"""
        if amount_tl > self.balance:
            amount_tl = self.balance
            
        exec_price = self.risk_manager.apply_slippage(price, 'buy')
        max_amount = int(amount_tl / (exec_price * (1 + self.risk_manager.commission_rate)))
        
        if max_amount > 0:
             cost = self.risk_manager.calculate_cost(max_amount, exec_price)
             self.balance -= ((max_amount * exec_price) + cost)
             
             # Position Update
             curr = self.positions.get(ticker, {'amount': 0, 'entry_price': 0.0})
             old_amt = curr['amount']
             old_ent = curr['entry_price']
             new_amt = old_amt + max_amount
             
             if new_amt > 0:
                 avg = ((old_amt * old_ent) + (max_amount * exec_price)) / new_amt
             else:
                 avg = exec_price
                 
             self.positions[ticker] = {'amount': new_amt, 'entry_price': avg}
             logger.info(f"VAULT BUY: {ticker} +{max_amount} units @ {exec_price:.2f}")


