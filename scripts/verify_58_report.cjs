// CDP 无头校验 58 号报告：canvas=4、无 pageerror、术语浮窗可触发
const CDP = "http://localhost:9222";
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
  const ws2 = sess;
  const url = "file:///" + process.argv[2].replace(/\\/g, "/");
  await ws2.send("Page.navigate", { url });
  await sleep(6000);
  const r = await ws2.send("Runtime.evaluate", {
    returnByValue: true,
    expression: `(() => ({
      canvas: document.querySelectorAll('canvas').length,
      terms: document.querySelectorAll('.term').length,
      tips: !!document.getElementById('termtip'),
      tables: document.querySelectorAll('table').length,
      title: document.title,
      chartsInit: ['c1','c2','c3','c4'].map(id => !!(document.getElementById(id) && document.getElementById(id).querySelector('canvas'))),
      errs: window.__errs || []
    }))()`
  });
  console.log(JSON.stringify(Object.assign({ pageErrors: sess.pageErrors }, r.result.value)));
  sess.close();
  await fetch(`${CDP}/json/close/${target.id}`);
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
