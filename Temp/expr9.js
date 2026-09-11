(async () => {
  const MONTHS = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'];
  const y0 = 2005, y1 = 2026;
  const syms = [];
  for (let y = y0; y <= y1; y++) for (const m of MONTHS) syms.push('HO' + m + String(y).slice(2));
  const data = {};
  let idx = 0, fails = [], okc = 0;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const grab = async (s) => {
    for (let k = 0; k < 4; k++) {
      try {
        const r = await fetch('/proxies/timeseries/queryeod.ashx?symbol=' + s + '&data=daily&maxrecords=1200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration', { headers: { Accept: 'text/csv,*/*' } });
        if (r.status === 200) {
          const t = await r.text();
          if (t.indexOf(',') > 0) {
            const o = {};
            for (const line of t.split('\n')) {
              const p = line.split(',');
              if (p.length < 7) continue;
              const d = p[1], c = parseFloat(p[5]);
              if (d && d.length === 10 && !isNaN(c)) o[d] = { c, v: parseFloat(p[6]) || 0 };
            }
            if (Object.keys(o).length) { data[s] = o; return true; }
            return false;
          }
        }
      } catch (e) { }
      await sleep(500 * (k + 1));
    }
    return false;
  };
  const worker = async () => {
    while (idx < syms.length) {
      const s = syms[idx++];
      const ok = await grab(s);
      if (ok) okc++; else fails.push(s);
    }
  };
  await Promise.all([worker(), worker(), worker()]);

  const seq = syms.filter(s => data[s]);
  const near = {}, far = {};
  for (const s of seq) for (const d of Object.keys(data[s])) {
    if (!near[d]) near[d] = s; else if (!far[d] && s !== near[d]) far[d] = s;
  }
  const rows = [];
  for (const d of Object.keys(near)) {
    const n = near[d], f = far[d];
    if (!f) continue;
    const a = data[n][d], b = data[f][d];
    if (!a || !b || a.v < 1000) continue;
    rows.push({ d, n, f, sp: +(a.c - b.c).toFixed(4), v: a.v });
  }
  rows.sort((x, y) => y.sp - x.sp);
  const ds = rows.map(r => r.d).sort();
  return JSON.stringify({ ok: okc, fail: fails.length, failSyms: fails.slice(0, 20), rowsSpan: ds.length ? ds[0] + '~' + ds[ds.length - 1] : '-', top: rows.slice(0, 10) });
})()
