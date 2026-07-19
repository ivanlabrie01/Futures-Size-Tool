# Futures Size Tool

A position-sizing and volatility-target calculator for futures and CFD trading — gold, crypto perps, index CFDs and FX. It's a single HTML page with no build step and no server: open it and it runs.

**Live:** https://ivanlabrie01.github.io/Futures-Size-Tool/

## What it does

Leverage is not the risk. **Size × stop** is the risk. The tool sizes a trade two independent ways and takes the smaller of the two:

1. **Risk to the stop** — the position that loses a fixed % of your equity if the stop is hit.
2. **Volatility target** — the position that keeps your daily risk steady across markets (`leverage = vol_target ÷ instrument_vol`). Wilder market, smaller size.

It then floors the result to the broker's minimum lot, tells you which cap is binding, and — the part small accounts need most — flags when the *smallest position the broker allows* is already too big for the account.

Other panels:

- **Reality check** — what the minimum lot actually risks (% of equity and leverage) on your account.
- **What you're holding vs. what's safe** — type in a live position and see its leverage and roughly where the broker auto-closes you.
- **Refresh any ticker** — paste a column of recent daily closes to recompute price, daily move and volatility for anything not in the presets.
- **Export plan** — download the current setup as a text file.

## Instruments

Presets: Gold (XAUUSD), BTC and ETH perps, S&P 500 and Nasdaq CFDs, EURUSD, plus a **Custom** instrument where you set the contract spec yourself. Contract specs vary by broker — check yours and override in the advanced panel.

The generic model: `mult` = dollars of P&L per 1 unit of size per 1 unit of price move, so `notional = mult × price × size` and `risk$ = mult × stop × size`.

## Market data

Prices and volatility are **seeded, not live** — the page fetches nothing at runtime, so it works offline and can be hosted anywhere. `data.js` holds the seed; `tools/refresh_seed.py` regenerates it from Yahoo Finance daily candles (last close, ATR-14, annualized realized vol) and Hyperliquid marks for crypto.

```bash
python tools/refresh_seed.py   # stdlib only, no pip install
```

A GitHub Action (`.github/workflows/refresh.yml`) runs it on weekdays and commits the result, so the hosted page stays current on its own. You can also just paste fresh closes into the tool for any symbol.

## Run it yourself

- **Locally:** open `index.html` in a browser. Done.
- **Host it:** it's static — GitHub Pages, Netlify, an S3 bucket, or any web server.

## Disclaimer

Educational tool for position sizing. Not financial advice, and not a recommendation to trade any instrument. You are responsible for your own risk.

## License

MIT — see [LICENSE](LICENSE).
