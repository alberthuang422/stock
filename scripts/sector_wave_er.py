# -*- coding: utf-8 -*-
"""
大盘横盘窗口内的板块波段 ER / 流畅度 / 独立性 打分表（阶段B修正版 2026-08-27）
用法: python sector_wave_er.py [T1 T2 [zigzag_th]]   默认窗口 2025-11-03 ~ 2026-02-27, th=0.05

修正规范（交接文档 §4）：
- 4.1 ER阈值：滚动ER平台主用 EP05(ER20>0.5持续天数)，辅助 EP06；波段ER用 截面分位 +
      板块自身同长度窗口历史80分位 双参照（hist80_high_up/dn 列）；0.7 绝对值仅长窗口辅助。
- 4.2 样本数：方向波段 n<3 → low_n=True，该方向ER不参与标签，降级只用滚动ER统计；
      均值与中位数并列。
- 4.3 标签：二维矩阵（方向×流畅度）：强势独立上涨/弱势独立下跌/跟随震荡/高波动跟随/中性混合。
      涨跌阈值默认8%，阶段B用全切片|区间涨跌|75分位校准后冻结。

保留的坑修复：ZigZag pending确认机制；load 用 startswith 过滤；端点归一化。
"""
import pandas as pd, numpy as np, os, sys

base = os.path.join(os.path.dirname(__file__), '..', 'data')
SECTORS = ['XLB','XLC','XLE','XLF','XLI','XLK','XLP','XLRE','XLU','XLV','XLY']

def load(s):
    d = os.path.join(base, s.lower())
    f = [x for x in os.listdir(d) if x.upper().startswith(s.upper()) and '1D' in x][0]
    return pd.read_csv(os.path.join(d, f), parse_dates=['date']).set_index('date')['adj_close']

def build_frame():
    px = {s: load(s) for s in SECTORS}
    px['SPY'] = load('SPY')
    # 以 SPY 日期为主轴，板块缺席保留 NaN（XLRE 2015-10、XLC 2018-06 才有数据）
    S = pd.DataFrame(px).sort_index()
    return S

S = build_frame()

def seg_er(c):
    path = np.abs(np.diff(c)).sum()
    return abs(c[-1]-c[0])/path if path > 0 else np.nan

def zigzag_pivots(c, th):
    """标准ZigZag拐点识别: 极值点需被反向运动≥th确认后才记为拐点(pending机制防震荡粘连)"""
    n = len(c)
    piv = []; trend = 0; ext = 0; pend = -1
    for i in range(1, n):
        if trend == 0:
            if c[i] >= c[ext]*(1+th): piv.append(ext); trend = 1; ext = i
            elif c[i] <= c[ext]*(1-th): piv.append(ext); trend = -1; ext = i
            elif c[i] > c[ext]: ext = i
        elif trend == 1:  # 上趋势, ext=当前高点
            if c[i] > c[ext]: ext = i; pend = -1
            elif pend >= 0:
                if c[i] <= c[pend]*(1-th): piv.append(pend); trend = -1; ext = i; pend = -1
                elif c[i] > c[ext]: ext = i; pend = -1
            elif c[i] <= c[ext]*(1-th): pend = ext
        else:  # 下趋势, ext=当前低点
            if c[i] < c[ext]: ext = i; pend = -1
            elif pend >= 0:
                if c[i] >= c[pend]*(1+th): piv.append(pend); trend = 1; ext = i; pend = -1
                elif c[i] < c[ext]: ext = i; pend = -1
            elif c[i] >= c[ext]*(1+th): pend = ext
    if pend >= 0: piv.append(pend)
    piv.append(ext)
    return sorted(set(piv))

def norm_pivots(pv, n):
    """端点归一化: 首点归0；末点若被截断在内部则延伸至窗口末尾"""
    if not pv: return [0, n-1]
    if pv[0] != 0: pv = [0]+pv
    if len(pv) == 1:
        pv.append(n-1)
    elif pv[-1] < n-1 and pv[-1] > pv[-2]:
        pv[-1] = n-1
    elif pv[-1] < n-1:
        pv.append(n-1)
    return pv

def waves_er(c, th):
    """返回 (上行ER列表, 下行ER列表, 幅度列表, 回撤列表)"""
    pv = norm_pivots(zigzag_pivots(c, th), len(c))
    ups=[]; dns=[]; amps=[]; maes=[]
    for a,b in zip(pv[:-1], pv[1:]):
        if b-a < 1: continue
        e = seg_er(c[a:b+1]); chg = c[b]/c[a]-1
        seg = c[a:b+1]
        if chg > 0:
            pull = (seg/np.maximum.accumulate(seg)-1).min()
            ups.append(e)
        else:
            pull = (seg/np.minimum.accumulate(seg)-1).max()*-1
            dns.append(e)
        maes.append(abs(pull)); amps.append(abs(chg))
    return ups, dns, amps, maes

