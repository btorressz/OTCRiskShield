"""
MEV (Maximum Extractable Value) profit calculations
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from .config import Config

class MEVCalculator:
    """Calculate potential MEV profits from front-running opportunities"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_calculation: Optional[Dict] = None
    
    async def calculate_mev_profit(self, token_symbol: str, trade_amount: float,
                                 initial_price: float, final_price: float,
                                 jupiter_client) -> float:
        """
        Calculate potential MEV profit from front-running opportunity
        
        Args:
            token_symbol: Token being traded
            trade_amount: Amount of tokens in trade
            initial_price: Price when OTC order placed
            final_price: Price after delay
            jupiter_client: Jupiter API client for additional data
            
        Returns:
            Estimated MEV profit in USD
        """
        try:
            # Calculate basic arbitrage opportunity
            price_diff = final_price - initial_price
            gross_profit = trade_amount * abs(price_diff)
            
            # Get current SOL price for gas cost calculations
            sol_price = await jupiter_client.get_token_price("SOL")
            if sol_price is None:
                sol_price = 100.0  # Fallback SOL price
            
            # Calculate transaction costs
            gas_cost_sol = self.config.gas_cost
            gas_cost_usd = gas_cost_sol * sol_price
            
            # Calculate slippage costs
            slippage_cost = self._calculate_slippage_cost(
                trade_amount, final_price, self.config.slippage_tolerance
            )
            
            # Calculate market impact cost
            market_impact_cost = self._calculate_market_impact(
                trade_amount, initial_price, final_price
            )
            
            # Calculate opportunity cost (time value)
            opportunity_cost = self._calculate_opportunity_cost(
                trade_amount * initial_price, self.config.delay
            )
            
            # Total costs
            total_costs = gas_cost_usd + slippage_cost + market_impact_cost + opportunity_cost
            
            # Net MEV profit
            net_profit = max(0.0, gross_profit - total_costs)
            
            # Store calculation details
            self.last_calculation = {
                'timestamp': datetime.now().isoformat(),
                'token': token_symbol,
                'trade_amount': trade_amount,
                'initial_price': initial_price,
                'final_price': final_price,
                'price_difference': price_diff,
                'price_change_pct': (price_diff / initial_price) * 100,
                'gross_profit': gross_profit,
                'costs': {
                    'gas_cost_sol': gas_cost_sol,
                    'gas_cost_usd': gas_cost_usd,
                    'slippage_cost': slippage_cost,
                    'market_impact_cost': market_impact_cost,
                    'opportunity_cost': opportunity_cost,
                    'total_costs': total_costs
                },
                'net_profit': net_profit,
                'profit_margin_pct': (net_profit / gross_profit) * 100 if gross_profit > 0 else 0,
                'roi_pct': (net_profit / (trade_amount * initial_price)) * 100
            }
            
            if net_profit > 0:
                self.logger.info(f"MEV opportunity: ${net_profit:.2f} profit "
                               f"(ROI: {self.last_calculation['roi_pct']:.2f}%)")
            else:
                self.logger.debug(f"No profitable MEV: costs (${total_costs:.2f}) "
                                f"exceed gross profit (${gross_profit:.2f})")
            
            return net_profit
            
        except Exception as e:
            self.logger.error(f"Error calculating MEV profit: {e}")
            return 0.0
    
    def _calculate_slippage_cost(self, amount: float, price: float, 
                               slippage_tolerance: float) -> float:
        """
        Calculate cost due to slippage
        
        Args:
            amount: Trade amount
            price: Token price
            slippage_tolerance: Expected slippage as decimal
            
        Returns:
            Slippage cost in USD
        """
        trade_value = amount * price
        return trade_value * slippage_tolerance
    
    def _calculate_market_impact(self, amount: float, initial_price: float, 
                               final_price: float) -> float:
        """
        Calculate market impact cost based on trade size
        
        Args:
            amount: Trade amount
            initial_price: Initial token price
            final_price: Final token price
            
        Returns:
            Market impact cost in USD
        """
        trade_value = amount * initial_price
        
        # Market impact increases with trade size
        if trade_value < 10000:
            impact_rate = 0.001  # 0.1%
        elif trade_value < 100000:
            impact_rate = 0.003  # 0.3%
        elif trade_value < 500000:
            impact_rate = 0.007  # 0.7%
        else:
            impact_rate = 0.015  # 1.5%
        
        return trade_value * impact_rate
    
    def _calculate_opportunity_cost(self, trade_value: float, delay_seconds: float) -> float:
        """
        Calculate opportunity cost for capital being locked up
        
        Args:
            trade_value: Value of trade in USD
            delay_seconds: Delay time in seconds
            
        Returns:
            Opportunity cost in USD
        """
        # Assume 5% annual opportunity cost (DeFi yield)
        annual_rate = 0.05
        seconds_per_year = 365 * 24 * 3600
        
        opportunity_cost = trade_value * annual_rate * (delay_seconds / seconds_per_year)
        return opportunity_cost
    
    def calculate_break_even_threshold(self, trade_amount: float, 
                                     initial_price: float) -> float:
        """
        Calculate minimum price change needed for profitable MEV
        
        Args:
            trade_amount: Trade amount
            initial_price: Initial token price
            
        Returns:
            Break-even price change as percentage
        """
        trade_value = trade_amount * initial_price
        
        # Estimate total costs
        gas_cost_usd = self.config.gas_cost * 100  # Assume $100 SOL
        slippage_cost = trade_value * self.config.slippage_tolerance
        market_impact_cost = self._calculate_market_impact(
            trade_amount, initial_price, initial_price
        )
        opportunity_cost = self._calculate_opportunity_cost(trade_value, self.config.delay)
        
        total_costs = gas_cost_usd + slippage_cost + market_impact_cost + opportunity_cost
        
        # Required price change to cover costs
        required_price_change = total_costs / trade_amount
        break_even_pct = (required_price_change / initial_price) * 100
        
        return break_even_pct
    
    def analyze_mev_distribution(self, mev_profits: list) -> Dict:
        """
        Analyze distribution of MEV profits across multiple simulations
        
        Args:
            mev_profits: List of MEV profit values
            
        Returns:
            Statistical analysis of MEV distribution
        """
        if not mev_profits:
            return {'error': 'No MEV data to analyze'}
        
        profitable_mevs = [p for p in mev_profits if p > 0]
        
        analysis = {
            'total_opportunities': len(mev_profits),
            'profitable_opportunities': len(profitable_mevs),
            'profitability_rate': len(profitable_mevs) / len(mev_profits) * 100,
            'total_mev': sum(mev_profits),
            'total_profitable_mev': sum(profitable_mevs),
            'statistics': {
                'min': min(mev_profits),
                'max': max(mev_profits),
                'average': sum(mev_profits) / len(mev_profits),
                'median': sorted(mev_profits)[len(mev_profits) // 2]
            }
        }
        
        if profitable_mevs:
            analysis['profitable_statistics'] = {
                'min': min(profitable_mevs),
                'max': max(profitable_mevs),
                'average': sum(profitable_mevs) / len(profitable_mevs),
                'median': sorted(profitable_mevs)[len(profitable_mevs) // 2]
            }
        
        return analysis
    
    def get_calculation_details(self) -> Optional[Dict]:
        """Get details from the last MEV calculation"""
        return self.last_calculation
    
    def estimate_front_runner_advantage(self, initial_price: float, final_price: float,
                                      trade_amount: float) -> Dict:
        """
        Estimate advantage a front-runner would have
        
        Args:
            initial_price: Price when OTC order placed
            final_price: Price after delay
            trade_amount: Size of original trade
            
        Returns:
            Analysis of front-runner advantage
        """
        price_change = final_price - initial_price
        
        # Front-runner could buy before price increase or sell before decrease
        if price_change > 0:
            # Price increased - front-runner buys early, sells high
            strategy = "buy_early_sell_high"
            advantage = trade_amount * price_change
        else:
            # Price decreased - front-runner sells early, buys low
            strategy = "sell_early_buy_low"
            advantage = trade_amount * abs(price_change)
        
        return {
            'strategy': strategy,
            'price_change': price_change,
            'gross_advantage': advantage,
            'advantage_pct': (advantage / (trade_amount * initial_price)) * 100,
            'description': self._get_strategy_description(strategy, price_change)
        }
    
    def _get_strategy_description(self, strategy: str, price_change: float) -> str:
        """Get human-readable description of front-running strategy"""
        if strategy == "buy_early_sell_high":
            return f"Front-runner could buy before {price_change:.4f} price increase"
        else:
            return f"Front-runner could sell before {abs(price_change):.4f} price decrease"
