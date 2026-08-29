#!/usr/bin/env python3
"""3-2-1 crack spread historical analysis from FRED spot prices.

Sources:
  DGASNYH    NY Harbor conventional gasoline spot, $/gal
  DDFUELNYH  NY Harbor ULSD diesel spot, $/gal
  DCOILWTICO WTI crude, $/bbl
3-2-1 = (2*gasoline*42 + 1*diesel*42)/3 - WTI
"""
import urllib.request
import statistics as st


def fetch(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode()
    out = {}
    for line in raw.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) != 2:
            continue
        d, v = parts[0], parts[1]
        if v in ("", "."):
            continue
        try:
            out[d] = float(v)
        except ValueError:
            pass
    return out


def main():
    g = fetch("DGASNYH")
    d = fetch("DDFUELNYH")
    w = fetch("DCOILWTICO")
    dates = sorted(set(g) & set(d) & set(w))
    series = []
    for dt in dates:
        crack = (2 * g[dt] * 42 + d[dt] * 42) / 3 - w[dt]
        series.append((dt, crack))
    series.sort()
    vals = [v for _, v in series]
    n = len(series)
    print(f"obs={n}  span={series[0][0]} -> {series[-1][0]}")
    print(f"current(3-2-1)={vals[-1]:.2f}  date={series[-1][0]}")

    def pct(p):
        s = sorted(vals)
        return s[int(p / 100 * (n - 1))]

    for p in (10, 25, 50, 75, 90, 95, 99):
        print(f"p{p}={pct(p):.2f}", end="  ")
    print(f"\nmean={st.mean(vals):.2f}  stdev={st.stdev(vals):.2f}")

    cur = vals[-1]
    below = sum(1 for v in vals if v <= cur)
    print(f"current percentile={below / n * 100:.1f}%")

    # runs above threshold 50 (extreme episodes)
    thresh = 50.0
    runs = []
    run = None
    for i, (dt, v) in enumerate(series):
        if v > thresh:
            if run is None:
                run = [i, i, v, v, dt, dt]
            else:
                run[1] = i
                if v > run[2]:
                    run[2] = v
                    run[4] = dt
                if v < run[3]:
                    run[3] = v
        else:
            if run is not None:
                runs.append(run)
                run = None
    if run is not None:
        runs.append(run)
    print(f"\nepisodes above ${thresh}: {len(runs)}")
    for r in runs:
        peak_i = max(range(r[0], r[1] + 1), key=lambda k: series[k][1])
        peak_v, peak_dt = series[peak_i][1], series[peak_i][0]
        # forward returns from episode start
        start_i = r[0]
        fwd = {}
        for m in (30, 90, 180, 365):
            j = start_i + m
            if j < n:
                fwd[m] = series[j][1]
        fwd_s = "  ".join(f"t+{m}d={fwd[m]:.1f}" for m in fwd)
        print(
            f"ep {r[4]}..{r[5]}  peak={peak_v:.1f}@{peak_dt}  "
            f"start_val={series[start_i][1]:.1f}  {fwd_s}"
        )

    # distribution of crack when it first crossed 50 -> where 3/6/12m later
    print("\n-- regression after crossing $50 (first day of each episode) --")
    for r in runs:
        start_i = r[0]
        start_v = series[start_i][1]
        out = [f"cross@50 on {series[start_i][0]} val={start_v:.1f}"]
        for m in (30, 90, 180, 365):
            j = start_i + m
            if j < n:
                out.append(f"t+{m}d={series[j][1]:.1f}")
        print("  ".join(out))


if __name__ == "__main__":
    main()
