(async () => {
  const dates = ['09/09/2026', '12/31/2025', '06/30/2025', '04/28/2025', '12/31/2024', '04/28/2024', '04/28/2023', '04/28/2022'];
  const out = {};
  for (const d of dates) {
    try {
      const r = await fetch('/CmeWS/mvc/Settlements/Futures/Settlements/426/FUT?tradeDate=' + d + '&pageSize=100&pageNumber=1', { headers: { Accept: 'application/json' } });
      const j = await r.json();
      const s = j.settlements || [];
      out[d] = 'n=' + s.length + ' type=' + j.reportType + ' empty=' + j.empty + (s[0] ? ' | ' + JSON.stringify(s[0]).slice(0, 70) : '');
    } catch (e) { out[d] = 'ERR ' + e.message; }
  }
  return JSON.stringify(out);
})()
