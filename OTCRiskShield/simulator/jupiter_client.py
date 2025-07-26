"""
Jupiter API client for fetching real-time price quotes
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from .config import Config

class JupiterClient:
    """Client for interacting with Jupiter API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_token_price(self, token_symbol: str) -> Optional[float]:
        """
        Get current token price in USD using real-time APIs with fallback
        
        Args:
            token_symbol: Token symbol (e.g., 'SOL', 'USDC')
            
        Returns:
            Token price in USD or None if failed
        """
        # Try CryptoCompare API for real-time prices
        try:
            url = "https://min-api.cryptocompare.com/data/price"
            params = {
                "fsym": token_symbol.upper(),
                "tsyms": "USD"
            }
            
            timeout = aiohttp.ClientTimeout(total=3)  # Quick timeout for real-time feel
            async with self.session.get(url, params=params, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    if "USD" in data:
                        price = float(data["USD"])
                        self.logger.info(f"Real-time price for {token_symbol}: ${price:.6f}")
                        return price
        except Exception as e:
            self.logger.warning(f"CryptoCompare API failed for {token_symbol}: {e}")
        
        # Try CoinGecko as backup for real-time data
        try:
            token_id = self.config.get_token_mint(token_symbol)
            if token_id:
                url = f"https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": token_id,
                    "vs_currencies": "usd"
                }
                
                timeout = aiohttp.ClientTimeout(total=3)
                async with self.session.get(url, params=params, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if token_id in data and "usd" in data[token_id]:
                            price = float(data[token_id]["usd"])
                            self.logger.info(f"Real-time price for {token_symbol} from CoinGecko: ${price:.6f}")
                            return price
        except Exception as e:
            self.logger.warning(f"CoinGecko API failed for {token_symbol}: {e}")
        
        # All real-time APIs failed
        self.logger.error(f"All price APIs failed for {token_symbol} - real-time pricing unavailable")
        
        return None
    

    
    async def get_swap_quote(self, input_mint: str, output_mint: str, amount: int) -> Optional[Dict]:
        """
        Get swap quote from Jupiter
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address  
            amount: Amount in smallest token units
            
        Returns:
            Quote data or None if failed
        """
        url = self.config.jupiter_quote_url
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": int(self.config.slippage_tolerance * 10000)
        }
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"Got swap quote: {data}")
                        return data
                    else:
                        self.logger.warning(f"Quote API returned status {response.status}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout getting swap quote (attempt {attempt + 1})")
            except Exception as e:
                self.logger.error(f"Error getting swap quote: {e}")
            
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
        
        self.logger.error(f"Failed to get swap quote after {self.config.max_retries} attempts")
        return None
    
    async def monitor_price_changes(self, token_symbol: str, duration: float) -> Tuple[float, float, list]:
        """
        Monitor price changes over a duration
        
        Args:
            token_symbol: Token to monitor
            duration: Duration to monitor in seconds
            
        Returns:
            Tuple of (initial_price, final_price, price_history)
        """
        price_history = []
        start_time = datetime.now()
        
        # Get initial price
        initial_price = await self.get_token_price(token_symbol)
        if initial_price is None:
            raise ValueError(f"Could not get initial price for {token_symbol}")
        
        price_history.append({
            'timestamp': start_time.isoformat(),
            'price': initial_price
        })
        
        self.logger.info(f"Starting price monitoring for {token_symbol} at ${initial_price:.6f}")
        
        # Monitor price changes
        elapsed = 0
        while elapsed < duration:
            await asyncio.sleep(self.config.quote_interval)
            
            current_price = await self.get_token_price(token_symbol)
            if current_price is not None:
                price_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'price': current_price
                })
                
                change_pct = ((current_price - initial_price) / initial_price) * 100
                self.logger.debug(f"Price update: ${current_price:.6f} ({change_pct:+.4f}%)")
            
            elapsed = (datetime.now() - start_time).total_seconds()
        
        # Get final price
        final_price = price_history[-1]['price'] if price_history else initial_price
        
        total_change = ((final_price - initial_price) / initial_price) * 100
        self.logger.info(f"Price monitoring complete: ${initial_price:.6f} -> ${final_price:.6f} ({total_change:+.4f}%)")
        
        return initial_price, final_price, price_history
    
    async def estimate_arbitrage_profit(self, token_symbol: str, amount: float, 
                                      price_before: float, price_after: float) -> float:
        """
        Estimate potential arbitrage profit
        
        Args:
            token_symbol: Token being traded
            amount: Trade amount
            price_before: Price before delay
            price_after: Price after delay
            
        Returns:
            Estimated profit in USD
        """
        # Calculate theoretical profit from price difference
        price_diff = price_after - price_before
        gross_profit = amount * abs(price_diff)
        
        # Subtract estimated costs
        gas_cost_usd = self.config.gas_cost * (await self.get_token_price("SOL") or 100)
        slippage_cost = amount * price_after * self.config.slippage_tolerance
        
        net_profit = max(0, gross_profit - gas_cost_usd - slippage_cost)
        
        self.logger.debug(f"Arbitrage calculation: gross=${gross_profit:.2f}, "
                         f"gas=${gas_cost_usd:.2f}, slippage=${slippage_cost:.2f}, "
                         f"net=${net_profit:.2f}")
        
        return net_profit
