"""
Configuration management for OTC simulator
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration class for OTC simulator"""
    
    # Trade parameters
    token: str = "SOL"
    amount: float = 100.0
    delay: float = 2.0  # Block delay in seconds
    
    # Risk detection parameters  
    threshold: float = 0.01  # 1% price change threshold
    
    # Simulation parameters
    iterations: int = 1
    verbose: bool = False
    
    # API configuration
    jupiter_api_url: str = "https://price.jup.ag/v6"
    jupiter_quote_url: str = "https://quote-api.jup.ag/v6/quote"
    
    # Timing parameters
    quote_interval: float = 0.5  # Seconds between price checks
    max_retries: int = 3
    request_timeout: float = 10.0
    
    # MEV calculation parameters
    gas_cost: float = 0.005  # Estimated transaction cost in SOL
    slippage_tolerance: float = 0.005  # 0.5% slippage tolerance
    
    # Token mint addresses (Solana mainnet)
    token_mints: dict = None
    
    # Enhanced features configuration
    enable_alerts: bool = True  # Real-time price alerts
    alert_threshold: float = 0.02  # 2% alert threshold
    custom_delay_periods: list = None  # Custom delay periods to test
    batch_tokens: list = None  # Multiple tokens for batch simulation
    historical_tracking: bool = True  # Track historical patterns
    volatility_window: int = 24  # Hours for volatility tracking
    advanced_risk_scoring: bool = True  # Enhanced risk algorithms
    
    def __post_init__(self):
        """Initialize default token mints if not provided"""
        if self.token_mints is None:
            self.token_mints = {
                "SOL": "So11111111111111111111111111111111111111112",
                "BTC": "bitcoin",  # CoinGecko ID
                "ETH": "ethereum",  # CoinGecko ID  
                "USDC": "usd-coin",  # CoinGecko ID
                "USDT": "tether",  # CoinGecko ID
                "BNB": "binancecoin",  # CoinGecko ID
                "ADA": "cardano",  # CoinGecko ID
                "MATIC": "polygon",  # CoinGecko ID
                "AVAX": "avalanche-2",  # CoinGecko ID
                "DOT": "polkadot",  # CoinGecko ID
                "LINK": "chainlink",  # CoinGecko ID
                "UNI": "uniswap",  # CoinGecko ID
                "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
                "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
                "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
                "MNGO": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac"
            }
        
        # Initialize new enhanced features
        if self.custom_delay_periods is None:
            self.custom_delay_periods = [1.0, 2.0, 3.0, 5.0, 10.0]  # Default delay periods
        
        if self.batch_tokens is None:
            self.batch_tokens = ["SOL", "BTC", "ETH", "USDC"]  # Default batch tokens
    
    def get_token_mint(self, token_symbol: str) -> Optional[str]:
        """Get token mint address by symbol"""
        return self.token_mints.get(token_symbol.upper())
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.delay < 0:
            raise ValueError("Delay cannot be negative")
        
        if self.threshold <= 0 or self.threshold > 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        if self.iterations <= 0:
            raise ValueError("Iterations must be positive")
        
        if not self.get_token_mint(self.token):
            raise ValueError(f"Unsupported token: {self.token}")
        
        return True
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls(
            token=os.getenv("OTC_TOKEN", "SOL"),
            amount=float(os.getenv("OTC_AMOUNT", "100.0")),
            delay=float(os.getenv("OTC_DELAY", "2.0")),
            threshold=float(os.getenv("OTC_THRESHOLD", "0.01")),
            iterations=int(os.getenv("OTC_ITERATIONS", "1")),
            verbose=os.getenv("OTC_VERBOSE", "false").lower() == "true"
        )
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return (f"Config(token={self.token}, amount={self.amount}, "
                f"delay={self.delay}s, threshold={self.threshold*100:.1f}%, "
                f"iterations={self.iterations})")
