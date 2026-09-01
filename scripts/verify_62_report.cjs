// CDP 无头校验 62 号报告：9 张 ECharts canvas、无 pageerror、关键文本存在
const CDP = "http://127.0.0.1:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open error")); });
  const pageErrors = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.method === "Runtime.exceptionThrown") {
      const d = m.params.exceptionDetails || {};
      pageErrors.push((d.text || "") + " @line " + (d.lineNumber || "?") + " " + ((d.exception && d.exception.description) || "").slice(0, 300));
    }
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++idc;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { openP, send, pageErrors, close: () => { try { ws.close(); } catch {} } };
}

(async () => {
  const target = await (await fetch(`${CDP}/json/new`, { method: "PUT" })).json();
  const sess = await cdpSession(target.webSocketDebuggerUrl);
  await sess.openP;
  await sess.send("Page.enable");
  await sess.send("Runtime.enable");
  const url = "file:///" + process.argv[2].replace(/\\/g, "/");
  await sess.send("Page.navigate", { url });
  await sleep(7000);
  const r = await sess.send("Runtime.evaluate", {
    returnByValue: true,
    expression: `(() => {
      const ids = ['ch_px','ch_long','ch_year','ch_fund','ch_val','ch_bt1','ch_bt2','ch_bt3','ch_bt4'];
      return {
        canvas: document.querySelectorAll('canvas').length,
        perChart: ids.map(id => {
          const el = document.getElementById(id);
          return id + ':' + (el ? (el.querySelector('canvas') ? 'OK' : 'NO_CANVAS') : 'MISSING');
        }),
        terms: document.querySelectorAll('.term').length,
        tables: document.querySelectorAll('table').length,
        kpis: document.querySelectorAll('.kpi').length,
        title: document.title,
        h1: (document.querySelector('h1')||{}).textContent || ''
      };
    })()`
  });
  const v = r.result.value;
  console.log('title:', v.title);
  console.log('h1:', v.h1);
  console.log('canvas count:', v.canvas);
  console.log('charts:', v.perChart.join(' | '));
  console.log('terms:', v.terms, 'tables:', v.tables, 'kpis:', v.kpis);
  console.log('pageErrors:', sess.pageErrors.length);
  sess.pageErrors.forEach(e => console.log('  ERR:', e));
  await sess.send("Page.close");
  sess.close();
  const ok = v.canvas >= 9 && sess.pageErrors.length === 0 && v.perChart.every(x => x.includes('OK'));
  console.log(ok ? 'VERIFY_OK' : 'VERIFY_FAIL');
  process.exit(ok ? 0 : 1);
})();