def rolling_er(series, n=20):
    s = pd.Series(series) if not isinstance(series, pd.Series) else series
    path = s.diff().abs().rolling(n).sum()
    return s.diff(n).abs()/path

def rolling_corr(s1, s2, n=60):
    return s1.pct_change().rolling(n).corr(s2.pct_change())

def episodes(sr, idx, th):
    above = (sr.loc[idx] > th).fillna(False).values
    lens = []; cur = 0
    for v in above:
        if v: cur += 1
        else:
            if cur: lens.append(cur)
            cur = 0
    if cur: lens.append(cur)
    return lens

def first_day_ep_reaches(sr, idx, th, min_len):
    """EP≥min_len 的 episode 首日在窗口内的位置(返回 idx 位置int或None)"""
    above = (sr.loc[idx] > th).fillna(False).values
    cur = 0
    for j, v in enumerate(above):
        cur = cur+1 if v else 0
        if cur == min_len:
            return j  # 0-based 位置
    return None

def hv(series, n=20):
    return series.pct_change().rolling(n).std()*np.sqrt(252)*100

RE = {s: rolling_er(S[s], 20) for s in S.columns}
CR = {s: rolling_corr(S[s], S['SPY'], 60) for s in S.columns}
HV = {s: hv(S[s], 20) for s in S.columns}

# ---------- 板块自身同长度窗口历史 ER 分布（4.1 双参照之一） ----------
_HIST_CACHE = {}
def hist_waves_pool(sector, wlen, th, step=50):
    """全历史所有长度≈wlen 滚动窗口的 (上行ER列表, 下行ER列表) 池，缓存。"""
    key = (sector, round(wlen/10)*10, th)
    hit = _HIST_CACHE.get(key)
    if hit is not None: return hit
    wl = round(wlen/10)*10
    s = S[sector].dropna()
    arr = s.values
    ups=[]; dns=[]
    for start in range(0, len(arr)-wl, step):
        u, dn, _, _ = waves_er(arr[start:start+wl], th)
        ups.extend(u); dns.extend(dn)
    out = (np.array(ups), np.array(dns))
    _HIST_CACHE[key] = out
    return out

def hist_er80(sector, wlen, th, direction):
    ups, dns = hist_waves_pool(sector, wlen, th)
    pool = ups if direction == 'up' else dns
    return float(np.percentile(pool, 80)) if len(pool) >= 20 else np.nan

_ANALYZE_CACHE = {}
def analyze(t1, t2, th=0.05, low_n_min=3):
    """切片打分表：每板块一行指标（不含标签，标签用 label_table 统一打）
    板块在窗口内数据缺失>50% → 整列剔除并记入 missing 返回属性。"""
    ck = (str(t1), str(t2), round(th, 3), low_n_min)
    if ck in _ANALYZE_CACHE: return _ANALYZE_CACHE[ck].copy()
    w = S.loc[t1:t2]
    w = w.dropna(subset=['SPY'])
    frac = w.notna().mean()
    missing = [c for c in w.columns if frac[c] < 0.5 and c != 'SPY']
    w = w.drop(columns=missing)
    dates = w.index
    rets = w.pct_change()
    rows = {}
    for s in w.columns:
        if s == 'SPY': continue
        c = w[s].values
        ups, dns, amps, maes = waves_er(c, th)
        ep5 = episodes(RE[s], dates, 0.5); ep6 = episodes(RE[s], dates, 0.6)
        ep7 = episodes(RE[s], dates, 0.7)
        n_up, n_dn = len(ups), len(dns)
        rows[s] = dict(
            区间涨跌pct=(c[-1]/c[0]-1)*100,
            全局ER=seg_er(c),
            上行ER=np.mean(ups) if ups else np.nan,
            上行ER中位=np.median(ups) if ups else np.nan, n_up=n_up, low_n_up=n_up < low_n_min,
            下行ER=np.mean(dns) if dns else np.nan,
            下行ER中位=np.median(dns) if dns else np.nan, n_dn=n_dn, low_n_dn=n_dn < low_n_min,
            最大波段pct=max(amps)*100 if amps else np.nan,
            波段回撤pct=np.mean(maes)*100 if maes else np.nan,
            EP05=max(ep5) if ep5 else 0, EP06=max(ep6) if ep6 else 0, EP07=max(ep7) if ep7 else 0,
            ER20最大=RE[s].loc[dates].max(),
            HV20=np.nanmean(HV[s].loc[dates]),
            静态corr=rets[s].corr(rets['SPY']) if 'SPY' in w else np.nan,
            corr60均值=CR[s].loc[dates].mean(),
            corr60最低=CR[s].loc[dates].min(),
            hist80高up=(np.mean(ups) >= hist_er80(s, len(w), th, 'up')) if ups else False,
            hist80高dn=(np.mean(dns) >= hist_er80(s, len(w), th, 'dn')) if dns else False,
        )
    df = pd.DataFrame(rows).T
    return df

