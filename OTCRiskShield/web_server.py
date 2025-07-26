"""
Web interface for OTC Front-Running Defense Simulator
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from aiohttp import web, web_request, ClientTimeout
from aiohttp.web import middleware
from jinja2 import Environment, FileSystemLoader
from simulator.otc_simulator import OTCSimulator
from simulator.config import Config
from simulator.logger import setup_logger

class WebServer:
    """Web server for OTC simulator interface"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("web_server", config.verbose)
        self.app = web.Application(middlewares=[self.cors_middleware])
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        self.setup_routes()
        self.simulation_results = []
    
    @middleware
    async def cors_middleware(self, request, handler):
        """CORS middleware for API endpoints"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    def setup_routes(self):
        """Setup web routes"""
        # Static files
        self.app.router.add_static('/static/', path='static/', name='static')
        
        # Web pages
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/report', self.risk_report)
        self.app.router.add_get('/simulation', self.simulation_page)
        
        # API endpoints
        self.app.router.add_post('/api/simulate', self.api_simulate)
        self.app.router.add_get('/api/results', self.api_get_results)
        self.app.router.add_get('/api/config', self.api_get_config)
        self.app.router.add_post('/api/config', self.api_update_config)
        self.app.router.add_get('/api/status', self.api_status)
        self.app.router.add_get('/api/sol-price', self.api_sol_price)
    
    async def index(self, request: web_request.Request):
        """Main dashboard page"""
        template = self.jinja_env.get_template('index.html')
        
        # Get recent results summary
        recent_results = self.simulation_results[-10:] if self.simulation_results else []
        
        context = {
            'config': self.config.__dict__,
            'recent_results': recent_results,
            'total_simulations': len(self.simulation_results),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        html = template.render(**context)
        return web.Response(text=html, content_type='text/html')
    
    async def risk_report(self, request: web_request.Request):
        """Risk analysis report page"""
        template = self.jinja_env.get_template('reports.html')
        
        # Calculate summary statistics
        if self.simulation_results:
            total_risks = sum(1 for r in self.simulation_results if r.get('risk_detected', False))
            total_mev = sum(r.get('mev_profit', 0) for r in self.simulation_results)
            
            summary = {
                'total_simulations': len(self.simulation_results),
                'risks_detected': total_risks,
                'risk_percentage': (total_risks / len(self.simulation_results)) * 100,
                'total_mev_profit': total_mev,
                'average_mev_per_risk': total_mev / total_risks if total_risks > 0 else 0
            }
        else:
            summary = {
                'total_simulations': 0,
                'risks_detected': 0,
                'risk_percentage': 0,
                'total_mev_profit': 0,
                'average_mev_per_risk': 0
            }
        
        context = {
            'config': self.config.__dict__,
            'results': self.simulation_results,
            'summary': summary,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        html = template.render(**context)
        return web.Response(text=html, content_type='text/html')
    
    async def simulation_page(self, request: web_request.Request):
        """Simulation control page"""
        template = self.jinja_env.get_template('simulation.html')
        html = template.render()
        return web.Response(text=html, content_type='text/html')
    
    async def simulation_page_old(self, request: web_request.Request):
        """Old simulation control page - keeping for reference"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OTC Simulator - Run Simulation</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>Run OTC Simulation</h1>
                <form id="simulationForm">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Token</label>
                                <select class="form-select" name="token">
                                    <option value="SOL">SOL - Solana</option>
                                    <option value="BTC">BTC - Bitcoin</option>
                                    <option value="ETH">ETH - Ethereum</option>
                                    <option value="USDC">USDC - USD Coin</option>
                                    <option value="USDT">USDT - Tether</option>
                                    <option value="BNB">BNB - Binance Coin</option>
                                    <option value="ADA">ADA - Cardano</option>
                                    <option value="MATIC">MATIC - Polygon</option>
                                    <option value="AVAX">AVAX - Avalanche</option>
                                    <option value="DOT">DOT - Polkadot</option>
                                    <option value="LINK">LINK - Chainlink</option>
                                    <option value="UNI">UNI - Uniswap</option>
                                    <option value="RAY">RAY - Raydium</option>
                                    <option value="SRM">SRM - Serum</option>
                                    <option value="ORCA">ORCA - Orca</option>
                                    <option value="MNGO">MNGO - Mango</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Amount</label>
                                <input type="number" class="form-control" name="amount" value="100" step="0.01">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Delay (seconds)</label>
                                <input type="number" class="form-control" name="delay" value="2.0" step="0.1">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Risk Threshold (%)</label>
                                <input type="number" class="form-control" name="threshold" value="1.0" step="0.1">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Iterations</label>
                                <input type="number" class="form-control" name="iterations" value="1" min="1">
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="verbose">
                                    <label class="form-check-label">Verbose logging</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Run Simulation</button>
                </form>
                
                <div id="results" class="mt-4" style="display: none;">
                    <h3>Results</h3>
                    <div id="resultsContent"></div>
                </div>
            </div>
            
            <script>
                document.getElementById('simulationForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    const config = Object.fromEntries(formData);
                    
                    // Convert numbers
                    config.amount = parseFloat(config.amount);
                    config.delay = parseFloat(config.delay);
                    config.threshold = parseFloat(config.threshold) / 100; // Convert to decimal
                    config.iterations = parseInt(config.iterations);
                    config.verbose = formData.has('verbose');
                    
                    try {
                        const response = await fetch('/api/simulate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(config)
                        });
                        
                        const results = await response.json();
                        
                        document.getElementById('results').style.display = 'block';
                        document.getElementById('resultsContent').innerHTML = `
                            <pre>${JSON.stringify(results, null, 2)}</pre>
                        `;
                    } catch (error) {
                        alert('Simulation failed: ' + error.message);
                    }
                });
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def api_simulate(self, request: web_request.Request):
        """API endpoint to run simulation with enhanced features"""
        try:
            data = await request.json()
            
            # Create config from request with enhanced features
            config = Config(
                token=data.get('token', self.config.token),
                amount=data.get('amount', self.config.amount),
                delay=data.get('delay', self.config.delay),
                threshold=data.get('threshold', self.config.threshold),
                iterations=data.get('iterations', 1),
                verbose=data.get('verbose', self.config.verbose),
                # Enhanced features
                enable_alerts=data.get('enable_alerts', True),
                alert_threshold=float(data.get('alert_threshold', 0.02)),
                historical_tracking=data.get('historical_tracking', True),
                advanced_risk_scoring=data.get('advanced_risk_scoring', True),
                batch_tokens=data.get('batch_tokens', ["SOL", "BTC", "ETH", "USDC", "USDT", "BNB", "ADA", "MATIC", "AVAX", "DOT", "LINK", "UNI", "RAY", "SRM", "ORCA", "MNGO"]),
                custom_delay_periods=data.get('custom_delay_periods', [1.0, 2.0, 3.0, 5.0, 10.0])
            )
            
            # Run simulation
            simulator = OTCSimulator(config)
            simulation_type = data.get('simulation_type', 'single')
            
            if simulation_type == 'enhanced_batch':
                results = await simulator.run_enhanced_batch_simulation()
                self.simulation_results = results
                return web.json_response({
                    'success': True,
                    'results': results,
                    'market_insights': simulator.get_market_insights(),
                    'simulation_type': 'enhanced_batch'
                })
            elif simulation_type == 'multi_token':
                results = await simulator.batch_simulator.run_multi_token_simulation(None)
                self.simulation_results = results
                return web.json_response({
                    'success': True,
                    'results': results,
                    'simulation_type': 'multi_token'
                })
            elif simulation_type == 'multi_delay':
                results = await simulator.batch_simulator.run_multi_delay_simulation(config.token, None)
                self.simulation_results = results
                return web.json_response({
                    'success': True,
                    'results': results,
                    'simulation_type': 'multi_delay'
                })
            elif config.iterations == 1:
                result = await simulator.simulate_otc_trade()
                self.simulation_results.append(result)
                return web.json_response({
                    'success': True,
                    'results': result,
                    'market_insights': simulator.get_market_insights(),
                    'simulation_type': 'single'
                })
            else:
                results = await simulator.run_batch_simulation()
                self.simulation_results.extend(results)
                analysis = simulator.analyze_batch_results(results)
                return web.json_response({
                    'success': True,
                    'results': results,
                    'analysis': analysis,
                    'market_insights': simulator.get_market_insights(),
                    'simulation_type': 'batch'
                })
                
        except Exception as e:
            self.logger.error(f"Simulation API error: {e}")
            return web.json_response(
                {'success': False, 'error': str(e)}, 
                status=500
            )
    
    async def api_get_results(self, request: web_request.Request):
        """API endpoint to get simulation results"""
        limit = int(request.query.get('limit', 100))
        results = self.simulation_results[-limit:] if limit else self.simulation_results
        
        return web.json_response({
            'results': results,
            'total_count': len(self.simulation_results)
        })
    
    async def api_get_config(self, request: web_request.Request):
        """API endpoint to get current configuration"""
        return web.json_response(self.config.__dict__)
    
    async def api_update_config(self, request: web_request.Request):
        """API endpoint to update configuration"""
        try:
            data = await request.json()
            
            # Update config
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            self.config.validate()
            
            return web.json_response({
                'success': True,
                'config': self.config.__dict__
            })
            
        except Exception as e:
            return web.json_response(
                {'error': str(e)}, 
                status=400
            )
    
    async def api_status(self, request: web_request.Request):
        """API endpoint for server status"""
        return web.json_response({
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'total_simulations': len(self.simulation_results),
            'config': self.config.__dict__
        })
    
    async def api_sol_price(self, request: web_request.Request):
        """API endpoint to get SOL price with multiple fallbacks"""
        # Check if we have cached data (cache for 30 seconds to avoid rate limits)
        cache_key = 'sol_price_cache'
        cache_duration = 30  # seconds
        
        if hasattr(self, '_price_cache') and self._price_cache:
            cache_time = self._price_cache.get('timestamp', 0)
            current_time = datetime.now().timestamp()
            if current_time - cache_time < cache_duration:
                return web.json_response(self._price_cache['data'])
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Try CoinGecko first (free tier)
                try:
                    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true"
                    headers = {
                        'User-Agent': 'OTC-Simulator/1.0',
                        'Accept': 'application/json'
                    }
                    
                    timeout = ClientTimeout(total=10)
                    async with session.get(url, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'solana' in data:
                                sol_data = data['solana']
                                price = sol_data.get('usd', 0)
                                change_24h = sol_data.get('usd_24h_change', 0)
                                
                                result = {
                                    'success': True,
                                    'price': price,
                                    'change_24h': change_24h,
                                    'source': 'coingecko',
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                # Cache the result
                                if not hasattr(self, '_price_cache'):
                                    self._price_cache = {}
                                self._price_cache = {
                                    'data': result,
                                    'timestamp': datetime.now().timestamp()
                                }
                                
                                return web.json_response(result)
                        elif response.status == 429:
                            self.logger.warning("CoinGecko rate limit hit, trying fallback...")
                            
                except Exception as e:
                    self.logger.warning(f"CoinGecko failed: {e}, trying fallback...")
                
                # Fallback to CryptoCompare API
                try:
                    url = "https://min-api.cryptocompare.com/data/price?fsym=SOL&tsyms=USD"
                    
                    timeout = ClientTimeout(total=10)
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'USD' in data:
                                price = data['USD']
                                
                                result = {
                                    'success': True,
                                    'price': price,
                                    'change_24h': 0,  # No change data from this API
                                    'source': 'cryptocompare',
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                # Cache the result
                                if not hasattr(self, '_price_cache'):
                                    self._price_cache = {}
                                self._price_cache = {
                                    'data': result,
                                    'timestamp': datetime.now().timestamp()
                                }
                                
                                return web.json_response(result)
                                
                except Exception as e:
                    self.logger.warning(f"CryptoCompare failed: {e}")
                
                # If both APIs fail, return cached data if available
                if hasattr(self, '_price_cache') and self._price_cache:
                    cached_result = self._price_cache['data'].copy()
                    cached_result['note'] = 'Using cached data due to API limits'
                    return web.json_response(cached_result)
                
                return web.json_response({
                    'success': False,
                    'error': 'All price APIs are currently unavailable'
                }, status=503)
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch SOL price: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def start_server(self, host='0.0.0.0', port=5000):
        """Start the web server"""
        self.logger.info(f"Starting web server on {host}:{port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        self.logger.info(f"Web server running at http://{host}:{port}")
        
        # Keep server running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour intervals

async def start_web_server(config: Config):
    """Start web server with given configuration"""
    server = WebServer(config)
    await server.start_server()

if __name__ == "__main__":
    config = Config()
    asyncio.run(start_web_server(config))

