(async () => {
  const r = await fetch('/CmeWS/mvc/Settlements/Futures/Settlements/426/FUT?tradeDate=09/09/2026&pageSize=100&pageNumber=1', { headers: { Accept: 'application/json' } });
  const j = await r.json();
  const rows = (j.settlements || []).slice(0, 10).map(s => [s.month, s.settle, s.last, s.volume, s.openInterest]);
  return JSON.stringify({ hdr: j.dsHeader, date: j.tradeDate, rows });
})()