def label_table(df, ret_th=8.0, ep_strong=8, corr_med_margin=0.0):
    """4.3 二维标签矩阵（切片内截面）。df=analyze()输出。
    返回追加 标签/robust_note 列的副本。"""
    d = df.copy()
    for col in ('low_n_up','low_n_dn','hist80高up','hist80高dn'):
        d[col] = d[col].astype(bool)
    d['up分位'] = d['上行ER'].where(~d['low_n_up']).rank(pct=True)
    d['dn分位'] = d['下行ER'].where(~d['low_n_dn']).rank(pct=True)
    hv_rank = d['HV20'].rank(pct=True)
    corr_med = d['corr60均值'].median()
    def lab(r):
        # 4.3 矩阵流畅度判定 + 4.2 降级路径：
        #  - n≥3：上行ER截面分位 ≥ 前1/3 或 EP05≥8（原条件）
        #  - n<3：该方向ER均值/分位不参与标签，降级只看滚动ER平台，阈值 EP05≥5
        #    （80日级别短切片全板块 n<3，若不留降级通道则标签体系失效——阶段B校准）
        def flow(up):
            er_q = r['up分位'] if up else r['dn分位']
            low_n = r['low_n_up'] if up else r['low_n_dn']
            if low_n: return r['EP05'] >= 5
            return (pd.notna(er_q) and er_q >= 2/3) or r['EP05'] >= ep_strong
        flow_up, flow_dn = flow(True), flow(False)
        low_corr = r['corr60均值'] <= corr_med + corr_med_margin
        if r['区间涨跌pct'] >= ret_th and flow_up and low_corr: return '强势独立上涨'
        if r['区间涨跌pct'] <= -ret_th and flow_dn and low_corr: return '弱势独立下跌'
        if r['corr60均值'] >= 0.7 and hv_rank[r.name] >= 2/3: return '高波动跟随'
        both_weak = ((pd.isna(r['up分位']) or r['up分位'] <= 1/3) and
                     (pd.isna(r['dn分位']) or r['dn分位'] <= 1/3))
        if both_weak and abs(r['区间涨跌pct']) < ret_th: return '跟随震荡'
        return '中性/混合'
    d['标签'] = d.apply(lab, axis=1)
    return d

def robustness(t1, t2, ret_th=8.0):
    """三档th方向一致性：一致→稳健，否则临界"""
    labs = []
    for th in (0.03, 0.05, 0.08):
        labs.append(label_table(analyze(t1, t2, th), ret_th)['标签'])
    L = pd.concat(labs, axis=1, keys=['3','5','8'])
    def agree(r):
        strong = sum('独立' in v for v in r)
        dir_ok = len(set('上涨' if '上涨' in v else ('下跌' if '下跌' in v else '其他') for v in r)) == 1
        return '稳健' if (strong >= 2 and dir_ok) else '临界'
    out = {}
    for s in L.index:
        vals = [v for v in L.loc[s] if v in ('强势独立上涨','弱势独立下跌')]
        out[s] = agree(L.loc[s]) if vals else ''
    return out

if __name__ == '__main__':
    t1 = sys.argv[1] if len(sys.argv) > 1 else '2025-11-03'
    t2 = sys.argv[2] if len(sys.argv) > 2 else '2026-02-27'
    th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    print(f'窗口 {t1} ~ {t2}, 交易日 {len(S.loc[t1:t2])}, 拐点过滤 {th:.0%}')
    df = label_table(analyze(t1, t2, th))
    pd.set_option('display.width', 300)
    print(df[['区间涨跌pct','全局ER','上行ER','n_up','low_n_up','下行ER','n_dn','low_n_dn',
              'EP05','EP06','ER20最大','HV20','静态corr','corr60均值','hist80高up','hist80高dn','标签']]
          .astype({'EP05':int,'EP06':int}).round(2).to_string())
    print('\n--- 敏感性(th=3%/5%/8%) 稳健性 ---')
    rb = robustness(t1, t2)
    for s, v in rb.items():
        if v: print(f'  {s}: {v}')
