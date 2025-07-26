#!/usr/bin/env python3
"""
OTC Front-Running Defense Simulator
Main entry point for the simulation system
"""

import argparse
import asyncio
import sys
import json
from datetime import datetime
from simulator.otc_simulator import OTCSimulator
from simulator.config import Config
from simulator.logger import setup_logger

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="OTC Front-Running Defense Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --token SOL --amount 100 --delay 2.5
  python main.py --token USDC --amount 50000 --threshold 0.02 --iterations 10
  python main.py --config custom_config.json
        """
    )
    
    parser.add_argument(
        '--token', 
        default='SOL',
        help='Token symbol to simulate (default: SOL)'
    )
    
    parser.add_argument(
        '--amount', 
        type=float, 
        default=100.0,
        help='Trade amount in token units (default: 100.0)'
    )
    
    parser.add_argument(
        '--delay', 
        type=float, 
        default=2.0,
        help='Block delay in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--threshold', 
        type=float, 
        default=0.01,
        help='Risk threshold as decimal (default: 0.01 = 1%%)'
    )
    
    parser.add_argument(
        '--iterations', 
        type=int, 
        default=1,
        help='Number of simulation iterations (default: 1)'
    )
    
    parser.add_argument(
        '--config', 
        type=str,
        help='Path to JSON configuration file'
    )
    
    parser.add_argument(
        '--output', 
        type=str,
        help='Output file for results (JSON format)'
    )
    
    parser.add_argument(
        '--web', 
        action='store_true',
        help='Start web interface on port 5000'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {config_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)

async def run_simulation(config):
    """Run the OTC simulation"""
    logger = setup_logger(verbose=config.verbose)
    
    logger.info("Starting OTC Front-Running Defense Simulator")
    logger.info(f"Configuration: {config}")
    
    simulator = OTCSimulator(config)
    results = []
    
    try:
        for iteration in range(config.iterations):
            logger.info(f"Running iteration {iteration + 1}/{config.iterations}")
            
            result = await simulator.simulate_otc_trade()
            results.append(result)
            
            # Log result summary
            if result['risk_detected']:
                logger.warning(f"RISK DETECTED - MEV Profit: ${result['mev_profit']:.2f}")
            else:
                logger.info(f"No risk detected - Price change: {result['price_change']:.4f}%")
    
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise
    
    # Generate summary
    total_risks = sum(1 for r in results if r['risk_detected'])
    total_mev = sum(r['mev_profit'] for r in results)
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config': config.__dict__,
        'total_iterations': len(results),
        'risks_detected': total_risks,
        'risk_percentage': (total_risks / len(results)) * 100 if results else 0,
        'total_mev_profit': total_mev,
        'average_mev_per_risk': total_mev / total_risks if total_risks > 0 else 0,
        'results': results
    }
    
    logger.info(f"Simulation complete: {total_risks}/{len(results)} risks detected")
    logger.info(f"Total theoretical MEV profit: ${total_mev:.2f}")
    
    return summary

def save_results(results, output_path):
    """Save results to JSON file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")

async def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Load configuration
    if args.config:
        config_dict = load_config(args.config)
        config = Config(**config_dict)
    else:
        config = Config(
            token=args.token,
            amount=args.amount,
            delay=args.delay,
            threshold=args.threshold,
            iterations=args.iterations,
            verbose=args.verbose
        )
    
    # Start web interface if requested
    if args.web:
        from web_server import start_web_server
        await start_web_server(config)
        return
    
    # Run simulation
    try:
        results = await run_simulation(config)
        
        # Save results if output path specified
        if args.output:
            save_results(results, args.output)
        
        # Print summary to console
        print("\n" + "="*50)
        print("SIMULATION SUMMARY")
        print("="*50)
        print(f"Token: {config.token}")
        print(f"Amount: {config.amount}")
        print(f"Delay: {config.delay}s")
        print(f"Risk Threshold: {config.threshold * 100:.1f}%")
        print(f"Iterations: {results['total_iterations']}")
        print(f"Risks Detected: {results['risks_detected']} ({results['risk_percentage']:.1f}%)")
        print(f"Total MEV Profit: ${results['total_mev_profit']:.2f}")
        if results['risks_detected'] > 0:
            print(f"Average MEV per Risk: ${results['average_mev_per_risk']:.2f}")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(0)
