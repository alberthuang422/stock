# 对比 close(未复权) vs adj_close(复权) 两口径的 2021 高点
import pandas as pd

df = pd.read_csv("/Users/alberthuang/Desktop/股票分析/data/sbux/SBUX, 1D.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

print("=== 2021-07 高点区域（按 adj_close 排序前 5）===")
d = df[(df.date >= "2021-06-01") & (df.date <= "2021-08-15")]
for _, r in d.nlargest(5, "adj_close").iterrows():
    print("{}  close={:.2f}  adj_close={:.2f}  high={:.2f}".format(r.date.date(), r.close, r.adj_close, r.high))

print("\n=== 全期 adj_close(复权) 最高点 ===")
i = df.adj_close.idxmax()
print("{}  adj_close={:.2f}  close={:.2f}".format(df.loc[i, "date"].date(), df.loc[i, "adj_close"], df.loc[i, "close"]))

print("\n=== 全期 close(未复权) 最高点 ===")
j = df.close.idxmax()
print("{}  close={:.2f}  adj_close={:.2f}".format(df.loc[j, "date"].date(), df.loc[j, "close"], df.loc[j, "adj_close"]))

print("\n=== 2021 年内 adj_close 最高 ===")
d21 = df[df.date.dt.year == 2021]
k = d21.adj_close.idxmax()
print("{}  adj_close={:.2f}  close={:.2f}".format(df.loc[k, "date"].date(), df.loc[k, "adj_close"], df.loc[k, "close"]))

print("\n=== 2026 年内 adj_close 最高（用户看到 111.4 附近?）===")
d26 = df[df.date.dt.year == 2026]
for _, r in d26.nlargest(5, "adj_close").iterrows():
    print("{}  adj_close={:.2f}  close={:.2f}  high={:.2f}".format(r.date.date(), r.adj_close, r.close, r.high))

print("\n=== 最新行 ===")
last = df.iloc[-1]
print("{}  close={:.2f}  adj_close={:.2f}".format(last.date.date(), last.close, last.adj_close))

hi_adj = df.adj_close.max()
print("\n按复权口径：2021 高点 adj_close=${:.2f}，最新 adj_close=${:.2f}，距高点 = {:.1f}%".format(
    hi_adj, last.adj_close, (last.adj_close / hi_adj - 1) * 100))
print("按未复权口径：2021 高点 close=${:.2f}，最新 close=${:.2f}，距高点 = {:.1f}%".format(
    df.close.max(), last.close, (last.close / df.close.max() - 1) * 100))

# 校验: 2021-07-23 adj_close 相对 close 的折价 = 累计分红调整
r = df[(df.date >= "2021-07-22") & (df.date <= "2021-07-26")]
for _, row in r.iterrows():
    print("{} close={:.2f} adj_close={:.2f} 折价={:.1f}%".format(row.date.date(), row.close, row.adj_close,
          (1 - row.adj_close / row.close) * 100))
