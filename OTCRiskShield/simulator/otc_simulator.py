"""
OTC trade simulator with front-running risk detection
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from .jupiter_client import JupiterClient
from .risk_detector import RiskDetector
from .mev_calculator import MEVCalculator
from .config import Config
from .enhanced_features import (
    HistoricalTracker, AlertSystem, AdvancedRiskScorer, BatchSimulator
)

class OTCSimulator:
    """Main OTC simulation engine"""
    
    def __init__(self, config: Config):
        self.config = config
        self.config.validate()
        self.logger = logging.getLogger(__name__)
        
        # Initialize enhanced features
        if config.historical_tracking:
            self.historical_tracker = HistoricalTracker(config)
        else:
            self.historical_tracker = None
            
        if config.enable_alerts:
            self.alert_system = AlertSystem(config)
            # Add default alerts
            self.alert_system.add_alert(config.token, config.alert_threshold)
        else:
            self.alert_system = None
            
        if config.advanced_risk_scoring:
            self.advanced_risk_scorer = AdvancedRiskScorer(config)
        else:
            self.advanced_risk_scorer = None
            
        self.batch_simulator = BatchSimulator(config)
        self.risk_detector = RiskDetector(config)
        self.mev_calculator = MEVCalculator(config)
    
    async def simulate_otc_trade(self) -> Dict:
        """
        Simulate a single OTC trade with front-running risk analysis
        
        Returns:
            Dictionary containing simulation results
        """
        self.logger.info(f"Simulating OTC trade: {self.config.amount} {self.config.token}")
        
        start_time = datetime.now()
        
        async with JupiterClient(self.config) as jupiter:
            try:
                # Step 1: Get initial quote (OTC order placement)
                initial_price = await jupiter.get_token_price(self.config.token)
                if initial_price is None:
                    raise ValueError(f"Could not get initial price for {self.config.token}")
                
                self.logger.info(f"OTC order placed at ${initial_price:.6f}")
                
                # Add to historical tracking
                if self.historical_tracker:
                    self.historical_tracker.add_price_data(self.config.token, initial_price)
                
                # Step 2: Simulate block delay and monitor price changes
                self.logger.info(f"Simulating {self.config.delay}s block delay...")
                
                initial_price_monitor, final_price, price_history = await jupiter.monitor_price_changes(
                    self.config.token, 
                    self.config.delay
                )
                
                # Add final price to historical tracking
                if self.historical_tracker:
                    self.historical_tracker.add_price_data(self.config.token, final_price)
                
                # Check alerts
                if self.alert_system:
                    self.alert_system.check_alerts(self.config.token, final_price, initial_price)
                
                # Step 3: Analyze risk and calculate MEV
                price_change = ((final_price - initial_price) / initial_price)
                price_change_pct = price_change * 100
                
                risk_detected = self.risk_detector.detect_risk(
                    initial_price, 
                    final_price, 
                    self.config.amount
                )
                
                mev_profit = 0.0
                if risk_detected:
                    mev_profit = await self.mev_calculator.calculate_mev_profit(
                        self.config.token,
                        self.config.amount,
                        initial_price,
                        final_price,
                        jupiter
                    )
                
                # Step 3.5: Enhanced risk analysis
                enhanced_analysis = {}
                if self.advanced_risk_scorer and self.historical_tracker:
                    volatility = self.historical_tracker.calculate_volatility(self.config.token)
                    market_patterns = self.historical_tracker.detect_market_patterns(self.config.token)
                    
                    enhanced_analysis = self.advanced_risk_scorer.calculate_advanced_risk_score(
                        self.config.token,
                        self.config.amount * initial_price,  # Trade value in USD
                        price_change,
                        volatility,
                        market_patterns.get("patterns", [])
                    )
                
                # Step 4: Compile results
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = {
                    'timestamp': start_time.isoformat(),
                    'token': self.config.token,
                    'amount': self.config.amount,
                    'delay_seconds': self.config.delay,
                    'initial_price': initial_price,
                    'final_price': final_price,
                    'price_change': price_change_pct,
                    'price_history': price_history,
                    'risk_detected': risk_detected,
                    'risk_threshold': self.config.threshold * 100,
                    'mev_profit': mev_profit,
                    'execution_time': execution_time,
                    'risk_analysis': self.risk_detector.get_risk_details(),
                    'mev_analysis': self.mev_calculator.get_calculation_details(),
                    'enhanced_analysis': enhanced_analysis,
                    'alerts_triggered': self.alert_system.get_recent_alerts(1) if self.alert_system else [],
                    'market_volatility': self.historical_tracker.calculate_volatility(self.config.token) if self.historical_tracker else 0.0
                }
                
                self.logger.info(f"Trade simulation complete: "
                               f"Price change: {price_change_pct:+.4f}%, "
                               f"Risk: {'YES' if risk_detected else 'NO'}, "
                               f"MEV: ${mev_profit:.2f}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"Simulation failed: {e}")
                return {
                    'timestamp': start_time.isoformat(),
                    'token': self.config.token,
                    'amount': self.config.amount,
                    'error': str(e),
                    'risk_detected': False,
                    'mev_profit': 0.0
                }
    
    async def run_batch_simulation(self, iterations: int = None) -> List[Dict]:
        """
        Run multiple simulation iterations
        
        Args:
            iterations: Number of iterations (uses config default if None)
            
        Returns:
            List of simulation results
        """
        if iterations is None:
            iterations = self.config.iterations
        
        self.logger.info(f"Starting batch simulation: {iterations} iterations")
        
        results = []
        for i in range(iterations):
            self.logger.info(f"Running iteration {i + 1}/{iterations}")
            
            result = await self.simulate_otc_trade()
            results.append(result)
            
            # Add small delay between iterations to avoid rate limiting
            if i < iterations - 1:
                await asyncio.sleep(1.0)
        
        self.logger.info(f"Batch simulation complete: {len(results)} results")
        return results
    
    def analyze_batch_results(self, results: List[Dict]) -> Dict:
        """
        Analyze results from batch simulation
        
        Args:
            results: List of simulation results
            
        Returns:
            Analysis summary
        """
        if not results:
            return {'error': 'No results to analyze'}
        
        successful_results = [r for r in results if 'error' not in r]
        
        if not successful_results:
            return {'error': 'No successful simulations'}
        
        # Calculate statistics
        risks_detected = sum(1 for r in successful_results if r['risk_detected'])
        total_mev = sum(r['mev_profit'] for r in successful_results)
        price_changes = [r['price_change'] for r in successful_results]
        
        analysis = {
            'total_simulations': len(results),
            'successful_simulations': len(successful_results),
            'risks_detected': risks_detected,
            'risk_percentage': (risks_detected / len(successful_results)) * 100,
            'total_mev_profit': total_mev,
            'average_mev_per_simulation': total_mev / len(successful_results),
            'average_mev_per_risk': total_mev / risks_detected if risks_detected > 0 else 0,
            'price_change_stats': {
                'min': min(price_changes),
                'max': max(price_changes),
                'average': sum(price_changes) / len(price_changes),
                'volatility': self._calculate_volatility(price_changes)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Batch analysis: {risks_detected}/{len(successful_results)} risks detected, "
                        f"${total_mev:.2f} total MEV")
        
        return analysis
    
    def _calculate_volatility(self, price_changes: List[float]) -> float:
        """Calculate price change volatility (standard deviation)"""
        if len(price_changes) < 2:
            return 0.0
        
        mean = sum(price_changes) / len(price_changes)
        variance = sum((x - mean) ** 2 for x in price_changes) / len(price_changes)
        return variance ** 0.5
    
    async def run_enhanced_batch_simulation(self) -> Dict:
        """Run enhanced batch simulation with multiple tokens and delay periods"""
        self.logger.info("Starting enhanced batch simulation")
        
        results = {
            "multi_token_results": {},
            "multi_delay_results": {},
            "enhanced_analysis": {}
        }
        
        # Multi-token simulation
        if len(self.config.batch_tokens) > 1:
            results["multi_token_results"] = await self.batch_simulator.run_multi_token_simulation(None)
        
        # Multi-delay simulation
        if len(self.config.custom_delay_periods) > 1:
            results["multi_delay_results"] = await self.batch_simulator.run_multi_delay_simulation(
                self.config.token, None
            )
        
        # Enhanced market analysis
        if self.historical_tracker:
            market_analysis = {}
            for token in self.config.batch_tokens:
                market_analysis[token] = self.historical_tracker.detect_market_patterns(token)
            results["enhanced_analysis"]["market_patterns"] = market_analysis
        
        # Alert summary
        if self.alert_system:
            results["enhanced_analysis"]["alerts"] = self.alert_system.get_recent_alerts(24)
        
        return results
    
    def get_market_insights(self) -> Dict:
        """Get comprehensive market insights from enhanced features"""
        insights = {}
        
        if self.historical_tracker:
            for token in self.config.batch_tokens:
                insights[token] = {
                    "volatility": self.historical_tracker.calculate_volatility(token),
                    "trend": self.historical_tracker.get_price_trend(token),
                    "patterns": self.historical_tracker.detect_market_patterns(token)
                }
        
        return insights
