# Infrastructure & Resilience Guide (NSSM)

To ensure the **44Trade Sniper** operates 24/5 with 99.9% uptime, we use **NSSM (Non-Sucking Service Manager)** to wrap the Python engine as a Windows Native Service.

### 1. Installation
1. Download NSSM from nssm.cc.
2. Move the `nssm.exe` to your project folder.

### 2. Creating the Service
Open PowerShell as Administrator and run:
`.\nssm.exe install 44TradeSniper`

### 3. Configuration
* **Path:** Path to your `python.exe` (inside your venv).
* **Startup directory:** Path to your `src/` folder.
* **Arguments:** `main.py`

### 4. Self-Healing (Recovery)
Under the "Recovery" tab, set:
* **First failure:** Restart Service.
* **Reset fail count after:** 60 seconds.

This ensures that if the Python script crashes or the VPS reboots, the system restarts itself within milliseconds.
