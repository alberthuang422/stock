(async () => {
  const r = await fetch('/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WGTSTUS1&f=W', { credentials: 'include' });
  const html = await r.text();
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const tables = Array.from(doc.querySelectorAll('table'));
  const lines = ['htmlLen=' + html.length, 'tables=' + tables.length, 'title=' + doc.title];
  tables.forEach((t, i) => {
    const rows = Array.from(t.querySelectorAll('tr'));
    let s1 = '', s2 = '';
    if (rows[0]) s1 = (rows[0].innerText || '').replace(/\s+/g, ' ').slice(0, 90);
    if (rows[1]) s2 = (rows[1].innerText || '').replace(/\s+/g, ' ').slice(0, 90);
    lines.push('T' + i + ' cls=[' + (t.className || '-') + '] id=[' + (t.id || '-') + '] rows=' + rows.length + ' r0=' + s1 + ' r1=' + s2);
  });
  const sel = doc.querySelector('#DataTables_Table_0') || doc.querySelector('.DataTable') || doc.querySelector('table[class*=Data]');
  lines.push('matchedSelector=' + (sel ? (sel.tagName + '.' + sel.className) : 'NONE'));
  lines.push('--- html slice ---');
  lines.push(html.replace(/\s+/g, ' ').slice(2000, 3400));
  return lines.join('\n');
})()
