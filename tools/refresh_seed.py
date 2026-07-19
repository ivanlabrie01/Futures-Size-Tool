#!/usr/bin/env python3
"""Refresh data.js with current market data.

Pulls ~6 months of daily candles from Yahoo Finance for each instrument,
computes last close, ATR(14) and annualized realized volatility, and overrides
the crypto prices with the live Hyperliquid mark. Writes the result to data.js.

No third-party dependencies (stdlib only). Run:  python tools/refresh_seed.py
The GitHub Action in .github/workflows/refresh.yml runs this on a schedule.
"""
import json
import math
import os
import urllib.request
from datetime import date, timezone, datetime

# instrument key (must match INSTRUMENTS keys in index.html) -> Yahoo symbol
YAHOO = {
    "XAUUSD": "GC=F",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SPX": "^GSPC",
    "NAS": "^NDX",
    "EURUSD": "EURUSD=X",
}
# crypto keys whose price we override with the Hyperliquid mark
HL_COIN = {"BTC": "BTC", "ETH": "ETH"}

UA = {"User-Agent": "Mozilla/5.0 (Futures-Size-Tool seed refresh)"}


def yahoo_daily(symbol, rng="6mo"):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval=1d")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.load(r)
    res = d["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = [(h, l, c) for h, l, c in zip(q["high"], q["low"], q["close"])
            if None not in (h, l, c)]
    highs = [x[0] for x in rows]
    lows = [x[1] for x in rows]
    closes = [x[2] for x in rows]
    if len(closes) < 20:
        raise ValueError(f"{symbol}: only {len(closes)} candles")

    # ATR(14): mean of the true range over the last 14 bars
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    atr14 = sum(trs[-14:]) / min(14, len(trs))

    # annualized realized vol from daily log returns
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    n = len(rets)
    mean = sum(rets) / n
    var = sum((x - mean) ** 2 for x in rets) / (n - 1)
    ann = math.sqrt(var) * math.sqrt(252) * 100.0

    return {"price": closes[-1], "dailyMove": atr14, "annVol": ann}


def hyperliquid_mark(coin):
    req = urllib.request.Request(
        "https://api.hyperliquid.xyz/info",
        data=json.dumps({"type": "metaAndAssetCtxs"}).encode(),
        headers={"Content-Type": "application/json", **UA},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.load(r)
    universe, ctxs = d[0]["universe"], d[1]
    for i, u in enumerate(universe):
        if u["name"] == coin:
            return float(ctxs[i]["markPx"])
    return None


def sig(x):
    """Trim to a sensible number of decimals for readability."""
    ax = abs(x)
    dp = 4 if ax < 10 else (2 if ax < 10000 else 0)
    return round(x, dp)


def main():
    market = {}
    for key, sym in YAHOO.items():
        try:
            m = yahoo_daily(sym)
            if key in HL_COIN:
                try:
                    mk = hyperliquid_mark(HL_COIN[key])
                    if mk:
                        m["price"] = mk
                except Exception as e:
                    print(f"  ! HL mark {key}: {e}")
            market[key] = {k: sig(v) for k, v in m.items()}
            print(f"  {key:7s} price={market[key]['price']} "
                  f"dailyMove={market[key]['dailyMove']} annVol={market[key]['annVol']}")
        except Exception as e:
            print(f"  ! {key} ({sym}): {e} — keeping previous seed")

    if not market:
        raise SystemExit("no data fetched; refusing to overwrite data.js")

    asof = date.today().strftime("%-d %b %Y")
    out = ["// Auto-generated market seed. Regenerate with: python tools/refresh_seed.py",
           "// price = last daily close (crypto = Hyperliquid mark); dailyMove = ATR(14) in price units; annVol = annualized realized vol (%).",
           "window.SIZE_SEED = {",
           f'  asof: "{asof}",',
           '  source: "Yahoo Finance daily candles + Hyperliquid marks",',
           "  market: {"]
    keys = list(market.keys())
    for i, k in enumerate(keys):
        m = market[k]
        comma = "" if i == len(keys) - 1 else ","
        out.append(f'    {k}: {{ price: {m["price"]}, dailyMove: {m["dailyMove"]}, annVol: {m["annVol"]} }}{comma}')
    out += ["  }", "};", ""]

    path = os.path.join(os.path.dirname(__file__), "..", "data.js")
    with open(os.path.abspath(path), "w") as f:
        f.write("\n".join(out))
    print(f"wrote data.js (asof {asof})")


if __name__ == "__main__":
    main()
