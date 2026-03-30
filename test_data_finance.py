"""
test_data_finance.py — Tests unitarios para el módulo de datos financieros
===========================================================================
Verifica: yfinance (tickers reales), DefiLlama (TVL), y formateo LLM.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_finance import (
    get_ticker_summary, get_historical_data, compare_tickers,
    get_protocol_tvl, get_top_protocols, get_chain_tvl,
    format_ticker_for_llm, format_defi_for_llm, _format_usd
)

PASSED = 0
FAILED = 0

def assert_true(test_name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        print(f"  ✅ {test_name}")
        PASSED += 1
    else:
        print(f"  ❌ {test_name}: {detail}")
        FAILED += 1


print("\n🧪 TEST SUITE: data_finance.py")
print("=" * 50)

# ═══════════════════════════════════════════════════
# SECTION A: yfinance Tests
# ═══════════════════════════════════════════════════

print("\n📌 Test Group 1: get_ticker_summary() — LIVE yfinance")
spy = get_ticker_summary("SPY")
print(f"  📊 SPY: price={spy.get('price')}, error='{spy.get('error', '')}'")
assert_true("SPY has no error", not spy.get("error"), spy.get("error", ""))
assert_true("SPY has price > 0", (spy.get("price") or 0) > 0, f"price={spy.get('price')}")
assert_true("SPY has name", bool(spy.get("name")))

btc = get_ticker_summary("BTC-USD")
print(f"  📊 BTC-USD: price={btc.get('price')}, error='{btc.get('error', '')}'")
assert_true("BTC-USD has price > 0", (btc.get("price") or 0) > 0, f"price={btc.get('price')}")

# ── TEST 2: Historical Data ──
print("\n📌 Test Group 2: get_historical_data()")
hist = get_historical_data("AAPL", period="5d")
print(f"  📊 AAPL 5d: {len(hist)} data points")
assert_true("Historical returns list", isinstance(hist, list))
assert_true("Historical has data", len(hist) >= 1, f"Got {len(hist)}")
if hist:
    assert_true("Has date field", "date" in hist[0])
    assert_true("Has close field", "close" in hist[0])
    assert_true("Close > 0", hist[0]["close"] > 0)

# ── TEST 3: Compare Tickers ──
print("\n📌 Test Group 3: compare_tickers()")
comparison = compare_tickers(["SPY", "QQQ"])
print(f"  📊 Compared {len(comparison)} tickers")
assert_true("Compare returns results", len(comparison) >= 1)

# ═══════════════════════════════════════════════════
# SECTION B: DefiLlama Tests
# ═══════════════════════════════════════════════════

print("\n📌 Test Group 4: get_protocol_tvl() — LIVE DefiLlama")
aave = get_protocol_tvl("aave")
print(f"  📊 Aave: TVL={aave.get('tvl_formatted')}, error='{aave.get('error', '')}'")
assert_true("Aave has no error", not aave.get("error"), aave.get("error", ""))
assert_true("Aave TVL > 0", (aave.get("tvl") or 0) > 0)
assert_true("Aave has name", bool(aave.get("name")))

# ── TEST 5: Top Protocols ──
print("\n📌 Test Group 5: get_top_protocols()")
top = get_top_protocols(limit=5)
print(f"  📊 Top protocols: {len(top)} returned")
assert_true("Top returns list", isinstance(top, list))
assert_true("Top has results", len(top) >= 3, f"Got {len(top)}")
if top:
    assert_true("Has name", bool(top[0].get("name")))
    assert_true("Has tvl", top[0].get("tvl", 0) > 0)

# ── TEST 6: Chain TVL ──
print("\n📌 Test Group 6: get_chain_tvl()")
eth = get_chain_tvl("Ethereum")
print(f"  📊 Ethereum TVL: {eth.get('tvl_formatted')}")
assert_true("Ethereum TVL > 0", (eth.get("tvl") or 0) > 0)

# ═══════════════════════════════════════════════════
# SECTION C: Formatting Tests
# ═══════════════════════════════════════════════════

print("\n📌 Test Group 7: _format_usd()")
assert_true("Billion", _format_usd(1_500_000_000) == "$1.50B")
assert_true("Million", _format_usd(230_000_000) == "$230.0M")
assert_true("Thousand", _format_usd(15_000) == "$15.0K")
assert_true("None", _format_usd(None) == "N/A")
assert_true("Trillion", _format_usd(2_500_000_000_000) == "$2.50T")

print("\n📌 Test Group 8: format_ticker_for_llm()")
llm_output = format_ticker_for_llm(["SPY", "QQQ"])
if llm_output:
    assert_true("Contains table header", "MARKET DATA" in llm_output)
    assert_true("Contains SPY", "SPY" in llm_output)
    assert_true("Contains table delimiter", "|" in llm_output)
else:
    print("  ⚠️ SKIPPED (no data available)")

print("\n📌 Test Group 9: format_defi_for_llm()")
defi_output = format_defi_for_llm(limit=3)
if defi_output:
    assert_true("Contains DeFi header", "DEFI TVL DATA" in defi_output)
    assert_true("Contains table", "|" in defi_output)
else:
    print("  ⚠️ SKIPPED (no DefiLlama data)")

# ── RESULTADO FINAL ──
print(f"\n{'=' * 50}")
print(f"🏆 RESULTS: {PASSED} passed, {FAILED} failed")
if FAILED == 0:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
sys.exit(FAILED)
