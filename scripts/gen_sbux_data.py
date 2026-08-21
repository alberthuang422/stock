# 生成 SBUX 报告图表用数据 JS（复权口径 adj_close，前复权含股息调整——与用户看盘软件一致）
import pandas as pd, json

df = pd.read_csv("/Users/alberthuang/Desktop/股票分析/data/sbux/SBUX, 1D.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
df["adj"] = df.adj_close.fillna(df.close)

# 1) 全历史月线（2014-01 ~ 2026-08，复权）
df["ym"] = df.date.dt.to_period("M")
mon = df.groupby("ym").agg(c=("adj", "last")).reset_index()
mon["date"] = mon.ym.astype(str)
monthly = [{"d": r.date, "c": round(float(r.c), 2)} for _, r in mon.iterrows()]

# 2) 2016-01 ~ 2017-12 日线（突破窗口，复权）
win = df[(df.date >= "2016-01-01") & (df.date <= "2017-12-31")]
daily = [{"d": r.date.strftime("%Y-%m-%d"), "c": round(float(r.adj), 2)} for _, r in win.iterrows()]

# 3) 2020-06 ~ 2026-08 周线（近期大图，复权）
df["wk"] = df.date.dt.to_period("W")
wk = df[df.date >= "2020-06-01"].groupby("wk").agg(c=("adj", "last")).reset_index()
wk["date"] = wk.wk.astype(str)
recent = [{"d": r.date, "c": round(float(r.c), 2)} for _, r in wk.iterrows()]

out = {"monthly": monthly, "breakout_daily": daily, "recent": recent}
js = "window.SBUX_DATA = " + json.dumps(out, separators=(",", ":")) + ";\n"
with open("/Users/alberthuang/Desktop/股票分析/reports/07_sbux星巴克/sbux_data.js", "w") as f:
    f.write(js)
print("monthly:", len(monthly), "daily:", len(daily), "recent:", len(recent))
print("monthly last:", monthly[-1], "| 2021-07:", [p for p in monthly if p["d"] == "2021-07"])

