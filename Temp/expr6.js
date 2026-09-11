(async () => {
  const btns = [...document.querySelectorAll('button.dropdown-toggle, button')];
  const b = btns.find(x => /day,\s/.test(x.innerText || ''));
  if (!b) return 'no date button';
  b.click();
  await new Promise(r => setTimeout(r, 2000));
  const menus = [...document.querySelectorAll('.dropdown-menu, ul.dropdown-menu, .cds--dropdown')];
  const vis = menus.filter(m => m.offsetParent !== null);
  const items = vis.flatMap(m => [...m.querySelectorAll('a, li, button, option')].map(x => (x.innerText || '').trim()).filter(Boolean));
  const opts = [...document.querySelectorAll('option')].map(o => o.value + ':' + o.textContent.trim());
  return JSON.stringify({ btn: b.innerText.trim(), openMenus: vis.length, items: [...new Set(items)].slice(0, 80), opts: opts.slice(0, 40) });
})()
