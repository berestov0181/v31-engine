"""Suite: T1 ddof-pin + T2 stress 500k degenerate. Closes spec S5 tails."""
import math, random, sys
sys.path.insert(0, ".")
from engine_v31 import O1Engine

def t1_ddof():
    rnd = random.Random(7)
    xs = [100.0 + rnd.gauss(0, 1) for _ in range(300)]
    ys = [2.0 * x + rnd.gauss(0, 0.5) for x in xs]
    eng = O1Engine(m_window=300)
    for x, y in zip(xs, ys):
        beta, sigma, ok = eng.update(x, y)
    assert ok, "engine returned invalid on well-formed input"
    n = eng.n
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((a - mx) ** 2 for a in xs)
    sxy = sum((a - mx) * (c - my) for a, c in zip(xs, ys))
    b = sxy / sxx
    res = [c - (my + b * (a - mx)) for a, c in zip(xs, ys)]
    sse = sum(r * r for r in res)
    sig_ref = math.sqrt(sse / (n * (n - 2)))
    rel_sig = abs(eng.sigma - sig_ref) / sig_ref
    z_core = res[-1] / eng.sigma
    z_pd = res[-1] / math.sqrt(sse / (n - 1))
    z_aligned = z_core * math.sqrt((n - 1) / (n * (n - 2)))
    rel_z = abs(z_aligned - z_pd) / abs(z_pd)
    print(f"T1: n={n} sigma={eng.sigma:.6e} ref={sig_ref:.6e} rel_sig={rel_sig:.2e}")
    print(f"T1: z_core={z_core:.4f} aligned={z_aligned:.4f} pandas={z_pd:.4f} rel_z={rel_z:.2e}")
    assert rel_sig < 1e-9, "restored sigma diverges from direct computation"
    assert rel_z < 1e-6, "ddof alignment failed"
    print("T1 PASS")

def t2_stress_500k_degenerate():
    rnd = random.Random(42)
    eng = O1Engine(m_window=300, beta_floor=0.05)
    degen_start = None; degen_seen = False
    for i in range(500_000):
        x = 100.0 + (0.5 if (200_000 <= i < 210_000) else rnd.gauss(0, 1))
        y = 2.0 * x + rnd.gauss(0, 0.5)
        beta, sigma, ok = eng.update(x, y, x_tick=1e-8)
        if not ok and 200_000 <= i < 210_000:
            if degen_start is None: degen_start = i
            degen_seen = True
        if i % 100_000 == 0:
            print(f"  ...{i} done, degen={eng.degen_count}, resyncs={eng.resync_count}")
    print(f"T2: resyncs={eng.resync_count} degen={eng.degen_count} "
          f"degen_seen={degen_seen} start={degen_start}")
    assert eng.degen_count > 0, "guard never fired on degenerate stretch"
    assert degen_seen, "guard did not freeze during flat stretch"
    beta, sigma, ok = eng.update(101.0, 202.0)
    assert ok and beta is not None, "no recovery after variability restored"
    print("T2 PASS: 0 crashes, guard fired, recovery OK")

if __name__ == "__main__":
    t1_ddof()
    t2_stress_500k_degenerate()
    print("ALL TESTS PASS")
