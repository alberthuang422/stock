(() => {
  const ins = [];
  document.querySelectorAll('input, select, button').forEach(el => {
    const a = {};
    for (const at of (el.attributes || [])) a[at.name] = at.value;
    ins.push({ tag: el.tagName, ...a, text: (el.innerText || '').slice(0, 30) });
  });
  return JSON.stringify({ inputs: ins.slice(0, 40) });
})()
