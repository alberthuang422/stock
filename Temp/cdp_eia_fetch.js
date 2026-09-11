(async () => {
  const list = ['WGTSTUS1', 'WGTSTP11', 'WGTSTP13', 'WGTSTP30', 'WGTSTP21', 'WDISTUS1'];
  const out = [];
  for (const s of list) {
    try {
      const r = await fetch('/dnav/pet/hist/LeafHandler.ashx?n=PET&s=' + s + '&f=W', { credentials: 'include' });
      const html = await r.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const tables = Array.from(doc.querySelectorAll('table'));
      let tbl = doc.querySelector('table.DataTable');
      if (!tbl) { tbl = tables.reduce((a, b) => (b.querySelectorAll('tr').length > (a ? a.querySelectorAll('tr').length : 0) ? b : a), null); }
      const rows = tbl ? Array.from(tbl.querySelectorAll('tr')) : [];
      const parts = [];
      let curYear = null;
      for (const tr of rows) {
        const tds = Array.from(tr.querySelectorAll('td'));
        if (tds.length < 2) continue;
        let dt = (tds[0].innerText || '').trim();
        const vv = (tds[1].innerText || '').trim().replace(/,/g, '');
        const y4 = dt.match(/^(\d{4})$/);
        if (y4) { curYear = y4[1]; continue; }
        const ymd = dt.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
        const md = dt.match(/^(\d{1,2})\/(\d{1,2})$/);
        if (ymd) { curYear = ymd[3]; dt = ymd[3] + ('0' + ymd[1]).slice(-2) + ('0' + ymd[2]).slice(-2); }
        else if (md && curYear) { dt = curYear + ('0' + md[1]).slice(-2) + ('0' + md[2]).slice(-2); }
        else continue;
        if (vv && !isNaN(parseFloat(vv))) parts.push(dt + ':' + vv);
      }
      out.push(s + '|' + r.status + '|' + parts.length + '|' + parts.join(';'));
    } catch (e) { out.push(s + '|ERR|0|' + String(e)); }
  }
  return out.join('\n@@\n');
})()
