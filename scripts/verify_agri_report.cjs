// 无头渲染验证 57 号报告：检查 canvas 数 + pageerror + console error
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FILE = "file:///C:/Users/Administrator/Desktop/stock/reports/57_%E5%86%9C%E4%B8%9A%E8%82%A1ENSO%E4%B8%8E%E5%88%A9%E7%8E%87%E6%95%8F%E6%84%9F%E6%80%A7/index.html";

async function cdpSession(wsUrl, onMsg) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open error")); });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (onMsg) setTimeout(() => onMsg(m, ws), 0);
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
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}

(async () => {
  const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
  const target = await resp.json();
  const errors = [];
  const sess = await cdpSession(target.webSocketDebuggerUrl, (m) => {
    const method = m.method || "";
    if (method === "Runtime.exceptionThrown") {
      errors.push("EXC: " + (m.params.exceptionDetails?.exception?.description || "").slice(0, 200));
    }
    if (method === "Runtime.consoleAPICalled" && (m.params.type === "error" || m.params.type === "warning")) {
      errors.push("CONSOLE: " + (m.params.args || []).map(a => a.value || a.description || "").join(" ").slice(0, 200));
    }
  });
  await sess.openP;
  await sess.send("Page.enable");
  await sess.send("Runtime.enable");
  await sess.send("Page.navigate", { url: FILE });
  await sleep(10000);
  const r = await sess.send("Runtime.evaluate", {
    expression: `({
      canvas: document.querySelectorAll('canvas').length,
      tables: document.querySelectorAll('table').length,
      h1: (document.querySelector('h1')||{}).innerText || '',
      bodyW: document.body.scrollWidth, winW: window.innerWidth
    })`,
    returnByValue: true
  });
  console.log("RENDER:", JSON.stringify(r.result.value));
  console.log("ERRORS:", errors.length ? errors.join("\n") : "none");
  if (sess) sess.close();
  if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  const v = r.result.value || {};
  process.exit(v.canvas >= 5 && errors.length === 0 ? 0 : 1);
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });