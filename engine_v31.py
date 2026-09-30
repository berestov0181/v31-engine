"""v3.1 O(1) rolling OLS with guards. Restored from spec (v31_spec.md S5).
Fix log (protocol rule 3): guard uses window dispersion sxx vs tick scale
(was: never-updated _var_x=0.0 -> everything classified degenerate);
sse via spec identity sse = syy_c - b^2*sxx_c in O(1) (the x64 channel);
guards HOLD last valid (beta, sigma) — no exceptions on market data."""
import math

class O1Engine:
    def __init__(self, m_window: int = 300, beta_floor: float = 0.05):
        self.m = m_window
        self.beta_floor = beta_floor
        self.Sx = self.Sy = self.Sxx = self.Syy = self.Sxy = 0.0
        self.dx = []; self.dy = []
        self.n = 0
        self.beta = None; self.sigma = None; self.sse = None
        self.invalid = False
        self.degen_count = 0
        self.resync_count = 0
        self.resync_period = 5000
        self._since = 0

    def _resync(self):
        self.Sx = sum(self.dx); self.Sy = sum(self.dy)
        self.Sxx = sum(v * v for v in self.dx)
        self.Syy = sum(v * v for v in self.dy)
        self.Sxy = sum(a * b for a, b in zip(self.dx, self.dy))
        self._since = 0
        self.resync_count += 1

    def update(self, x: float, y: float, x_tick: float = 1e-8):
        self.dx.append(x); self.dy.append(y)
        if len(self.dx) > self.m:
            ox = self.dx.pop(0); oy = self.dy.pop(0)
            self.Sx -= ox; self.Sy -= oy
            self.Sxx -= ox * ox; self.Syy -= oy * oy; self.Sxy -= ox * oy
        self.Sx += x; self.Sy += y
        self.Sxx += x * x; self.Syy += y * y; self.Sxy += x * y
        self.n = len(self.dx)
        self._since += 1
        if self._since >= self.resync_period:
            self._resync()

        if self.n < 3:
            return (None, None, False)

        mx = self.Sx / self.n
        my = self.Sy / self.n
        sxx = self.Sxx - self.n * mx * mx
        syy = self.Syy - self.n * my * my
        sxy = self.Sxy - self.n * mx * my

        # GUARD 1: degenerate x — window dispersion below tick-size scale
        if sxx <= self.n * x_tick * x_tick:
            self.degen_count += 1
            self.invalid = True
            return (self.beta, self.sigma, False)   # hold last valid

        b = sxy / sxx

        # GUARD 2: beta collapse (bear patch #1)
        if abs(b) < self.beta_floor:
            self.degen_count += 1
            self.invalid = True
            return (self.beta, self.sigma, False)

        # sse via spec identity: sse = syy_c - b^2 * sxx_c  (O(1), x64 channel)
        sse = syy - b * b * sxx
        if sse < 0.0:
            sse = 0.0   # float noise near perfect fit

        self.beta = b
        self.sse = sse
        self.sigma = math.sqrt(sse / (self.n * (self.n - 2)))
        self.invalid = False
        return (self.beta, self.sigma, True)
