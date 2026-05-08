# TradingAgents Benchmark — Schema

## Domain

**Algorithmic multi-agent trading.** TradingAgents is a multi-agent framework for automated financial decision-making in which specialised agents collaborate to analyse markets, manage risk, and execute trades.

Each case is a full trading session where one or more agents have been deliberately given incorrect information or behavioural instructions. The benchmark tests whether a fault-attribution system can identify *which* components failed from the resulting conversation and decisions.

---

## Agents

| Agent key | Display name | Dimension index |
|-----------|--------------|-----------------|
| `market_analyst` | Market Analyst | 0 |
| `fundamentals_analyst` | Fundamentals Analyst | 1 |
| `news_analyst` | News Analyst | 2 |
| `social_media_analyst` | Social Media Analyst | 3 |
| `bull_researcher` | Bull Researcher | 4 |
| `bear_researcher` | Bear Researcher | 5 |
| `research_manager` | Research Manager | 6 |
| `trader` | The Trader | 7 |
| `risky_analyst` | Risky Analyst (Aggressive) | 8 |
| `safe_analyst` | Safe Analyst (Conservative) | 9 |
| `neutral_analyst` | Neutral Analyst (Balanced) | 10 |
| `risk_manager` | Risk Manager (The Judge) | 11 |

Dimensions 12–14 cover infrastructure components not tied to a specific agent.

---

## Fault Dimensions (15)

The ground truth is a binary vector of length 15:

| Index | Name | Description |
|-------|------|-------------|
| 0 | Market Analyst | Errors in technical indicator selection or market trend interpretation |
| 1 | Fundamentals Analyst | Errors in fundamental analysis (P/E, earnings, balance sheet) |
| 2 | News Analyst | Errors in news sentiment interpretation or relevance assessment |
| 3 | Social Media Analyst | Errors in social signal analysis or sentiment aggregation |
| 4 | Bull Researcher | Biased or unsupported bullish case construction |
| 5 | Bear Researcher | Biased or unsupported bearish case construction |
| 6 | Research Manager | Errors in synthesising or arbitrating analyst reports |
| 7 | The Trader | Execution errors or decisions inconsistent with the research consensus |
| 8 | Risky Analyst (Aggressive) | Miscalibrated risk appetite; advocates excessive position sizes |
| 9 | Safe Analyst (Conservative) | Miscalibrated caution; advocates unwarranted under-exposure |
| 10 | Neutral Analyst (Balanced) | Balanced assessment degraded; fails to moderate between extremes |
| 11 | Risk Manager (The Judge) | Risk-limit enforcement failures or contradictory final arbitration |
| 12 | System Memory | Retrieval errors from persistent memory affecting agent context |
| 13 | Workflow DAG | Orchestration errors causing incorrect agent ordering or skipped steps |
| 14 | External Data Feeds | Corrupted or delayed market/news data reaching the agents |

`1` at position `i` means component `i` is **faulty**.  
`0` means the component is **operating normally**.

Example: `[0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]` — only the Fundamentals Analyst is faulty.

---

## Message Structure

TradingAgents uses a broadcast messaging model: agents post to a shared thread rather than exchanging point-to-point messages.

| Field | Description |
|-------|-------------|
| `from` | Agent key or `"system"` |
| `to` | Always `"broadcast"` for agent messages; agent key for `SystemMessage` |
| `type` | `HumanMessage`, `AIMessage`, or `SystemMessage` |
| `content` | Full message text (broadcast prefix `[agent → broadcast]:` stripped) |

There are no `ToolMessage` entries in TradingAgents cases; tool results are embedded in each agent's `AIMessage` context.

---

## Case JSON Fields

```
case_id             string   Unique identifier, e.g. "trading_session_2"
domain              string   Always "algorithmic_trading"
system              string   Always "TradingAgents"
agents              list     Agent keys present in this session (12 agents)
dimensions          list     The 15 dimension names (fixed order, see table above)
ground_truth_vector list     Binary vector of length 15
n_errors            int      Number of faulty components (sum of ground_truth_vector)
injected_hazards    string   Human-readable description of what was injected
faulty_components   list     Per-fault details (see below)
session             object   Full message log (see below)
metadata            object   Source session id, generation timestamp
```

### `faulty_components` entry

```json
{
  "dimension_index":   1,
  "dimension_name":    "Fundamentals Analyst",
  "fault_description": "Analyst reported inflated P/E ratio inconsistent with..."
}
```

### `session` object

```
session.session_number   int    Original session number from the source dataset
session.messages         list   Ordered, deduplicated message list across all agents
```

---

## Agent JSON Fields (`agents/`)

```
agent_id              string   Agent key, e.g. "market_analyst"
display_name          string   Human-readable name
dimension_index       int      Index in ground_truth_vector this agent maps to (null for infra dims)
fault_error_signature string   Characteristic failure mode description
system_prompt         string   Full system prompt the agent received
tools                 list     Tools available: {name, description, parameters}
exclusive_tools       list     Tool names only this agent can call
```

---

## Results CSV (`results/results.csv`)

One row per model evaluation, appended by `evaluate.py --append-results`:

```
case_id, model, predicted_vector, ground_truth_vector, is_correct, n_errors, timestamp
trading_session_2, GPT-4o, "1,0,0,0,...", "1,0,0,0,...", True, 1, 2025-04-25T10:00:00
```

| Column | Description |
|--------|-------------|
| `case_id` | Benchmark case identifier |
| `model` | Model or system name passed via `--model` |
| `predicted_vector` | Comma-separated binary prediction |
| `ground_truth_vector` | Comma-separated ground truth |
| `is_correct` | `True` only when every bit matches (exact match) |
| `n_errors` | Number of faults in ground truth (`sum(ground_truth_vector)`) |
| `timestamp` | UTC ISO-8601 timestamp of the evaluation run |
