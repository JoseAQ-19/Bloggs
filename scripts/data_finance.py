"""
data_finance.py — Golden Stack Module: Financial Data Provider
==============================================================
Integra yfinance (stocks/ETFs/funds) y DefiLlama API (crypto TVL/DeFi)
para inyectar datos financieros reales en los artículos.

APIs: yfinance (GRATIS), DefiLlama (GRATIS, sin API key)
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger("data_finance")

# ── yfinance import ──
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    logger.warning("[data_finance] yfinance not installed. pip install yfinance")

REQUEST_TIMEOUT = 15


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 1: yfinance — Stocks, ETFs, Funds
# ═══════════════════════════════════════════════════════════════════

def get_ticker_summary(symbol: str) -> dict:
    """
    Obtiene un resumen completo de un ticker (acción, ETF, fondo).

    Args:
        symbol: Ticker (ej: "SPY", "AAPL", "BTC-USD", "VWCE.DE").

    Returns:
        dict con keys: symbol, name, price, change_pct, market_cap,
                       pe_ratio, dividend_yield, 52w_high, 52w_low,
                       sector, currency, error.
    """
    if not YF_AVAILABLE:
        return {"symbol": symbol, "error": "yfinance not installed"}

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or info.get("regularMarketPrice") is None:
            # Fallback: intentar con fast_info
            fast = ticker.fast_info
            price = getattr(fast, 'last_price', None)
            if price is None:
                return {"symbol": symbol, "error": f"No data found for {symbol}"}
            
            return {
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": round(price, 2),
                "change_pct": None,
                "market_cap": getattr(fast, 'market_cap', None),
                "pe_ratio": None,
                "dividend_yield": None,
                "52w_high": getattr(fast, 'year_high', None),
                "52w_low": getattr(fast, 'year_low', None),
                "sector": info.get("sector", ""),
                "currency": info.get("currency", "USD"),
                "error": ""
            }

        price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
        prev_close = info.get("regularMarketPreviousClose", price)
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0

        return {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", symbol)),
            "price": round(price, 2),
            "change_pct": change_pct,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector", ""),
            "currency": info.get("currency", "USD"),
            "error": ""
        }

    except Exception as e:
        logger.warning(f"[yfinance] Error fetching {symbol}: {type(e).__name__}: {e}")
        return {"symbol": symbol, "error": str(e)}


def get_historical_data(symbol: str, period: str = "1mo") -> list:
    """
    Obtiene datos históricos de un ticker.

    Args:
        symbol: Ticker (ej: "SPY").
        period: Periodo ("1d", "5d", "1mo", "3mo", "6mo", "1y", "5y").

    Returns:
        Lista de dicts con: date, open, high, low, close, volume.
    """
    if not YF_AVAILABLE:
        return []

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return []

        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        logger.info(f"[yfinance] ✅ {symbol}: {len(records)} data points ({period})")
        return records

    except Exception as e:
        logger.warning(f"[yfinance] Historical error {symbol}: {e}")
        return []


def compare_tickers(symbols: list) -> list:
    """
    Compara múltiples tickers. Ideal para generar tablas comparativas.

    Args:
        symbols: Lista de tickers (ej: ["SPY", "QQQ", "VWO"]).

    Returns:
        Lista de dicts con el resumen de cada ticker.
    """
    results = []
    for symbol in symbols[:10]:  # Máximo 10 tickers
        summary = get_ticker_summary(symbol)
        if not summary.get("error"):
            results.append(summary)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 2: DefiLlama — Crypto TVL & DeFi Metrics
# ═══════════════════════════════════════════════════════════════════

DEFILLAMA_BASE = "https://api.llama.fi"


def get_protocol_tvl(protocol: str) -> dict:
    """
    Obtiene TVL y métricas de un protocolo DeFi.

    Args:
        protocol: Slug del protocolo (ej: "aave", "uniswap", "lido").

    Returns:
        dict con: name, tvl, chain, category, change_1d, change_7d, url.
    """
    try:
        resp = requests.get(f"{DEFILLAMA_BASE}/protocol/{protocol}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        tvl = data.get("currentChainTvls", {})
        total_tvl = sum(v for k, v in tvl.items() if not k.endswith("-borrowed") and not k.endswith("-staking"))

        return {
            "name": data.get("name", protocol),
            "tvl": round(total_tvl, 2),
            "tvl_formatted": _format_usd(total_tvl),
            "category": data.get("category", ""),
            "chains": data.get("chains", [])[:5],
            "change_1d": data.get("change_1d"),
            "change_7d": data.get("change_7d"),
            "url": data.get("url", f"https://defillama.com/protocol/{protocol}"),
            "error": ""
        }

    except requests.RequestException as e:
        logger.warning(f"[DefiLlama] Error fetching {protocol}: {e}")
        return {"name": protocol, "error": str(e)}


def get_top_protocols(limit: int = 10) -> list:
    """
    Obtiene los top protocolos DeFi por TVL.

    Returns:
        Lista de dicts con: name, tvl, category, chain, change_1d.
    """
    try:
        resp = requests.get(f"{DEFILLAMA_BASE}/protocols", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        protocols = []
        for p in data[:limit]:
            protocols.append({
                "name": p.get("name", ""),
                "tvl": round(p.get("tvl", 0), 2),
                "tvl_formatted": _format_usd(p.get("tvl", 0)),
                "category": p.get("category", ""),
                "chain": p.get("chain", ""),
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
            })

        logger.info(f"[DefiLlama] ✅ Top {len(protocols)} protocols fetched")
        return protocols

    except requests.RequestException as e:
        logger.warning(f"[DefiLlama] Error: {e}")
        return []


def get_chain_tvl(chain: str = "Ethereum") -> dict:
    """
    Obtiene el TVL total de una blockchain.

    Args:
        chain: Nombre de la cadena (ej: "Ethereum", "Solana", "Arbitrum").

    Returns:
        dict con: name, tvl, tvl_formatted.
    """
    try:
        resp = requests.get(f"{DEFILLAMA_BASE}/v2/chains", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for c in data:
            if c.get("name", "").lower() == chain.lower():
                tvl = c.get("tvl", 0)
                return {
                    "name": c["name"],
                    "tvl": round(tvl, 2),
                    "tvl_formatted": _format_usd(tvl),
                    "error": ""
                }

        return {"name": chain, "tvl": 0, "error": f"Chain '{chain}' not found"}

    except requests.RequestException as e:
        return {"name": chain, "tvl": 0, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# SECCIÓN 3: Formateo para LLM
# ═══════════════════════════════════════════════════════════════════

def format_ticker_for_llm(symbols: list) -> str:
    """Formatea datos de tickers para inyectar en contexto LLM."""
    results = compare_tickers(symbols)
    if not results:
        return ""

    lines = ["[MARKET DATA — REAL-TIME FINANCIAL INTELLIGENCE]"]
    lines.append("| Symbol | Name | Price | Change % | Market Cap | P/E | Div Yield |")
    lines.append("|--------|------|-------|----------|------------|-----|-----------|")

    for r in results:
        mc = _format_usd(r.get("market_cap")) if r.get("market_cap") else "N/A"
        pe = f"{r['pe_ratio']:.1f}" if r.get("pe_ratio") else "N/A"
        dy = f"{r['dividend_yield']*100:.2f}%" if r.get("dividend_yield") else "N/A"
        chg = f"{r['change_pct']:+.2f}%" if r.get("change_pct") is not None else "N/A"
        lines.append(f"| {r['symbol']} | {r['name'][:25]} | ${r['price']} | {chg} | {mc} | {pe} | {dy} |")

    lines.append("[END MARKET DATA — Use real numbers and cite yfinance/Yahoo Finance]")
    return "\n".join(lines)


def format_defi_for_llm(limit: int = 5) -> str:
    """Formatea los top protocolos DeFi para inyectar en contexto LLM."""
    protocols = get_top_protocols(limit)
    if not protocols:
        return ""

    lines = ["[DEFI TVL DATA — DefiLlama Real-Time Metrics]"]
    lines.append("| Protocol | TVL | Category | 24h Change | 7d Change |")
    lines.append("|----------|-----|----------|------------|-----------|")

    for p in protocols:
        d1 = f"{p['change_1d']:+.1f}%" if p.get('change_1d') is not None else "N/A"
        d7 = f"{p['change_7d']:+.1f}%" if p.get('change_7d') is not None else "N/A"
        lines.append(f"| {p['name']} | {p['tvl_formatted']} | {p['category']} | {d1} | {d7} |")

    lines.append("[END DEFI DATA — Cite DefiLlama as source with link: https://defillama.com]")
    return "\n".join(lines)


def _format_usd(value) -> str:
    """Formatea números grandes en formato legible ($1.5B, $230M, etc.)."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "N/A"

    if v >= 1_000_000_000_000:
        return f"${v/1_000_000_000_000:.2f}T"
    elif v >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f}B"
    elif v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"${v/1_000:.1f}K"
    else:
        return f"${v:.2f}"
