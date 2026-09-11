(async () => {
  const cache = JSON.parse(localStorage.getItem('wb_ho_scan_v1') || '{}');
  const MONTHS = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z'];
  const syms = [];
  for (let y = 2000; y <= 2026; y++) for (const m of MONTHS) syms.push('HO' + m + String(y).slice(2));
  const seq = syms.filter(s => cache[s]);
  const px = {};
  for (const s of seq) {
    const o = {};
    for (const rec of cache[s].split('|')) { const p = rec.split(':'); o[p[0]] = { c: +p[1], v: +p[2] }; }
    px[s] = o;
  }
  const near = {}, far = {};
  for (const s of seq) for (const d of Object.keys(px[s])) {
    if (!near[d]) near[d] = s; else if (!far[d] && s !== near[d]) far[d] = s;
  }
  const out = ['date,near_contract,far_contract,spread_usd_per_gal,spread_usd_per_bbl,front_volume'];
  const ds = Object.keys(near).sort();
  for (const d of ds) {
    const n = near[d], f = far[d];
    if (!f) continue;
    const a = px[n][d], b = px[f][d];
    if (!a || !b || a.v < 1000) continue;
    const sp = a.c - b.c;
    out.push([d, n, f, sp.toFixed(4), (sp * 42).toFixed(2), a.v].join(','));
  }
  return out.join('\n');
})()
