# v3.1 — O(1) Rolling OLS Pair Engine with Degenerate-Input Guard

A numerically verified O(1)-per-update rolling OLS engine for pair/spread trading,
built through a falsification protocol: every hypothesis was staked numerically
BEFORE measurement, and every failed stake is documented.

## Verified results
| Test | What it proves | Result |
|---|---|---|
| T1 ddof-pin | restored sigma matches direct computation; z aligned to pandas ddof=1 | rel err 2.4e-12 |
| T2 stress: 500k updates + degenerate x | guard holds, zero crashes, counters predicted exactly | resyncs=100 (predicted 100), degen=9701 (predicted 9701) |
| T3/T3b market run BTC/ETH 1h | honest negative: major-pair spread carries no edge after fees | PF 0.60 / 0.45, documented |

## Error model (core insight)
db ~ eps·ū²·√k; the sigma channel amplifies ×64 via sse = syy_c − b²·sxx_c.
Any floating-error corridor MUST include √k accumulation and 1/σ_step² scaling.
Single-step eps models undershoot by ~1000×.

## Files
- `engine_v31.py` — the core. Guards: degenerate-x by window dispersion vs tick size; beta collapse.
- `test_v31.py` — verification suite T1/T2
- `v31_spec.md` — full specification + falsification protocol H1–H6
- `t3_market.py` — market verification harness (BTC/ETH, Bybit 1h)
- `AGENT_BRIEF.md` — standing instructions for AI agents working on this code

## Method
Stake → measure → admit → registry. Negative results are results.

## Author
Andrey Berestof
