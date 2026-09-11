(async () => {
  const KEY = 'wb_ho_scan_v1';
  const MONTHS = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'];
  const y0 = 2000, y1 = 2026;
  const syms = [];
  for (let y = y0; y <= y1; y++) for (const m of MONTHS) syms.push('HO' + m + String(y).slice(2));
  const cache = JSON.parse(localStorage.getItem(KEY) || '{}');
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  let fetched = 0, failed = [];
  const grab = async (s) => {
    if (cache[s]) return;
    for (let k = 0; k < 5; k++) {
      try {
        const r = await fetch('/proxies/timeseries/queryeod.ashx?symbol=' + s + '&data=daily&maxrecords=1200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration', { headers: { Accept: 'text/csv,*/*' } });
        if (r.status === 200) {
          const t = await r.text();
          const parts = [];
          for (const line of t.split('\n')) {
            const p = line.split(',');
            if (p.length < 7) continue;
            const d = p[1], c = parseFloat(p[5]);
            if (d && d.length === 10 && !isNaN(c)) parts.push(d + ':' + c + ':' + (parseFloat(p[6]) || 0));
          }
          if (parts.length) { cache[s] = parts.join('|'); fetched++; return; }
        }
      } catch (e) { }
      await sleep(600 * (k + 1));
    }
    failed.push(s);
  };
  let idx = 0;
  const worker = async () => { while (idx < syms.length) { await grab(syms[idx++]); } };
  await Promise.all([worker(), worker()]);
  try { localStorage.setItem(KEY, JSON.stringify(cache)); } catch (e) { }

  const seq = syms.filter(s => cache[s]);
  const near = {}, far = {}, px = {};
  for (const s of seq) {
    const o = {};
    for (const rec of cache[s].split('|')) {
      const p = rec.split(':');
      o[p[0]] = { c: +p[1], v: +p[2] };
    }
    px[s] = o;
  }
  for (const s of seq) for (const d of Object.keys(px[s])) {
    if (!near[d]) near[d] = s; else if (!far[d] && s !== near[d]) far[d] = s;
  }
  const rows = [];
  for (const d of Object.keys(near)) {
    const n = near[d], f = far[d];
    if (!f) continue;
    const a = px[n][d], b = px[f][d];
    if (!a || !b || a.v < 1000) continue;
    rows.push({ d, n, f, sp: +(a.c - b.c).toFixed(4), v: a.v });
  }
  rows.sort((x, y) => y.sp - x.sp);
  const ds = rows.map(r => r.d).sort();
  return JSON.stringify({
    cached: seq.length, target: syms.length, fetchedThisRun: fetched, failed: failed,
    span: ds.length ? ds[0] + '~' + ds[ds.length - 1] : '-',
    top: rows.slice(0, 14)
  });
})()
