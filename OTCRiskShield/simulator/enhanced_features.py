"""
Enhanced features for OTC simulator including:
- Historical price analysis
- Real-time price alerts  
- Market volatility tracking
- Advanced risk scoring
- Batch simulations with multiple tokens
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics

from .config import Config
from .logger import setup_logger

@dataclass
class PriceAlert:
    """Price alert configuration"""
    token: str
    threshold: float
    direction: str  # 'up' or 'down'
    triggered: bool = False
    timestamp: Optional[datetime] = None

@dataclass
class HistoricalDataPoint:
    """Historical price data point"""
    timestamp: datetime
    token: str
    price: float
    volume: Optional[float] = None
    volatility: Optional[float] = None

class HistoricalTracker:
    """Tracks historical price patterns and market data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("historical_tracker", config.verbose)
        self.price_history: List[HistoricalDataPoint] = []
        self.volatility_cache = {}
        
    def add_price_data(self, token: str, price: float, volume: Optional[float] = None):
        """Add new price data point"""
        data_point = HistoricalDataPoint(
            timestamp=datetime.now(),
            token=token,
            price=price,
            volume=volume
        )
        self.price_history.append(data_point)
        
        # Keep only data within volatility window
        cutoff_time = datetime.now() - timedelta(hours=self.config.volatility_window)
        self.price_history = [dp for dp in self.price_history if dp.timestamp >= cutoff_time]
        
        self.logger.debug(f"Added price data: {token} @ ${price}")
    
    def calculate_volatility(self, token: str, window_hours: int = None) -> float:
        """Calculate price volatility for a token"""
        if window_hours is None:
            window_hours = self.config.volatility_window
            
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        token_data = [dp for dp in self.price_history 
                     if dp.token == token and dp.timestamp >= cutoff_time]
        
        if len(token_data) < 2:
            return 0.0
            
        prices = [dp.price for dp in token_data]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                  for i in range(1, len(prices))]
        
        if not returns:
            return 0.0
            
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
        self.volatility_cache[token] = volatility
        
        return volatility
    
    def get_price_trend(self, token: str, window_hours: int = 1) -> Dict:
        """Analyze price trend over specified window"""
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        token_data = [dp for dp in self.price_history 
                     if dp.token == token and dp.timestamp >= cutoff_time]
        
        if len(token_data) < 2:
            return {"trend": "insufficient_data", "change": 0.0}
            
        token_data.sort(key=lambda x: x.timestamp)
        initial_price = token_data[0].price
        final_price = token_data[-1].price
        
        price_change = (final_price - initial_price) / initial_price
        
        if price_change > 0.001:  # 0.1% threshold
            trend = "upward"
        elif price_change < -0.001:
            trend = "downward"
        else:
            trend = "stable"
            
        return {
            "trend": trend,
            "change": price_change,
            "initial_price": initial_price,
            "final_price": final_price,
            "data_points": len(token_data)
        }
    
    def detect_market_patterns(self, token: str) -> Dict:
        """Detect market patterns and anomalies"""
        volatility = self.calculate_volatility(token)
        trend = self.get_price_trend(token)
        
        patterns = []
        
        # High volatility pattern
        if volatility > 0.05:  # 5% volatility threshold
            patterns.append("high_volatility")
            
        # Trending pattern
        if abs(trend["change"]) > 0.02:  # 2% change threshold
            patterns.append(f"strong_{trend['trend']}_trend")
            
        # Stability pattern
        if volatility < 0.005 and abs(trend["change"]) < 0.005:
            patterns.append("stable_market")
            
        return {
            "patterns": patterns,
            "volatility": volatility,
            "trend_analysis": trend,
            "risk_level": self._assess_pattern_risk(patterns, volatility)
        }
    
    def _assess_pattern_risk(self, patterns: List[str], volatility: float) -> str:
        """Assess risk level based on detected patterns"""
        if "high_volatility" in patterns or any("strong" in p for p in patterns):
            return "high"
        elif volatility > 0.02:
            return "medium"
        else:
            return "low"

