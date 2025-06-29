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
