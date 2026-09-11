(async () => {
  const urls = [
    '/proxies/timeseries/queryeod.ashx?symbol=HOK22&data=daily&maxrecords=200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration',
    '/proxies/timeseries/queryeod.ashx?symbol=HOM22&data=daily&maxrecords=200&volume=contract&order=asc&backadjust=false&daystoexpiration=1&contractroll=expiration'
  ];
  const out = {};
  for (const u of urls) {
    try {
      const r = await fetch(u, { headers: { Accept: 'text/csv,*/*' } });
      const t = await r.text();
      const lines = t.split('\n').filter(l => /2022-04-2[5-9]|2022-05-0[1-5]|2022-04-2[0-4]/.test(l));
      out[u.split('symbol=')[1].split('&')[0]] = 'HTTP' + r.status + ' len=' + t.length + ' :: ' + t.slice(0, 120) + ' || APR: ' + JSON.stringify(lines);
    } catch (e) { out[u.slice(0, 50)] = 'ERR ' + e.message; }
  }
  return JSON.stringify(out);
})()
