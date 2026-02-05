44Trade: Adaptive Decision Engine
An Agentic Microservices Infrastructure for Algorithmic Execution and Risk Governance.

The 44Trade Sniper is an autonomous, modular decision ecosystem designed for real-time financial signal processing. The system operates on a Closed-Loop architecture, integrating quantitative technical analysis, semantic LLM filtering, and probabilistic Machine Learning models to ensure high precision and systemic stability.

Technology Stack
Perception: Pine Script v6.1 (Data Ingestion & Signal Scoring).

Orchestration: n8n (Workflow Automation).

Cognition: GPT-4o Mini (Contextual Semantic Filtering).

Inference: Python 3.10+ & XGBoost (Statistical Probability Classifier).

Persistence: SQLite3 (Operational Memory).

Infrastructure: Windows Server + NSSM (Self-healing Service Management).

Execution: MetaTrader 5 Terminal (Official Python Integration).

System Architecture
1. Detection Layer: The Radar (Pine Script)
Acts as a pre-processor for market data, operating at the edge to reduce noise before transmission.

Signal Logic: Synergy between Price Action patterns (Engulfing) and Macro Trend (EMA 100).

Exhaustion Filters: Implementation of RSI and ATR to validate volatility and potential movement exhaustion.

Payload: Dispatches structured signals via JSON Webhook containing ticker, action, technical score, RSI, and ATR.

2. Cognitive Filter: The Nervous System (n8n + GPT-4o Mini)
A Generative AI layer integrated into the automation bus for semantic context analysis.

NLP Processing: n8n submits the signal to GPT-4o Mini for context interpretation and semantic opportunity description.

Technical Gatekeeper: A JavaScript Code Node validates AI output, aborting the sequence instantly in case of inconsistencies to prevent false positives.

3. Intelligence Layer: The Agentic Brain (Python & XGBoost)
Statistical decision core focused on probability and adaptation.

Probabilistic Classification: Utilizes an XGBoost Sniper v3 model to calculate the statistical probability of success (0-100%) based on complex non-linear patterns.

Self-Evolution Cycle: Native connection to SQLite3 for historical Winrate analysis (last 20 trades).

Adaptive Threshold: Dynamic adjustment of entry rigor. The system automatically raises the acceptance threshold during low-performance periods, vetoing orders that do not meet the new safety criteria.

4. Execution & Stability (MT5 & NSSM)
Reliability engineering focused on low latency and service persistence.

Native Integration: Direct execution within the Windows environment to minimize latency between the decision engine and the MetaTrader 5 terminal.

Resilience via NSSM: The Python engine operates as a Windows Native Service via the Non-Sucking Service Manager.

graph TD
    subgraph "Perception Layer (TradingView)"
        A[Pine Script v6.1] -->|JSON Webhook| B(Signal Scoring > 85)
    end

    subgraph "Nervous System (Orchestration)"
        B --> C{n8n Bus}
        C --> D[GPT-4o Mini: Semantic Filter]
        D --> E{JS Gatekeeper}
    end

    subgraph "Intelligence Layer (Inference)"
        E -->|Validated POST| F[Python Core]
        F --> G[[XGBoost Sniper v3]]
        G --> H{Adaptive Threshold}
        H -->|Decision: Execute/Veto| I[(SQLite3 Memory)]
    end

    subgraph "Execution Layer (Infrastructure)"
        H -->|Trade Command| J[MetaTrader 5]
        K[NSSM Service] -.->|Self-healing| F
    end

    style G fill:#f96,stroke:#333,stroke-width:2px
    style D fill:#69f,stroke:#333,stroke-width:2px

Self-Healing: Automatic recovery within milliseconds after system crashes or reboots, ensuring 24/5 autonomous operation without human intervention.

Trade Management: Standardized execution with Stop Loss (800 pts) and Take Profit (2400 pts), managed via the official MT5 Python library.
