# TradingAssistant

A read-only rules checker for forex day trading. It uses Claude Code and MetaTrader 5.

A small MCP server ([`mt5_server.py`](mt5_server.py)) gives Claude read-only access to a local MetaTrader 5 terminal: prices, candles, account state, positions and trade history. A written rulebook in [`CLAUDE.md`](CLAUDE.md) tells Claude how to check the market against the rules. Claude only reports a trade idea when every rule passes. The trader makes every decision and places every trade by hand.

> **The server cannot place, modify or close orders.** It has no tools that trade, and the rulebook tells Claude never to trade even if it could.

## How it works

```
MetaTrader 5 terminal  ──►  mt5_server.py (MCP, read-only)  ──►  Claude Code  ──►  you
   (logged-in account)        prices, candles, account            checks CLAUDE.md     decide &
                               positions, deal history             rulebook             execute
```

1. Claude Code starts the server through [`.mcp.json`](.mcp.json).
2. The server attaches to the MT5 terminal on your machine and uses the account already logged in there. It never handles credentials.
3. You type a command (`SCAN`, `REVIEW`, `STATS`). Claude fetches the data, computes the indicators from the raw candles, and checks each rule in order.

## MCP tools

| Tool | Returns |
|---|---|
| `account_info` | Balance, equity, margin, leverage, currency, server |
| `terminal_info` | Connection status, build, data path |
| `symbols` | Symbol names, optionally filtered (e.g. `*USD*`) |
| `symbol_info` | Contract details: digits, contract size, tick value, volume limits |
| `tick` | Latest bid / ask |
| `candles` | Recent OHLCV bars (M1–MN1). Times are broker server time |
| `positions` | Open positions |
| `orders` | Pending orders |
| `deal_history` | Closed deals over the last N days |

## Requirements

- Windows. The `MetaTrader5` Python package only runs on Windows.
- MetaTrader 5 installed and logged in to an account.
- Python 3.12+ and [uv](https://docs.astral.sh/uv/).
- [Claude Code](https://claude.com/claude-code).

## Setup

1. Clone the repo and install the dependencies:

   ```bash
   git clone https://github.com/<your-username>/TradingAssistant.git
   ```

   ```bash
   cd TradingAssistant
   ```

   ```bash
   uv sync
   ```

2. Point the server at your terminal. By default it uses
   `C:\Program Files\MetaTrader 5 IC Markets Global\terminal64.exe`. For a different install, set `MT5_TERMINAL_PATH`:

   ```powershell
   $env:MT5_TERMINAL_PATH = "C:\Program Files\MetaTrader 5\terminal64.exe"
   ```

3. Edit [`.mcp.json`](.mcp.json) so `--directory` points to your clone.

4. Open MetaTrader 5 and log in. Then start Claude Code in the project folder and approve the `metatrader5` server when it asks.

5. Edit [`CLAUDE.md`](CLAUDE.md) with your own account details, timezone, trading windows, risk rules and setups.

## Usage

In Claude Code, type:

| Command | What it does |
|---|---|
| `SCAN` | Checks the account against the risk rules, then checks every instrument against the setup rules. Prints one line per instrument with no setup, or a full trade card (entry, stop, target, R:R, position size, rule checklist) when all rules pass. |
| `REVIEW <trade or date>` | Grades past trades on whether they followed the rulebook, not just on profit. |
| `STATS` | Win rate, average R, expectancy and rule-break rate for recent trades. |

"No setup" is a normal result.

## The rulebook

[`CLAUDE.md`](CLAUDE.md) holds everything Claude follows:

- **Hard limits:** read-only, never invent prices, mark anything it can't check as `UNVERIFIED`.
- **Risk rules:** 0.5% risk per trade, at most 3 trades per day, a −2% daily loss limit, at most 2 open positions, no correlated positions, minimum 1.5R.
- **Setups:** currently one, "Trend Pullback": H1 EMA50 bias, an M15 pullback to the EMA20 or an H1 swing level, an engulfing or EMA-reclaim trigger, and ATR, spread and range filters.

To add a setup, write it in the same format. Claude only suggests setups listed there.

## Limitations

- No economic calendar is connected, so news-time rules always show as `UNVERIFIED` unless you give the times.
- Indicators are computed from the candles, not read from the MT5 chart. Small differences from your chart's values are possible.
- Candle and tick times are broker server time, not UTC.

## Disclaimer

This is a personal tool for checking trades against your own rules. It is not financial advice. Trading forex and CFDs on margin carries a high risk of loss. Test on a demo account first. You are responsible for every trade you place.
