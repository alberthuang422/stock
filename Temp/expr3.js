(async () => {
  const ids = [426, 194, 181, 2819, 2820, 2821, 5776, 566, 2769, 10923, 302, 111, 425, 343, 257];
  const out = {};
  for (const id of ids) {
    try {
      const r = await fetch('/CmeWS/mvc/Settlements/Futures/Settlements/' + id + '/FUT?tradeDate=09/09/2026&pageSize=100&pageNumber=1', { headers: { Accept: 'application/json' } });
      const j = await r.json();
      const s = j.settlements || [];
      out[id] = r.status + ' hdr="' + j.dsHeader + '" n=' + s.length + ' first=' + (s[0] ? JSON.stringify(s[0]).slice(0, 90) : '-');
    } catch (e) { out[id] = 'ERR ' + e.message; }
  }
  return JSON.stringify(out);
})()
