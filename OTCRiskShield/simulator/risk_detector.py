"""
Risk detection algorithms for front-running analysis
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .config import Config

class RiskDetector:
    """Detects front-running risks based on price movements"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_analysis: Optional[Dict] = None
    
    def detect_risk(self, initial_price: float, final_price: float, 
                   trade_amount: float) -> bool:
        """
        Detect if a trade is at risk of front-running
        
        Args:
            initial_price: Price when OTC order was placed
            final_price: Price after delay period
            trade_amount: Size of the trade
            
        Returns:
            True if risk detected, False otherwise
        """
        # Calculate price change percentage
        price_change = (final_price - initial_price) / initial_price
        price_change_pct = abs(price_change) * 100
        
        # Basic threshold check
        threshold_exceeded = abs(price_change) > self.config.threshold
        
        # Calculate trade impact factors
        trade_value = trade_amount * initial_price
        impact_factor = self._calculate_impact_factor(trade_value)
        
        # Directional risk (price moved against the trade)
        directional_risk = self._assess_directional_risk(price_change, trade_amount)
        
        # Volume-adjusted risk
        volume_risk = self._assess_volume_risk(trade_amount, initial_price)
        
        # Combined risk score
        risk_score = self._calculate_risk_score(
            price_change, impact_factor, directional_risk, volume_risk
        )
        
        # Store analysis details
        self.last_analysis = {
            'timestamp': datetime.now().isoformat(),
            'initial_price': initial_price,
            'final_price': final_price,
            'price_change_pct': price_change_pct,
            'threshold_pct': self.config.threshold * 100,
            'threshold_exceeded': threshold_exceeded,
            'trade_amount': trade_amount,
            'trade_value': trade_value,
            'impact_factor': impact_factor,
            'directional_risk': directional_risk,
            'volume_risk': volume_risk,
            'risk_score': risk_score,
            'risk_detected': risk_score > 0.5  # Risk threshold
        }
        
        risk_detected = self.last_analysis['risk_detected']
        
        if risk_detected:
            self.logger.warning(f"RISK DETECTED: Price change {price_change_pct:.4f}% "
                              f"exceeds threshold {self.config.threshold * 100:.2f}%, "
                              f"Risk score: {risk_score:.3f}")
        else:
            self.logger.debug(f"No risk: Price change {price_change_pct:.4f}%, "
                            f"Risk score: {risk_score:.3f}")
        
        return risk_detected
    
    def _calculate_impact_factor(self, trade_value: float) -> float:
        """
        Calculate impact factor based on trade size
        Larger trades have higher impact and risk
        """
        # Define trade size categories (in USD)
        if trade_value < 1000:
            return 0.1  # Small trade
        elif trade_value < 10000:
            return 0.3  # Medium trade
        elif trade_value < 100000:
            return 0.6  # Large trade
        else:
            return 1.0  # Very large trade
    
    def _assess_directional_risk(self, price_change: float, trade_amount: float) -> float:
        """
        Assess risk based on price direction relative to trade
        Assumes we're analyzing potential sell pressure
        """
        if price_change < 0:
            # Price dropped - higher risk for sellers
            return min(1.0, abs(price_change) / self.config.threshold)
        else:
            # Price increased - lower risk for sellers
            return max(0.0, price_change / (self.config.threshold * 2))
    
    def _assess_volume_risk(self, trade_amount: float, price: float) -> float:
        """
        Assess risk based on trade volume
        """
        trade_value = trade_amount * price
        
        # Risk increases with trade size
        if trade_value < 10000:
            return 0.2
        elif trade_value < 50000:
            return 0.4
        elif trade_value < 200000:
            return 0.7
        else:
            return 1.0
    
    def _calculate_risk_score(self, price_change: float, impact_factor: float,
                            directional_risk: float, volume_risk: float) -> float:
        """
        Calculate combined risk score (0.0 to 1.0)
        """
        # Normalize price change component
        price_component = min(1.0, abs(price_change) / self.config.threshold)
        
        # Weighted combination of risk factors
        risk_score = (
            price_component * 0.4 +      # Price change weight: 40%
            impact_factor * 0.2 +        # Impact factor weight: 20%
            directional_risk * 0.25 +    # Directional risk weight: 25%
            volume_risk * 0.15           # Volume risk weight: 15%
        )
        
        return min(1.0, risk_score)
    
    def get_risk_details(self) -> Optional[Dict]:
        """Get details from the last risk analysis"""
        return self.last_analysis
    
    def analyze_price_history(self, price_history: List[Dict]) -> Dict:
        """
        Analyze price movement patterns in history
        
        Args:
            price_history: List of price data points with timestamp and price
            
        Returns:
            Analysis of price patterns
        """
        if len(price_history) < 2:
            return {'error': 'Insufficient price data'}
        
        prices = [p['price'] for p in price_history]
        
        # Calculate price volatility
        price_changes = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1]
            price_changes.append(change)
        
        volatility = self._calculate_volatility(price_changes)
        
        # Detect trends
        trend = self._detect_trend(prices)
        
        # Find maximum price movement
        max_price = max(prices)
        min_price = min(prices)
        max_movement = (max_price - min_price) / prices[0]
        
        analysis = {
            'total_data_points': len(price_history),
            'price_range': {
                'min': min_price,
                'max': max_price,
                'initial': prices[0],
                'final': prices[-1]
            },
            'volatility': volatility,
            'max_movement_pct': max_movement * 100,
            'trend': trend,
            'risk_periods': self._identify_risk_periods(price_history)
        }
        
        return analysis
    
    def _calculate_volatility(self, changes: List[float]) -> float:
        """Calculate volatility from price changes"""
        if not changes:
            return 0.0
        
        mean = sum(changes) / len(changes)
        variance = sum((x - mean) ** 2 for x in changes) / len(changes)
        return variance ** 0.5
    
    def _detect_trend(self, prices: List[float]) -> str:
        """Detect overall price trend"""
        if len(prices) < 2:
            return 'insufficient_data'
        
        start_price = prices[0]
        end_price = prices[-1]
        change = (end_price - start_price) / start_price
        
        if change > 0.005:  # 0.5% threshold
            return 'upward'
        elif change < -0.005:
            return 'downward'
        else:
            return 'sideways'
    
    def _identify_risk_periods(self, price_history: List[Dict]) -> List[Dict]:
        """Identify periods with high risk of front-running"""
        risk_periods = []
        
        for i in range(1, len(price_history)):
            prev_price = price_history[i-1]['price']
            curr_price = price_history[i]['price']
            
            change = abs((curr_price - prev_price) / prev_price)
            
            if change > self.config.threshold:
                risk_periods.append({
                    'start_time': price_history[i-1]['timestamp'],
                    'end_time': price_history[i]['timestamp'],
                    'price_change_pct': change * 100,
                    'direction': 'up' if curr_price > prev_price else 'down'
                })
        
        return risk_periods