class AlertSystem:
    """Real-time price alert system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("alert_system", config.verbose)
        self.active_alerts: List[PriceAlert] = []
        self.alert_history: List[Dict] = []
        
    def add_alert(self, token: str, threshold: float, direction: str = "both"):
        """Add new price alert"""
        if direction in ["up", "both"]:
            alert = PriceAlert(token=token, threshold=threshold, direction="up")
            self.active_alerts.append(alert)
            
        if direction in ["down", "both"]:
            alert = PriceAlert(token=token, threshold=-threshold, direction="down")
            self.active_alerts.append(alert)
            
        self.logger.info(f"Added alert for {token}: {direction} {threshold*100:.1f}%")
    
    def check_alerts(self, token: str, current_price: float, previous_price: float):
        """Check if any alerts should be triggered"""
        if previous_price == 0:
            return
            
        price_change = (current_price - previous_price) / previous_price
        
        for alert in self.active_alerts:
            if alert.token != token or alert.triggered:
                continue
                
            should_trigger = False
            
            if alert.direction == "up" and price_change >= alert.threshold:
                should_trigger = True
            elif alert.direction == "down" and price_change <= alert.threshold:
                should_trigger = True
                
            if should_trigger:
                self._trigger_alert(alert, current_price, price_change)
    
    def _trigger_alert(self, alert: PriceAlert, price: float, change: float):
        """Trigger an alert"""
        alert.triggered = True
        alert.timestamp = datetime.now()
        
        alert_data = {
            "token": alert.token,
            "direction": alert.direction,
            "threshold": alert.threshold,
            "actual_change": change,
            "price": price,
            "timestamp": alert.timestamp.isoformat(),
            "severity": "high" if abs(change) > 0.05 else "medium"
        }
        
        self.alert_history.append(alert_data)
        self.logger.warning(f"ALERT: {alert.token} {alert.direction} {change*100:.2f}% @ ${price}")
        
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts within specified timeframe"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history 
                if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time]
    
    def reset_alerts(self, token: str = None):
        """Reset triggered alerts"""
        if token:
            for alert in self.active_alerts:
                if alert.token == token:
                    alert.triggered = False
        else:
            for alert in self.active_alerts:
                alert.triggered = False

class AdvancedRiskScorer:
    """Advanced risk scoring algorithms"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("risk_scorer", config.verbose)
        
    def calculate_advanced_risk_score(self, token: str, trade_amount: float, 
                                    price_change: float, volatility: float,
                                    market_patterns: List[str]) -> Dict:
        """Calculate advanced risk score with multiple factors"""
        
        # Base risk from price change
        price_risk = min(abs(price_change) / self.config.threshold, 1.0)
        
        # Volatility risk
        volatility_risk = min(volatility / 0.1, 1.0)  # Normalize to 10% volatility
        
        # Trade size risk
        size_risk = min(trade_amount / 10000, 1.0)  # Normalize to $10k trade
        
        # Pattern-based risk
        pattern_risk = self._calculate_pattern_risk(market_patterns)
        
        # Weighted composite score
        weights = {
            "price": 0.4,
            "volatility": 0.3,
            "size": 0.15,
            "pattern": 0.15
        }
        
        composite_score = (
            price_risk * weights["price"] +
            volatility_risk * weights["volatility"] +
            size_risk * weights["size"] +
            pattern_risk * weights["pattern"]
        )
        
        return {
            "composite_score": composite_score,
            "risk_level": self._score_to_level(composite_score),
            "components": {
                "price_risk": price_risk,
                "volatility_risk": volatility_risk,
                "size_risk": size_risk,
                "pattern_risk": pattern_risk
            },
            "recommendations": self._generate_recommendations(composite_score, market_patterns)
        }
    
    def _calculate_pattern_risk(self, patterns: List[str]) -> float:
        """Calculate risk based on market patterns"""
        risk_multipliers = {
            "high_volatility": 0.8,
            "strong_upward_trend": 0.6,
            "strong_downward_trend": 0.7,
            "stable_market": 0.2
        }
        
        total_risk = 0.0
        for pattern in patterns:
            total_risk += risk_multipliers.get(pattern, 0.3)
            
        return min(total_risk, 1.0)
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, score: float, patterns: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if score >= 0.7:
            recommendations.append("Consider delaying trade execution")
            recommendations.append("Reduce trade size to minimize exposure")
            
        if "high_volatility" in patterns:
            recommendations.append("Monitor market closely for sudden changes")
            
        if any("strong" in p for p in patterns):
            recommendations.append("Consider timing trade with trend direction")
            
        if score < 0.3:
            recommendations.append("Market conditions appear favorable")
            
        return recommendations

