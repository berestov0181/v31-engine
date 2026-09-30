#!/usr/bin/env python3
"""T3b: + z-stop 3.5, exit band 0.5."""
import sys, os, glob, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_v31 import O1Engine
import pandas as pd

FEE, Z_ENTRY, WINDOW = 0.0006, 2.0, 300

def load(pair):
    hits = glob.glob(os.path.expanduser(f"~/ftdata/**/{pair}*-1h-futures.feather"), recursive=True)
    if not hits:
        raise FileNotFoundError(pair)
    print("data:", hits[0])
    df = pd.read_feather(hits[0])
    return df.rename(columns={"date": "t", "close": "c"})[["t", "c"]].set_index("t")

b = load("BTC").rename(columns={"c": "cb"})
e = load("ETH").rename(columns={"c": "ce"})
df = b.join(e, how="inner").dropna()
print(f"bars: {len(df)}, from {df.index.min()} to {df.index.max()}")

ly = np.log(df["ce"].values)
lx = np.log(df["cb"].values)
ce = df["ce"].values
cb = df["cb"].values

eng = O1Engine(m_window=WINDOW, beta_floor=0.05)
pos = 0; entry_px = None; trades = []; pnl = 0.0; eq = 0.0; peak = 0.0; dd = 0.0

for i in range(WINDOW, len(df)):
    beta, sigma, ok = eng.update(lx[i], ly[i])
    if not ok or not sigma:
        continue
    n = min(WINDOW, i + 1)
    my = ly[i - n + 1:i + 1].mean()
    mx = lx[i - n + 1:i + 1].mean()
    resid = ly[i] - (my + beta * (lx[i] - mx))
    z = resid / sigma
    if pos == 0:
        if z > Z_ENTRY:
            pos = -1; entry_px = (ce[i], cb[i], beta)
        elif z < -Z_ENTRY:
            pos = 1; entry_px = (ce[i], cb[i], beta)
    else:
        if abs(z) < 0.5 or abs(z) > 3.5 or (pos == 1 and z > 2 * Z_ENTRY) or (pos == -1 and z < -2 * Z_ENTRY):
            pe, pb, beta0 = entry_px
            ret_e = (ce[i] / pe - 1) * (1 if pos == 1 else -1)
            ret_b = (cb[i] / pb - 1) * (1 if pos == -1 else -1)
            t = ret_e + beta0 * ret_b - 2 * FEE
            pnl += t; eq += t; trades.append(t)
            peak = max(peak, eq); dd = max(dd, peak - eq)
            pos = 0; entry_px = None

wins = [t for t in trades if t > 0]; losses = [t for t in trades if t <= 0]
pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else float("inf")
wr = len(wins) / len(trades) * 100 if trades else 0
print(f"trades: {len(trades)}  win%: {wr:.1f}  PF: {pf:.2f}")
print(f"total pnl: {pnl*100:.2f}%  max DD (sum-based): {dd*100:.2f}%")
if trades:
    print(f"avg win: {sum(wins)/len(wins)*100:.2f}%  avg loss: {sum(losses)/len(losses)*100:.2f}%")
    print("last 10 trades %:", [round(t * 100, 2) for t in trades[-10:]])
