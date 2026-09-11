(async () => {
  const MONTHS = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'];
  const syms = [];
  for (let y = 2021; y <= 2023; y++) for (const m of MONTHS) syms.push('HO' + m + String(y).slice(2));
  const data = {};
  let idx = 0;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const grab = async (s) => {
    for (let k = 0; k < 3; k++) {
      try {
        const r = await fetch('/proxies/timeseries/queryeod.ashx?symbol=' + s + '&data=daily&maxrecords=1200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration', { headers: { Accept: 'text/csv,*/*' } });
        if (r.status === 200) {
          const t = await r.text();
          const o = {};
          for (const line of t.split('\n')) {
            const p = line.split(',');
            if (p.length < 7) continue;
            const d = p[1], c = parseFloat(p[5]);
            if (d && d.length === 10 && !isNaN(c)) o[d] = { c, v: parseFloat(p[6]) || 0 };
          }
          if (Object.keys(o).length) { data[s] = o; return Object.keys(o).length; }
        }
      } catch (e) { }
      await sleep(400 * (k + 1));
    }
    return 0;
  };
  const worker = async () => { while (idx < syms.length) { await grab(syms[idx++]); } };
  await Promise.all([worker(), worker(), worker()]);

  const seq = syms.filter(s => data[s]);
  const near = {}, far = {};
  for (const s of seq) for (const d of Object.keys(data[s])) {
    if (!near[d]) near[d] = s; else if (!far[d] && s !== near[d]) far[d] = s;
  }
  const out = [];
  const dts = Object.keys(near).filter(d => d >= '2022-04-18' && d <= '2022-05-06').sort();
  for (const d of dts) {
    const n = near[d], f = far[d];
    out.push({ d, n, f, nv: data[n] ? data[n][d].v : null, sp: (data[n] && data[f]) ? +(data[n][d].c - data[f][d].c).toFixed(4) : null });
  }
  return JSON.stringify({ loaded: seq.length, missed: syms.filter(s => !data[s]), rows: out });
})()