class BatchSimulator:
    """Run simulations across multiple tokens and delay periods"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("batch_simulator", config.verbose)
        
    async def run_multi_token_simulation(self, jupiter_client) -> Dict:
        """Run simulation across multiple tokens"""
        results = {}
        
        for token in self.config.batch_tokens:
            self.logger.info(f"Running simulation for {token}")
            
            # Create temporary config for this token
            token_config = Config(
                token=token,
                amount=self.config.amount,
                delay=self.config.delay,
                threshold=self.config.threshold,
                iterations=1
            )
            
            try:
                # Import here to avoid circular imports
                from .otc_simulator import OTCSimulator
                
                simulator = OTCSimulator(token_config)
                token_result = await simulator.simulate_otc_trade()
                results[token] = token_result
                
            except Exception as e:
                self.logger.error(f"Simulation failed for {token}: {e}")
                results[token] = {"error": str(e)}
                
        return {
            "multi_token_results": results,
            "summary": self._analyze_multi_token_results(results)
        }
    
    async def run_multi_delay_simulation(self, token: str, jupiter_client) -> Dict:
        """Run simulation with different delay periods"""
        results = {}
        
        for delay in self.config.custom_delay_periods:
            self.logger.info(f"Running simulation with {delay}s delay")
            
            # Create temporary config with custom delay
            delay_config = Config(
                token=token,
                amount=self.config.amount,
                delay=delay,
                threshold=self.config.threshold,
                iterations=1
            )
            
            try:
                from .otc_simulator import OTCSimulator
                
                simulator = OTCSimulator(delay_config)
                delay_result = await simulator.simulate_otc_trade()
                results[f"{delay}s"] = delay_result
                
            except Exception as e:
                self.logger.error(f"Simulation failed for {delay}s delay: {e}")
                results[f"{delay}s"] = {"error": str(e)}
                
        return {
            "multi_delay_results": results,
            "summary": self._analyze_multi_delay_results(results)
        }
    
    def _analyze_multi_token_results(self, results: Dict) -> Dict:
        """Analyze results across multiple tokens"""
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        
        if not valid_results:
            return {"error": "No valid results to analyze"}
            
        total_mev = sum(r.get("mev_profit", 0) for r in valid_results.values())
        risks_detected = sum(1 for r in valid_results.values() if r.get("risk_detected", False))
        
        return {
            "tokens_analyzed": len(valid_results),
            "total_mev_profit": total_mev,
            "risks_detected": risks_detected,
            "risk_percentage": (risks_detected / len(valid_results)) * 100,
            "highest_risk_token": max(valid_results.keys(), 
                                    key=lambda k: valid_results[k].get("mev_profit", 0)),
            "average_mev": total_mev / len(valid_results) if valid_results else 0
        }
    
    def _analyze_multi_delay_results(self, results: Dict) -> Dict:
        """Analyze results across different delay periods"""
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        
        if not valid_results:
            return {"error": "No valid results to analyze"}
            
        mev_by_delay = {k: v.get("mev_profit", 0) for k, v in valid_results.items()}
        optimal_delay = max(mev_by_delay.keys(), key=lambda k: mev_by_delay[k])
        
        return {
            "delays_tested": len(valid_results),
            "optimal_delay": optimal_delay,
            "max_mev_profit": mev_by_delay[optimal_delay],
            "mev_by_delay": mev_by_delay,
            "recommendation": f"Use {optimal_delay} delay for maximum MEV opportunity"
        }