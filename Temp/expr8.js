(async () => {
  const MONTHS = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'];
  const y0 = 2015, y1 = 2026;
  const syms = [];
  for (let y = y0; y <= y1; y++) for (const m of MONTHS) syms.push('HO' + m + String(y).slice(2));
  const data = {};
  let idx = 0, errs = 0;
  const worker = async () => {
    while (idx < syms.length) {
      const s = syms[idx++];
      try {
        const r = await fetch('/proxies/timeseries/queryeod.ashx?symbol=' + s + '&data=daily&maxrecords=1200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration', { headers: { Accept: 'text/csv,*/*' } });
        const t = await r.text();
        if (r.status === 200 && t.indexOf(',') > 0) {
          const o = {};
          for (const line of t.split('\n')) {
            const p = line.split(',');
            if (p.length < 7) continue;
            const d = p[1], c = parseFloat(p[5]);
            if (d && d.length === 10 && !isNaN(c)) o[d] = { c, v: parseFloat(p[6]) || 0 };
          }
          if (Object.keys(o).length) data[s] = o;
        } else errs++;
      } catch (e) { errs++; }
    }
  };
  await Promise.all([worker(), worker(), worker(), worker(), worker(), worker()]);

  const seq = syms.filter(s => data[s]);
  const near = {}, far = {};
  for (const s of seq) {
    for (const d of Object.keys(data[s])) {
      if (!near[d]) near[d] = s;
      else if (!far[d] && s !== near[d]) far[d] = s;
    }
  }
  const rows = [];
  for (const d of Object.keys(near)) {
    const n = near[d], f = far[d];
    if (!f) continue;
    const a = data[n][d], b = data[f][d];
    if (!a || !b || a.v < 1000) continue;
    rows.push({ d, n, f, a: a.c, b: b.c, sp: +(a.c - b.c).toFixed(4), v: a.v });
  }
  rows.sort((x, y) => y.sp - x.sp);
  return JSON.stringify({
    ok: seq.length, errs: errs, rows: rows.length,
    top: rows.slice(0, 12),
    worst: rows.slice(-5),
    from: rows.length ? rows[rows.length - 1].d : null,
    to: rows.length ? rows.reduce((m, r) => r.d > m ? r.d : m, '') : null
  });
})()
