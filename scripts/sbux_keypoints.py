# SBUX 关键点位与时间线分析 —— 复权口径（adj_close，前复权，含股息/拆股调整）
# 与未复权口径（close/high）双输出，报告统一用复权口径（用户视角）
import pandas as pd
import json, os

df = pd.read_csv("/Users/alberthuang/Desktop/股票分析/data/sbux/SBUX, 1D.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
# 缺失 adj_close 时回退 close
df["adj"] = df.adj_close.fillna(df.close)
print("数据范围:", df.date.min().date(), "~", df.date.max().date(), "| 行数:", len(df))

out = {}

# ---------- 2015 年高点（复权） ----------
d15 = df[(df.date >= "2015-01-01") & (df.date <= "2015-12-31")]
i15hi = d15.adj.idxmax()
print("\n=== 2015 年高点 ===")
print("复权: %s  adj=$%.2f（未复权 close=$%.2f）" % (df.loc[i15hi, "date"].date(), df.loc[i15hi, "adj"], df.loc[i15hi, "close"]))
out["h2015_date"], out["h2015_adj"], out["h2015_close"] = str(df.loc[i15hi, "date"].date()), round(float(df.loc[i15hi, "adj"]), 2), round(float(df.loc[i15hi, "close"]), 2)

# ---------- 2015Q4-2017 低点 ----------
d16 = df[(df.date >= "2015-09-01") & (df.date <= "2017-01-31")]
i16lo = d16.adj.idxmin()
print("\n=== 2016 低点 ===")
print("复权: %s  adj=$%.2f（未复权 low=$%.2f）" % (df.loc[i16lo, "date"].date(), df.loc[i16lo, "adj"], df.loc[i16lo, "low"]))
out["low2016_date"], out["low2016_adj"] = str(df.loc[i16lo, "date"].date()), round(float(df.loc[i16lo, "adj"]), 2)

# ---------- 突破 2015 高点（复权口径） ----------
hi2015 = df.loc[i15hi, "adj"]
after = df[df.date > "2016-01-01"].reset_index(drop=True)
cand = after[after.adj > hi2015]
if len(cand):
    print("\n=== 突破 2015 高点（复权） ===")
    print("2015 复权高点 $%.2f，adj 收盘首次超过: %s  $%.2f（未复权 close=$%.2f）" % (
        hi2015, cand.iloc[0].date.date(), cand.iloc[0].adj, cand.iloc[0].close))
    out["brk2015_date"], out["brk2015_adj"] = str(cand.iloc[0].date.date()), round(float(cand.iloc[0].adj), 2)
    days = (cand.iloc[0].date - df.loc[i16lo, "date"]).days
    print("距 2016 低点 %d 天" % days)
    out["brk2015_days"] = days

# ---------- 2021 年高点（复权=历史最高） ----------
d21 = df[(df.date >= "2020-06-01") & (df.date <= "2022-06-30")]
i21hi = d21.adj.idxmax()
print("\n=== 2021 高点（复权=历史最高） ===")
print("复权: %s  adj=$%.2f（未复权 close=$%.2f / high=$%.2f）" % (
    df.loc[i21hi, "date"].date(), df.loc[i21hi, "adj"], df.loc[i21hi, "close"], df.loc[i21hi, "high"]))
out["h2021_date"], out["h2021_adj"] = str(df.loc[i21hi, "date"].date()), round(float(df.loc[i21hi, "adj"]), 2)
# 全期复权最高点确认
i_all = df.adj.idxmax()
print("全期复权最高: %s adj=$%.2f" % (df.loc[i_all, "date"].date(), df.loc[i_all, "adj"]))

# 2021 年复权口径各月最高
print("2021 复权口径月最高:")
for m in ["2021-01", "2021-02", "2021-03", "2021-04", "2021-05", "2021-06", "2021-07"]:
    dm = df[df.date.astype(str).str.startswith(m)]
    r = dm.loc[dm.adj.idxmax()]
    print("  %s adj=$%.2f (close=$%.2f)" % (m, r.adj, r.close))

# ---------- 2022 低点 / 2024 低点（复权） ----------
for lo, hi, key in [("2022-01-01", "2022-12-31", "lo2022"), ("2024-01-01", "2025-03-31", "lo2024")]:
    dw = df[(df.date >= lo) & (df.date <= hi)]
    i = dw.adj.idxmin()
    print("\n%s~%s 低点(复权): %s  adj=$%.2f（未复权 low=$%.2f）" % (lo, hi, df.loc[i, "date"].date(), df.loc[i, "adj"], df.loc[i, "low"]))
    out[key + "_date"], out[key + "_adj"] = str(df.loc[i, "date"].date()), round(float(df.loc[i, "adj"]), 2)

# ---------- 当前 ----------
last = df.iloc[-1]
out["last_date"], out["last_close"], out["last_adj"] = str(last.date.date()), round(float(last.close), 2), round(float(last.adj), 2)
print("\n=== 当前 ===")
print("%s  未复权 close=$%.2f / 复权 adj=$%.2f" % (last.date.date(), last.close, last.adj))
print("2026 YTD(复权): %.1f%%" % ((last.adj / df[df.date < "2026-01-01"].iloc[-1].adj - 1) * 100))
print("距 2021 复权高点 $%.2f: %+.1f%%" % (out["h2021_adj"], (last.adj / out["h2021_adj"] - 1) * 100))
out["pct_to_h2021_adj"] = round((last.adj / out["h2021_adj"] - 1) * 100, 1)

# ---------- 2026 年内 ----------
d26f = df[df.date >= "2026-01-01"].reset_index(drop=True)
i26lo = d26f.adj.idxmin()
i26hi = d26f.adj.idxmax()
print("\n=== 2026 走势（复权） ===")
print("低点: %s adj=$%.2f | 高点: %s adj=$%.2f（未复权 high=$%.2f）" % (
    d26f.loc[i26lo, "date"].date(), d26f.loc[i26lo, "adj"],
    d26f.loc[i26hi, "date"].date(), d26f.loc[i26hi, "adj"], d26f.loc[i26hi, "high"]))
out["y2026_lo_date"], out["y2026_lo_adj"] = str(d26f.loc[i26lo, "date"].date()), round(float(d26f.loc[i26lo, "adj"]), 2)
out["y2026_hi_date"], out["y2026_hi_adj"] = str(d26f.loc[i26hi, "date"].date()), round(float(d26f.loc[i26hi, "adj"]), 2)

# 52 周
r52 = df[df.date >= last.date - pd.Timedelta(days=370)]
out["r52_lo"] = round(float(r52.adj.min()), 2)
out["r52_hi"] = round(float(r52.adj.max()), 2)
print("52 周复权: $%.2f ~ $%.2f" % (out["r52_lo"], out["r52_hi"]))

# 2021 高点后最大回撤（复权）
d2124 = df[(df.date >= "2021-07-01") & (df.date <= "2024-12-31")]
i = d2124.adj.idxmin()
print("2021 高点后最大回撤低点(复权): %s adj=$%.2f = %.1f%%" % (
    df.loc[i, "date"].date(), df.loc[i, "adj"], (df.loc[i, "adj"] / out["h2021_adj"] - 1) * 100))
out["dd2022_adj"] = round(float(df.loc[i, "adj"]), 2)

os.makedirs("/Users/alberthuang/Desktop/股票分析/results", exist_ok=True)
with open("/Users/alberthuang/Desktop/股票分析/results/sbux_keypoints.json", "w") as f:
    json.dump(out, f, indent=2)
print("\n已保存 results/sbux_keypoints.json (复权口径)")
print(json.dumps(out, indent=1, ensure_ascii=False))
