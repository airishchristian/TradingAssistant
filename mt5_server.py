"""Read-only MCP server for a local MetaTrader 5 terminal.

Exposes account info, symbols, prices, candles, positions and history.
It deliberately has no tools that place, modify or close orders.
"""

import os
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
from mcp.server.fastmcp import FastMCP

TERMINAL_PATH = os.environ.get(
    "MT5_TERMINAL_PATH",
    r"C:\Program Files\MetaTrader 5 IC Markets Global\terminal64.exe",
)

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1,
}

mcp = FastMCP("metatrader5")


def _connect():
    # Attaches to the terminal (starting it if needed) using the account
    # already logged in there; no credentials are passed from here.
    if mt5.terminal_info() is None and not mt5.initialize(path=TERMINAL_PATH):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")


def _records(rows):
    return [] if rows is None else [r._asdict() for r in rows]


@mcp.tool()
def account_info() -> dict:
    """Balance, equity, margin, leverage, currency and server of the logged-in account."""
    _connect()
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"No account info: {mt5.last_error()}")
    return info._asdict()


@mcp.tool()
def terminal_info() -> dict:
    """Terminal status: connected, trade allowed, build, data path."""
    _connect()
    return mt5.terminal_info()._asdict()


@mcp.tool()
def symbols(group: str = "*") -> list[str]:
    """List symbol names, optionally filtered by an MT5 group pattern like '*USD*'."""
    _connect()
    return [s.name for s in (mt5.symbols_get(group=group) or [])]


@mcp.tool()
def symbol_info(symbol: str) -> dict:
    """Contract details for a symbol (digits, spread, contract size, swaps...)."""
    _connect()
    mt5.symbol_select(symbol, True)
    info = mt5.symbol_info(symbol)
    if info is None:
        raise ValueError(f"Unknown symbol {symbol}: {mt5.last_error()}")
    return info._asdict()


@mcp.tool()
def tick(symbol: str) -> dict:
    """Latest bid/ask/last tick for a symbol."""
    _connect()
    mt5.symbol_select(symbol, True)
    t = mt5.symbol_info_tick(symbol)
    if t is None:
        raise ValueError(f"No tick for {symbol}: {mt5.last_error()}")
    return t._asdict()


@mcp.tool()
def candles(symbol: str, timeframe: str = "H1", count: int = 100) -> list[dict]:
    """Most recent OHLCV bars. timeframe: M1 M5 M15 M30 H1 H4 D1 W1 MN1.

    `time` is the bar open in broker server time (not UTC).
    """
    _connect()
    mt5.symbol_select(symbol, True)
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAMES[timeframe.upper()], 0, min(count, 5000))
    if rates is None:
        raise ValueError(f"No rates for {symbol}: {mt5.last_error()}")
    return [
        # MT5 stamps bars in server time; strip the tz so it isn't mistaken for UTC.
        {"time": datetime.fromtimestamp(int(r["time"]), timezone.utc).replace(tzinfo=None).isoformat(),
         "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]),
         "close": float(r["close"]), "tick_volume": int(r["tick_volume"]),
         "spread": int(r["spread"])}
        for r in rates
    ]


@mcp.tool()
def positions(symbol: str | None = None) -> list[dict]:
    """Open positions, optionally for one symbol."""
    _connect()
    return _records(mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get())


@mcp.tool()
def orders(symbol: str | None = None) -> list[dict]:
    """Pending orders, optionally for one symbol."""
    _connect()
    return _records(mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get())


@mcp.tool()
def deal_history(days: int = 30) -> list[dict]:
    """Closed deals over the last N days."""
    _connect()
    now = datetime.now()
    return _records(mt5.history_deals_get(now - timedelta(days=days), now))


if __name__ == "__main__":
    mcp.run()
