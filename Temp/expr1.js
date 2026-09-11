(() => {
  const out = {href: location.href, title: document.title};
  const attrs = [];
  document.querySelectorAll('*').forEach(el => {
    for (const a of (el.attributes||[])) {
      if (/product|instrument/i.test(a.name) && a.value) attrs.push(a.name+'='+a.value);
    }
  });
  out.prodAttrs = [...new Set(attrs)].slice(0,25);
  const html = document.documentElement.outerHTML;
  const hits = html.match(/productId["'\s:=]{1,4}\d+/gi);
  out.prodIdHits = hits ? [...new Set(hits)].slice(0,10) : [];
  out.tables = document.querySelectorAll('table').length;
  out.textHead = (document.body.innerText||'').slice(0, 700);
  return JSON.stringify(out);
})()
