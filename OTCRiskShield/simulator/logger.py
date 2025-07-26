"""
Logging configuration for OTC simulator
"""

import logging
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: Optional[str] = None, verbose: bool = False) -> logging.Logger:
    """
    Set up logger with appropriate formatting and level
    
    Args:
        name: Logger name (defaults to root logger)
        verbose: Enable debug level logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

class RiskLogger:
    """Specialized logger for risk detection events"""
    
    def __init__(self, logger_name: str = "risk_detector"):
        self.logger = logging.getLogger(logger_name)
        self.risk_events = []
    
    def log_risk_detected(self, trade_data: dict, risk_analysis: dict):
        """Log a risk detection event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'RISK_DETECTED',
            'trade_data': trade_data,
            'risk_analysis': risk_analysis
        }
        
        self.risk_events.append(event)
        
        self.logger.warning(
            f"FRONT-RUNNING RISK DETECTED: "
            f"Token: {trade_data.get('token', 'Unknown')}, "
            f"Amount: {trade_data.get('amount', 0)}, "
            f"Price Change: {risk_analysis.get('price_change_pct', 0):.4f}%, "
            f"MEV Profit: ${risk_analysis.get('mev_profit', 0):.2f}"
        )
    
    def log_mev_opportunity(self, mev_data: dict):
        """Log an MEV opportunity"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': 'MEV_OPPORTUNITY',
            'mev_data': mev_data
        }
        
        self.risk_events.append(event)
        
        self.logger.info(
            f"MEV OPPORTUNITY: "
            f"Profit: ${mev_data.get('net_profit', 0):.2f}, "
            f"ROI: {mev_data.get('roi_pct', 0):.2f}%, "
            f"Token: {mev_data.get('token', 'Unknown')}"
        )
    
    def get_risk_events(self, event_type: Optional[str] = None) -> list:
        """Get logged risk events"""
        if event_type:
            return [e for e in self.risk_events if e['type'] == event_type]
        return self.risk_events.copy()
    
    def export_risk_log(self, filename: str):
        """Export risk events to JSON file"""
        import json
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.risk_events, f, indent=2, default=str)
            self.logger.info(f"Risk log exported to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to export risk log: {e}")

class MEVLogger:
    """Specialized logger for MEV calculations"""
    
    def __init__(self, logger_name: str = "mev_calculator"):
        self.logger = logging.getLogger(logger_name)
        self.mev_calculations = []
    
    def log_mev_calculation(self, calculation_data: dict):
        """Log an MEV calculation"""
        self.mev_calculations.append({
            'timestamp': datetime.now().isoformat(),
            **calculation_data
        })
        
        profit = calculation_data.get('net_profit', 0)
        if profit > 0:
            self.logger.info(f"MEV calculated: ${profit:.2f} profit")
        else:
            self.logger.debug(f"MEV calculation: ${profit:.2f} (not profitable)")
    
    def get_mev_summary(self) -> dict:
        """Get summary of MEV calculations"""
        if not self.mev_calculations:
            return {'error': 'No MEV calculations recorded'}
        
        profits = [calc.get('net_profit', 0) for calc in self.mev_calculations]
        profitable_calculations = [p for p in profits if p > 0]
        
        return {
            'total_calculations': len(self.mev_calculations),
            'profitable_calculations': len(profitable_calculations),
            'total_mev': sum(profits),
            'average_mev': sum(profits) / len(profits),
            'max_mev': max(profits),
            'min_mev': min(profits)
        }

