# 🛡️ OTCRiskShield – OTC Front-Running Defense Simulator

## 📄 Overview

**OTCRiskShield** is a Python-based web application that simulates Over-The-Counter (OTC) cryptocurrency trades to detect **front-running risks**.  
It monitors price movements during simulated block delays and calculates potential Maximum Extractable Value (MEV) that front-runners could capture.  
It provides both a **command-line interface (CLI)** and a **web-based dashboard** for running simulations and viewing risk reports.

---


## 🏛️ System Architecture

The application follows a modular design with clear separation between simulation logic, web interface, and API integrations.

### ⚙️ Backend Architecture
- **Async Python Framework:** Uses `asyncio` for concurrent operations and real-time price monitoring.
- **Web Framework:** Built with `aiohttp` for lightweight async HTTP server capabilities.
- **Template Engine:** Uses **Jinja2** for server-side HTML rendering.
- **API Client:** Custom **Jupiter API client** for fetching real-time crypto prices.

### 🎨 Frontend Architecture
- **Web Interface:** Server-rendered HTML with **Bootstrap 5** for responsive design.
- **Real-time Updates:** JavaScript-based dashboard for live simulation results.
- **Charts & Visualization:** **Chart.js** integration for price movement and risk visualization.
- **Static Assets:** CSS and JavaScript files served directly by `aiohttp`.

---

## 🗂️ Key Components

### 🧩 OTC Simulator Engine (`simulator/otc_simulator.py`)
- Main simulation orchestrator
- Coordinates price monitoring, risk detection, and MEV calculations
- Handles multiple simulation iterations

### 🔗 Jupiter API Client (`simulator/jupiter_client.py`)
- Interfaces with **Jupiter DEX API** for real-time price data
- Implements retry logic and error handling
- Monitors price changes during block delays

### 🚨 Risk Detector (`simulator/risk_detector.py`)
- Analyzes price movements to identify front-running risks
- Calculates risk scores based on price thresholds and trade impact
- Provides detailed risk assessment metrics

### 💰 MEV Calculator (`simulator/mev_calculator.py`)
- Estimates potential profits from front-running opportunities
- Accounts for gas costs, slippage, and transaction fees
- Calculates net MEV value in USD

### 🌐 Web Server (`web_server.py`)
- Serves the web dashboard and API endpoints
- Handles CORS for frontend-backend communication
- Manages simulation state and results storage

### ⚙️ Configuration System (`simulator/config.py`)
- Centralized configuration management
- Token mint address mappings for Solana
- Simulation parameters and API settings

---

## 🔄 Data Flow

1. **Simulation Initiation:** User triggers simulation via web interface or CLI.
2. **Initial Price Fetch:** System queries Jupiter API for current token price.
3. **Block Delay Simulation:** Monitors price changes over specified delay period.
4. **Risk Analysis:** Analyzes price movements against configurable thresholds.
5. **MEV Calculation:** Estimates potential front-running profits.
6. **Report Generation:** Compiles results into web dashboard or CLI output.
7. **Historical Storage:** Maintains simulation results for trend analysis.

---

## 📦 External Dependencies

### 🧰 Core Dependencies
- `aiohttp (3.12.13)`: Async HTTP client/server framework
- `jinja2 (3.1.6)`: Template engine for web interface
- `asyncio`: Built-in Python async library

### 🖼️ Frontend Dependencies (CDN)
- **Bootstrap 5.1.3:** CSS framework for responsive design
- **Chart.js:** JavaScript charting library
- **Font Awesome 6.0.0:** Icon library

### 🌐 External APIs
- **Jupiter API:** Primary data source for cryptocurrency prices  
  - Price API: `https://price.jup.ag/v6`
  - Quote API: `https://quote-api.jup.ag/v6/quote`
- **Solana Token Registry:** Token mint address resolution

---
