"""
test_data_finance.py — Tests unitarios para el módulo de datos financieros
===========================================================================
Verifica: yfinance (tickers reales), DefiLlama (TVL), y formateo LLM.
"""

import sys
import os

from data_finance import (
    get_ticker_summary, get_historical_data, compare_tickers,
    get_protocol_tvl, get_top_protocols, get_chain_tvl,
    format_ticker_for_llm, format_defi_for_llm, _format_usd
)

def test_yfinance_and_defillama():
    # ── yfinance Tests ──
    spy = get_ticker_summary("SPY")
    assert not spy.get("error"), f"SPY error: {spy.get('error')}"
    assert (spy.get("price") or 0) > 0, f"SPY price: {spy.get('price')}"
    assert bool(spy.get("name")), "SPY has name"

    btc = get_ticker_summary("BTC-USD")
    assert (btc.get("price") or 0) > 0, f"BTC price: {btc.get('price')}"

    hist = get_historical_data("AAPL", period="5d")
    assert isinstance(hist, list), "Historical data is list"
    assert len(hist) >= 1, "Historical has data"
    if hist:
        assert "date" in hist[0]
        assert "close" in hist[0]
        assert hist[0]["close"] > 0

    comparison = compare_tickers(["SPY", "QQQ"])
    assert len(comparison) >= 1, "Comparison has data"

    # ── DefiLlama Tests ──
    aave = get_protocol_tvl("aave")
    assert not aave.get("error"), f"Aave error: {aave.get('error')}"
    assert (aave.get("tvl") or 0) > 0, "Aave TVL > 0"

    top = get_top_protocols(limit=5)
    assert isinstance(top, list), "Top protocols is list"
    assert len(top) >= 1, "Top protocols has results"

    eth = get_chain_tvl("Ethereum")
    assert (eth.get("tvl") or 0) > 0, "Ethereum TVL > 0"

def test_formatting():
    assert _format_usd(1_500_000_000) == "$1.50B"
    assert _format_usd(230_000_000) == "$230.0M"
    assert _format_usd(15_000) == "$15.0K"
    assert _format_usd(None) == "N/A"
    assert _format_usd(2_500_000_000_000) == "$2.50T"

    llm_output = format_ticker_for_llm(["SPY", "QQQ"])
    if llm_output:
        assert "MARKET DATA" in llm_output
        assert "SPY" in llm_output

    defi_output = format_defi_for_llm(limit=3)
    if defi_output:
        assert "DEFI TVL DATA" in defi_output

if __name__ == "__main__":
    test_yfinance_and_defillama()
    test_formatting()
    print("✅ test_data_finance passed")
