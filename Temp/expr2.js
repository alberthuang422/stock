(async () => {
  const out = {};
  for (const d of ["04/28/2022", "2022-04-28"]) {
    try {
      const r = await fetch('/CmeWS/mvc/Settlements/Futures/Settlements/426/FUT?tradeDate=' + encodeURIComponent(d) + '&pageSize=100', { headers: { 'Accept': 'application/json' } });
      const t = await r.text();
      out[d] = r.status + ' | ' + t.slice(0, 900);
    } catch (e) { out[d] = 'ERR ' + e.message; }
    if (out[d] && out[d].indexOf('200') === 0) break;
  }
  return JSON.stringify(out);
})()
