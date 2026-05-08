# TradingAgents Benchmark

**Domain:** Algorithmic Trading  
**System:** TradingAgents — a 12-agent LLM system that produces an investment recommendation (Buy/Hold/Sell) for a given stock ticker.

## Agents

| Agent | Role |
|-------|------|
| Market Analyst | Technical analysis of price/volume data |
| Social Media Analyst | Sentiment analysis from social media |
| News Analyst | News and macroeconomic context |
| Fundamentals Analyst | Fundamental financial metrics |
| Bull Researcher | Constructs the bullish thesis |
| Bear Researcher | Constructs the bearish thesis |
| Research Manager | Synthesises bull/bear debate |
| Risky Analyst | High-risk investment perspective |
| Safe Analyst | Conservative/risk-adjusted perspective |
| Neutral Analyst | Balanced/neutral perspective |
| Risk Manager | Aggregates risk signals |
| Trader | Final trading decision |

Full agent definitions (system prompts, tools) are in [`agents/`](agents/).

## Fault Dimensions (15)

See [`schema.md`](schema.md) for the full dimension specification.

| Index | Dimension |
|-------|-----------|
| 0 | Market Analyst |
| 1 | Fundamentals Analyst |
| 2 | News Analyst |
| 3 | Social Media Analyst |
| 4 | Bull Researcher |
| 5 | Bear Researcher |
| 6 | Research Manager |
| 7 | The Trader |
| 8 | Risky Analyst (Aggressive) |
| 9 | Safe Analyst (Conservative) |
| 10 | Neutral Analyst (Balanced) |
| 11 | Risk Manager (The Judge) |
| 12 | System Memory |
| 13 | Workflow DAG |
| 14 | External Data Feeds |

A dimension is `1` if that component exhibited a fault during the session; `0` otherwise.

## Cases

6 cases covering single-fault scenarios for different agent roles.  
Each case is a self-contained JSON file in [`cases/`](cases/).

### Case structure

```json
{
  "case_id": "trading_session_2",
  "domain": "trading_agents",
  "agents": ["market_analyst", "social_media_analyst", ...],
  "dimensions": ["Market Analyst", ...],
  "ground_truth_vector": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  "n_errors": 1,
  "injected_hazards": "...",
  "faulty_components": [...],
  "session": {
    "messages": [
      {
        "index": 1,
        "type": "SystemMessage",
        "from": "system",
        "to": "bear_researcher",
        "content": "You are a Bear Analyst..."
      },
      {
        "index": 2,
        "type": "HumanMessage",
        "from": "market_analyst_v83baa837",
        "to": "broadcast",
        "content": "### Bearish Technical Analysis Report..."
      },
      ...
    ]
  }
}
```

### Message routing

Messages are broadcast-based: most messages go `from=<agent> to=broadcast`.  
The deduplication logic in `export_cases.py` ensures each broadcast message appears only once in the unified message list, preserving first-occurrence ordering.

## Quick start

```bash
# Evaluate your system's predictions
python ../../evaluate.py --benchmark trading_agents --predictions my_predictions.csv --model "MyModel"
```

Predictions CSV format:
```
case_id,predicted_vector
trading_session_2,"0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
trading_session_3,"0,1,0,0,0,0,0,0,0,0,0,0,0,0,0"
```

## Results

See [`results/results.csv`](results/results.csv) for all submitted evaluations.
